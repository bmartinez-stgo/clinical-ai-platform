from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.ui import router as ui_router

app = FastAPI(
    title="Clinical AI Engine Portal",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(ui_router)
