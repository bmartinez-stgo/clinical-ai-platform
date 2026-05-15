from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="clinical-chat",
    version=settings.service_version,
)

app.include_router(health_router)
app.include_router(chat_router)
