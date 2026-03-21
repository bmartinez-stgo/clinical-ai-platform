from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


async def extract_laboratory_observations(payload: dict) -> dict:
    timeout = httpx.Timeout(settings.ai_engine_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(settings.ai_engine_url, json=payload)
        response.raise_for_status()
        return response.json()
