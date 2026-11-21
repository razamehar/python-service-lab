import logging
import os
import time

from fastapi import FastAPI, Request

from app.utils import get_welcome_message


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("app")

app = FastAPI(
    title="AWS CI/CD Demo",
    description="A Python API demonstrating automated deployment to AWS.",
    version="1.0.0",
)


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
    return {"message": get_welcome_message()}
