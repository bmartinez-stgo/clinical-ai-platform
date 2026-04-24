from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.health import router as health_router
from app.routes.cases import router as cases_router

settings = get_settings()

app = FastAPI(
    title="clinical-rag",
    version=settings.service_version,
)

app.include_router(health_router)
app.include_router(cases_router)
