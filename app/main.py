
import logging
import os
import time

import httpx2
from fastapi import FastAPI, HTTPException, Request

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode

from app.utils import get_welcome_message


# Configure OpenTelemetry tracing
resource = Resource.create(
    {
        "service.name": "aws-cicd-demo",
    }
)

tracer_provider = TracerProvider(resource=resource)

tracer_provider.add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)

trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)


# Configure Python logging with OpenTelemetry correlation
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format=(
        "%(asctime)s %(levelname)s %(name)s "
        "trace_id=%(otelTraceID)s span_id=%(otelSpanID)s "
        "%(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)

LoggingInstrumentor().instrument(
    set_logging_format=False,
    inject_trace_context=True,
)

logger = logging.getLogger("app")


app = FastAPI(
    title="AWS CI/CD Demo",
    description="A Python API demonstrating automated deployment to AWS.",
    version="1.0.0",
)


# Automatically create tracing spans for incoming FastAPI requests
FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests, responses, processing time, and exceptions."""
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "Request failed method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "Request completed method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.get("/health")
async def health_check():
    """Check whether the application is running."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Return the application welcome message."""
    return {"message": get_welcome_message()}


@app.get("/github/file")
async def get_github_file(path: str):
    """Retrieve a file from GitHub through the GitHub MCP server."""

    token = os.getenv("GITHUB_MCP_TOKEN")

    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub MCP token is not configured.",
        )

    owner = os.getenv("GITHUB_REPOSITORY_OWNER", "razamehar")
    repo = os.getenv("GITHUB_REPOSITORY_NAME", "python-service-lab")

    headers = {
        "Authorization": f"Bearer {token}",
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
            span.set_attribute("github.repository", f"{owner}/{repo}")
            span.set_attribute("github.file_path", path)

            async with httpx2.AsyncClient(
                headers=headers,
                timeout=timeout,
            ) as http_client:

                async with streamable_http_client(
                    "https://api.githubcopilot.com/mcp/readonly",
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
                                "owner": owner,
                                "repo": repo,
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

                raise HTTPException(
                    status_code=502,
                    detail=error_messages or "GitHub MCP tool returned an error.",
                )

            file_content = [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]

            return {
                "repository": f"{owner}/{repo}",
                "path": path,
                "content": file_content,
            }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("GitHub MCP request failed")

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve the file through GitHub MCP.",
        ) from exc
