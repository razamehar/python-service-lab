from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

from app.core.config import get_settings


def configure_telemetry() -> None:
    """Configure application-wide OpenTelemetry tracing."""
    settings = get_settings()

    tracer_provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.service_name,
            }
        )
    )

    tracer_provider.add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )

    trace.set_tracer_provider(tracer_provider)


def get_tracer(name: str):
    """Return a tracer for the specified module."""
    return trace.get_tracer(name)