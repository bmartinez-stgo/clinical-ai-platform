from fastapi import APIRouter, Response

from app.core import store
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
async def ready(response: Response) -> dict:
    try:
        n = store.count()
        return {
            "status": "ready",
            "service": settings.app_name,
            "cases_in_store": n,
        }
    except Exception as exc:
        response.status_code = 503
        return {"status": "error", "detail": str(exc)}
