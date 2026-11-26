
import asyncio
import os

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/readonly"


async def main():
    token = os.getenv("GITHUB_MCP_TOKEN")

    if not token:
        raise RuntimeError("GITHUB_MCP_TOKEN environment variable is not set.")

    headers = {
    "Authorization": f"Bearer {token}",
    "X-MCP-Toolsets": "repos",
    "Accept": "application/json, text/event-stream",
    }

    timeout = httpx2.Timeout(30, read=300)

    async with httpx2.AsyncClient(
        headers=headers,
        timeout=timeout,
    ) as http_client:

        async with streamable_http_client(
            GITHUB_MCP_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:

                try:
                    await session.initialize()
                except Exception as exc:
                    print("\nMCP initialization failed.")
                    print("Error type:", type(exc).__name__)
                    print("Error code:", getattr(exc, "code", None))
                    print("Error message:", getattr(exc, "message", str(exc)))
                    print("Error data:", repr(getattr(exc, "data", None)))
                    raise

                result = await session.list_tools()

                file_result = await session.call_tool(
                    "get_file_contents",
                    arguments={
                        "owner": "razamehar",
                        "repo": "python-service-lab",
                        "path": "app/main.py",
                    },
                )

                print("\nMCP tool invocation successful.")
                print("\napp/main.py content:")

                for item in file_result.content:
                    if hasattr(item, "text"):
                        print(item.text)

                print("\nGitHub MCP connection successful.")
                print("\nAvailable repository tools:")

                for tool in result.tools:
                    print(f"- {tool.name}: {tool.description or 'No description'}")


if __name__ == "__main__":
    asyncio.run(main())
