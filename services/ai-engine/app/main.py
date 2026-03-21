from fastapi import FastAPI

from app.core.config import get_settings
from app.core.engine import warmup_pipeline
from app.routes.extract import router as extract_router
from app.routes.health import router as health_router
from app.routes.infer import router as infer_router

settings = get_settings()

app = FastAPI(
    title="ai-engine",
    version=settings.service_version,
)


@app.on_event("startup")
def startup() -> None:
    warmup_pipeline()

app.include_router(health_router)
app.include_router(extract_router)
app.include_router(infer_router)
