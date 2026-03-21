from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.service_version,
    }


@router.get("/ready")
async def ready() -> dict:
    return {
        "status": "ready",
        "service": settings.app_name,
    }
