from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logging_config import configure_logging
from app.middleware.request_context import request_context_middleware
from app.observability import initialize_service_metrics, update_uptime
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.proxy import router as proxy_router
from app.routers.root import router as root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    initialize_service_metrics()
    update_uptime()
    yield


app = FastAPI(
    title="Clinical AI Platform Gateway",
    version=settings.service_version,
    lifespan=lifespan,
)

app.middleware("http")(request_context_middleware)

app.include_router(health_router)
app.include_router(root_router)

if settings.metrics_enabled:
    app.include_router(metrics_router)

app.include_router(proxy_router)
