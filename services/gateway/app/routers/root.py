from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def root():
    return {
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
        "environment": settings.app_env,
        "status": "running",
    }


@router.get("/api/v1/status")
async def status():
    return {
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
        "environment": settings.app_env,
        "auth_service": settings.auth_service_url,
        "features": {
            "health_endpoint": True,
            "ready_endpoint": True,
            "metrics_endpoint": True,
            "token_validation_ready": True,
        },
    }
