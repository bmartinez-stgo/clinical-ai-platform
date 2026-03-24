from fastapi import FastAPI

from app.core.config import get_settings
from app.core.engine import warmup_pipeline
from app.core.logging import configure_logging
from app.routes.extract import router as extract_router
from app.routes.health import router as health_router
from app.routes.infer import router as infer_router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="ai-engine",
    version=settings.service_version,
)


@app.on_event("startup")
def startup() -> None:
    import logging

    logger = logging.getLogger("app.main")
    logger.info(
        "starting ai-engine",
        extra={
            "service": settings.app_name,
            "namespace": settings.app_namespace,
            "version": settings.service_version,
            "environment": settings.environment,
            "log_level": settings.log_level,
            "debug_logging": settings.debug_logging,
        },
    )
    warmup_pipeline()

app.include_router(health_router)
app.include_router(extract_router)
app.include_router(infer_router)
