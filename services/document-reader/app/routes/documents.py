from __future__ import annotations

import logging

from arq import ArqRedis
from arq.jobs import Job
from arq.jobs import JobStatus as ArqJobStatus
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.jobs import _SECS_PER_JOB
from app.core.lab_service import normalize_lab_document
from app.core.pdf_parser import extract_document_payload, extract_image_payload
from app.core.schema import JobStatus

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}


def build_document_payload(file_bytes: bytes, filename: str, content_type: str) -> dict:
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


def _queue(request: Request) -> ArqRedis:
    return request.app.state.arq


def _validate_upload(file: UploadFile, file_bytes: bytes) -> None:
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only pdf and common image formats are supported",
        )
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded file is empty",
        )
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="uploaded file exceeds the maximum allowed size",
        )


@router.post("/parse")
async def parse_document(request: Request, file: UploadFile = File(...)):
    """Synchronous generic document parse (lightweight — no AI call)."""
    file_bytes = await file.read()
    _validate_upload(file, file_bytes)
    try:
        logger.info(
            "starting generic document parse",
            extra={
                "document_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_bytes),
            },
        )
        return build_document_payload(
            file_bytes=file_bytes,
            filename=file.filename or "document",
            content_type=file.content_type or "application/pdf",
        )
    except Exception as exc:
        logger.exception("generic document parse failed", extra={"document_filename": file.filename})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="failed to parse document",
        ) from exc


@router.post("/labs/parse", status_code=202, response_model=JobStatus)
async def enqueue_lab_parse(
    request: Request,
    file: UploadFile = File(...),
    language: str = Query(default="es", pattern="^(es|en)$"),
) -> JobStatus:
    """Enqueue a lab PDF for async extraction. Poll GET /labs/parse/{job_id} for result."""
    file_bytes = await file.read()
    _validate_upload(file, file_bytes)

    queue = _queue(request)
    job = await queue.enqueue_job(
        "process_lab_parse_job",
        file_bytes,
        file.filename or "document",
        file.content_type or "application/pdf",
        language,
    )

    queued = await queue.queued_jobs()
    position = next((i + 1 for i, j in enumerate(queued) if j.job_id == job.job_id), 1)
    estimated_seconds = position * _SECS_PER_JOB

    logger.info(
        "enqueued lab parse job",
        extra={
            "job_id": job.job_id,
            "file_name": file.filename,
            "size_bytes": len(file_bytes),
            "position": position,
            "language": language,
        },
    )
    return JobStatus(
        job_id=job.job_id,
        status="queued",
        position=position,
        estimated_seconds=estimated_seconds,
    )


@router.get("/labs/parse/{job_id}", response_model=JobStatus)
async def get_lab_parse_status(job_id: str, request: Request) -> JobStatus:
    """Poll extraction job status. Returns result when done."""
    queue = _queue(request)
    job = Job(job_id, queue)

    try:
        arq_status = await job.status()
    except Exception:
        raise HTTPException(status_code=404, detail="job not found")

    if arq_status == ArqJobStatus.not_found:
        raise HTTPException(status_code=404, detail="job not found or expired")

    if arq_status in (ArqJobStatus.queued, ArqJobStatus.deferred):
        queued = await queue.queued_jobs()
        position = next((i + 1 for i, j in enumerate(queued) if j.job_id == job_id), None)
        estimated_seconds = (position * _SECS_PER_JOB) if position else None
        return JobStatus(
            job_id=job_id,
            status="queued",
            position=position,
            estimated_seconds=estimated_seconds,
        )

    if arq_status == ArqJobStatus.in_progress:
        return JobStatus(job_id=job_id, status="processing")

    if arq_status == ArqJobStatus.complete:
        info = await job.result_info()
        if info and info.success:
            return JobStatus(job_id=job_id, status="done", result=info.result)
        error = str(info.result) if info else "unknown error"
        logger.error("lab parse job failed", extra={"job_id": job_id, "error": error})
        return JobStatus(job_id=job_id, status="failed", error="extraction failed")

    return JobStatus(job_id=job_id, status=str(arq_status))
