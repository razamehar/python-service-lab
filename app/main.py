
import logging
import os
import time

from fastapi import FastAPI, Request

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

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
