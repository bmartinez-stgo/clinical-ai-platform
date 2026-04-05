from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def extract_laboratory_observations(payload: dict) -> dict:
    if settings.ocr_backend == "ocr-engine":
        target_url = settings.ocr_engine_url
        timeout_seconds = settings.ocr_engine_timeout_seconds
    else:
        target_url = settings.ai_engine_url
        timeout_seconds = settings.ai_engine_timeout_seconds

    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        logger.info(
            "calling extraction backend",
            extra={
                "ocr_backend": settings.ocr_backend,
                "target_url": target_url,
                "timeout_seconds": timeout_seconds,
                "document_id": payload.get("document_id"),
                "document_filename": payload.get("filename"),
                "page_numbers": [page.get("page_number") for page in payload.get("pages", [])],
                "include_metadata": payload.get("include_metadata"),
            },
        )
        try:
            response = await client.post(target_url, json=payload)
            logger.info(
                "received extraction backend response",
                extra={
                    "ocr_backend": settings.ocr_backend,
                    "target_url": target_url,
                    "status_code": response.status_code,
                    "document_id": payload.get("document_id"),
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            logger.exception(
                "extraction backend call failed",
                extra={
                "ocr_backend": settings.ocr_backend,
                "target_url": target_url,
                "timeout_seconds": timeout_seconds,
                "document_id": payload.get("document_id"),
                "document_filename": payload.get("filename"),
                "page_numbers": [page.get("page_number") for page in payload.get("pages", [])],
                "include_metadata": payload.get("include_metadata"),
            },
        )
            raise
