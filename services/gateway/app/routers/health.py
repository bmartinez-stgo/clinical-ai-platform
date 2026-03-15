import httpx
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
    }


@router.get("/ready")
async def ready():
    readiness = {
        "ready": True,
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
        "checks": {
            "config_loaded": True,
        },
    }

    if settings.readiness_check_auth:
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(f"{settings.auth_service_url}/health")
                readiness["checks"]["auth_dependency"] = response.status_code == 200
                readiness["ready"] = readiness["ready"] and response.status_code == 200
        except Exception:
            readiness["checks"]["auth_dependency"] = False
            readiness["ready"] = False

    return readiness
