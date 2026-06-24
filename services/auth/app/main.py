from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger
from app.observability.metrics import metrics
from app.observability.middleware import RequestContextMiddleware
from app.observability.tracing import setup_tracing
from app.routes.auth import router as auth_router
from app.routes.clients import router as clients_router
from app.routes.docs import router as docs_router
from app.routes.health import router as health_router
from app.routes.token import router as token_router

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    metrics.set_service_info(
        service_name=settings.app_name,
        service_namespace=settings.app_namespace,
        service_version=settings.service_version,
        environment=settings.environment,
    )
    setup_tracing(app, settings)
    logger.info(
        "service startup complete",
        extra={
            "request_id": None,
            "http_method": None,
            "http_route": None,
            "http_status_code": None,
            "duration_ms": None,
            "error_type": None,
        },
    )
    yield
    logger.info(
        "service shutdown complete",
        extra={
            "request_id": None,
            "http_method": None,
            "http_route": None,
            "http_status_code": None,
            "duration_ms": None,
            "error_type": None,
        },
    )


app = FastAPI(
    title="auth",
    version=settings.service_version,
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(clients_router)
app.include_router(docs_router)


@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    metrics.update_uptime()
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
