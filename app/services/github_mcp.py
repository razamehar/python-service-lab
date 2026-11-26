import logging

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from opentelemetry.trace import Status, StatusCode

from app.core.config import get_settings
from app.core.telemetry import get_tracer


logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class GitHubMCPError(Exception):
    """Base exception for GitHub MCP integration errors."""

class GitHubMCPNotConfiguredError(GitHubMCPError):
    """Raised when required GitHub MCP configuration is missing."""

class GitHubMCPToolError(GitHubMCPError):
    """Raised when the GitHub MCP tool reports an error."""

    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__("GitHub MCP tool returned an error.")


async def get_file_contents(path: str) -> list[str]:
    """Retrieve file contents from GitHub using the MCP server."""

    settings = get_settings()

    if not settings.github_mcp_token:
        raise GitHubMCPNotConfiguredError(
            "GitHub MCP token is not configured."
    )

    headers = {
        "Authorization": f"Bearer {settings.github_mcp_token}",
        "X-MCP-Toolsets": "repos",
        "Accept": "application/json, text/event-stream",
    }

    timeout = httpx2.Timeout(30, read=300)

    try:
        with tracer.start_as_current_span(
            "mcp.github.get_file_contents"
        ) as span:

            span.set_attribute("mcp.server", "github")
            span.set_attribute("mcp.tool", "get_file_contents")
            span.set_attribute(
                "github.repository",
                f"{settings.github_repository_owner}/"
                f"{settings.github_repository_name}",
            )
            span.set_attribute("github.file_path", path)

            async with httpx2.AsyncClient(
                headers=headers,
                timeout=timeout,
            ) as http_client:

                async with streamable_http_client(
                    settings.github_mcp_url,
                    http_client=http_client,
                ) as (read_stream, write_stream):

                    async with ClientSession(
                        read_stream,
                        write_stream,
                    ) as session:

                        await session.initialize()

                        result = await session.call_tool(
                            "get_file_contents",
                            arguments={
                                "owner": settings.github_repository_owner,
                                "repo": settings.github_repository_name,
                                "path": path,
                            },
                        )

            if result.is_error:
                span.set_status(Status(StatusCode.ERROR))

                error_messages = [
                    item.text
                    for item in result.content
                    if hasattr(item, "text")
                ]

                raise GitHubMCPToolError(
                    error_messages or ["GitHub MCP tool returned an error."]
                )

            return [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]

    except GitHubMCPError:
        raise

    except Exception as exc:
        logger.exception("GitHub MCP request failed")
        raise GitHubMCPError(
            "Unable to retrieve the file through GitHub MCP."
        ) from exc