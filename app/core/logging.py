import logging

from opentelemetry.instrumentation.logging import LoggingInstrumentor

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure application logging with OpenTelemetry trace correlation."""
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format=(
            "%(asctime)s %(levelname)s %(name)s "
            "trace_id=%(otelTraceID)s span_id=%(otelSpanID)s "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    LoggingInstrumentor().instrument(
        set_logging_format=False,
        inject_trace_context=True,
    )