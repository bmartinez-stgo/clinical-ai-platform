from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="document-reader",
    version=settings.service_version,
)

app.include_router(health_router)
app.include_router(documents_router)
