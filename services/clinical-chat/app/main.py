from fastapi import FastAPI

from app.core.config import get_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="clinical-chat",
    version=settings.service_version,
)

# Add rate limiting middleware (10 requests per minute per client)
app.add_middleware(RateLimitMiddleware, requests_per_minute=10)

app.include_router(health_router)
app.include_router(chat_router)
