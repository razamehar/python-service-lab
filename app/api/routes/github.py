import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.github_mcp import (
    GitHubMCPError,
    GitHubMCPNotConfiguredError,
    GitHubMCPToolError,
    get_file_contents,
)
from app.core.config import get_settings


logger = logging.getLogger("app")

router = APIRouter()


@router.get("/github/file")
async def get_github_file(
    path: str = Query(..., min_length=1),
):
    """Retrieve a file from the configured GitHub repository."""

    settings = get_settings()

    try:
        content = await get_file_contents(path)

        return {
            "repository": (
                f"{settings.github_repository_owner}/"
                f"{settings.github_repository_name}"
            ),
            "path": path,
            "content": content,
        }

    except GitHubMCPNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except GitHubMCPToolError as exc:
        raise HTTPException(
            status_code=502,
            detail=exc.messages,
        ) from exc

    except GitHubMCPError as exc:
        logger.exception("GitHub file retrieval failed")
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc