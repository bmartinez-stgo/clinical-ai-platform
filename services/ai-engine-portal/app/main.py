from fastapi import FastAPI

from app.core.config import get_settings
from app.core.tracing import setup_tracing
from app.routes.health import router as health_router
from app.routes.ui import router as ui_router

settings = get_settings()

app = FastAPI(
    title="Clinical AI Engine Portal",
    version="0.1.0",
)

setup_tracing(app, settings)

app.include_router(health_router)
app.include_router(ui_router)
