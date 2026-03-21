from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.diagnostics import router as diagnostics_router
from app.routes.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="ai-diagnostic",
    version=settings.service_version,
)

app.include_router(health_router)
app.include_router(diagnostics_router)
