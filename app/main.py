import logging
import time

from fastapi import FastAPI, Request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import configure_telemetry


settings = get_settings()

# Initialise observability before creating and instrumenting the application.
configure_telemetry()
configure_logging()

logger = logging.getLogger("app")


app = FastAPI(
    title=settings.app_name,
    description="A Python API demonstrating automated deployment to AWS.",
    version=settings.app_version,
)


# Automatically create tracing spans for incoming FastAPI requests.
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


# Register all application API endpoints.
app.include_router(api_router)