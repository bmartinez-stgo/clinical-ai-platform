from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


async def extract_laboratory_observations(payload: dict) -> dict:
    if settings.ocr_backend == "ocr-engine":
        target_url = settings.ocr_engine_url
        timeout_seconds = settings.ocr_engine_timeout_seconds
    else:
        target_url = settings.ai_engine_url
        timeout_seconds = settings.ai_engine_timeout_seconds

    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(target_url, json=payload)
        response.raise_for_status()
        return response.json()
