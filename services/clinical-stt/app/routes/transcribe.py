from __future__ import annotations

import logging
from typing import Annotated

from arq import ArqRedis
from arq.jobs import Job
from arq.jobs import JobStatus as ArqJobStatus
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from app.core.config import get_settings
from app.core.schema import JobStatus, SOAPNote

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


def _queue(request: Request) -> ArqRedis:
    return request.app.state.arq


@router.post("/soap", status_code=202, response_model=JobStatus)
async def enqueue_soap(
    request: Request,
    file: Annotated[UploadFile, File(description="Audio file — wav, mp3, m4a, ogg, webm")],
    language: Annotated[str, Form()] = "es",
) -> JobStatus:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="audio file is empty")
    if len(audio_bytes) > settings.max_audio_size_bytes:
        limit_mb = settings.max_audio_size_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"audio exceeds {limit_mb}MB limit")

    queue = _queue(request)
    job = await queue.enqueue_job("process_soap_job", audio_bytes, language)

    logger.info(
        "enqueued soap job",
        extra={"job_id": job.job_id, "size_bytes": len(audio_bytes), "language": language},
    )
    return JobStatus(job_id=job.job_id, status="queued")


@router.get("/soap/{job_id}", response_model=JobStatus)
async def get_soap_status(job_id: str, request: Request) -> JobStatus:
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
        return JobStatus(job_id=job_id, status="queued", position=position)

    if arq_status == ArqJobStatus.in_progress:
        return JobStatus(job_id=job_id, status="processing")

    if arq_status == ArqJobStatus.complete:
        info = await job.result_info()
        if info and info.success:
            return JobStatus(job_id=job_id, status="done", result=SOAPNote(**info.result))
        error = str(info.result) if info else "unknown error"
        return JobStatus(job_id=job_id, status="failed", error=error)

    return JobStatus(job_id=job_id, status=str(arq_status))
