from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import get_settings
from app.core.engine import warmup_pipeline
from app.core.logging import configure_logging
from app.observability.metrics import metrics
from app.observability.middleware import RequestContextMiddleware
from app.routes.extract import router as extract_router
from app.routes.health import router as health_router

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    metrics.set_service_info(
        service_name=settings.app_name,
        service_namespace=settings.app_namespace,
        service_version=settings.service_version,
        environment=settings.environment,
    )
    yield

app = FastAPI(
    title="ocr-engine",
    version=settings.service_version,
    lifespan=lifespan,
)


@app.on_event("startup")
def startup() -> None:
    import logging

    logger = logging.getLogger("app.main")
    logger.info(
        "starting ocr-engine",
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


app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(extract_router)


@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    metrics.update_uptime()
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
