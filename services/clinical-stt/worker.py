"""ARQ worker entry point — run as a separate pod."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.jobs import get_worker_settings

settings = get_settings()
WorkerSettings = get_worker_settings(settings.redis_url)
