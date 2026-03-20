import time

from fastapi import APIRouter

from app.core.config import get_settings
from app.observability.metrics import metrics

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health():
    metrics.update_uptime()
    return {
        "status": "ok",
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
    }


@router.get("/ready")
async def ready():
    metrics.update_uptime()
    return {
        "status": "ready",
        "service": settings.app_name,
        "namespace": settings.app_namespace,
        "version": settings.service_version,
        "timestamp": int(time.time()),
    }
