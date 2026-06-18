from __future__ import annotations

import logging

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.lab_service import normalize_lab_document
from app.core.pdf_parser import extract_document_payload, extract_image_payload

logger = logging.getLogger(__name__)

_SECS_PER_JOB = 60  # rough estimate used for queue ETA


def _build_document_payload(file_bytes: bytes, filename: str, content_type: str) -> dict:
    if content_type == "application/pdf":
        return extract_document_payload(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )
    return extract_image_payload(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )


async def process_lab_parse_job(
    ctx: dict,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    language: str,
) -> dict:
    settings = get_settings()
    logger.info(
        "processing lab parse job",
        extra={"file_name": filename, "size_bytes": len(file_bytes), "language": language},
    )
    document_payload = _build_document_payload(file_bytes, filename, content_type)
    return await normalize_lab_document(document_payload, language=language)


def get_worker_settings(redis_url: str):
    settings = get_settings()

    class WorkerSettings:
        functions = [process_lab_parse_job]
        redis_settings = RedisSettings.from_dsn(redis_url)
        max_jobs = 1
        job_timeout = 300
        keep_result = settings.job_ttl_seconds

    return WorkerSettings
