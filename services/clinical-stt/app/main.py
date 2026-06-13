from __future__ import annotations

from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.health import router as health_router
from app.routes.transcribe import router as transcribe_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    yield
    await app.state.arq.close()


app = FastAPI(title="clinical-stt", version=settings.service_version, lifespan=lifespan)

app.include_router(health_router)
app.include_router(transcribe_router)
