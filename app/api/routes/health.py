from fastapi import APIRouter

from app.utils import get_welcome_message


router = APIRouter()


@router.get("/health")
async def health_check():
    """Return the application health status."""
    return {"status": "healthy"}


@router.get("/")
async def root():
    """Return the application welcome message."""
    return {"message": get_welcome_message()}