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

_SUPPORTED_FORMATS = "wav, mp3, m4a, ogg, webm, flac"

# (offset, magic_bytes) for supported audio formats
_AUDIO_SIGNATURES: list[tuple[int, bytes]] = [
    (0, b"RIFF"),           # WAV
    (0, b"ID3"),            # MP3 with ID3 tag
    (0, b"\xff\xfb"),       # MP3 frame sync
    (0, b"\xff\xf3"),
    (0, b"\xff\xf2"),
    (0, b"\x1a\x45\xdf\xa3"),  # WebM / MKV (EBML)
    (0, b"OggS"),           # OGG
    (0, b"fLaC"),           # FLAC
    (4, b"ftyp"),           # M4A / MP4
]


def _is_audio(data: bytes) -> bool:
    for offset, sig in _AUDIO_SIGNATURES:
        end = offset + len(sig)
        if len(data) >= end and data[offset:end] == sig:
            return True
    return False


def _queue(request: Request) -> ArqRedis:
    return request.app.state.arq


@router.post(
    "/soap",
    status_code=202,
    response_model=JobStatus,
    summary="Enqueue SOAP note generation from audio",
    description=(
        "Accepts a clinical consultation audio recording and enqueues it for transcription "
        "and SOAP note generation.\n\n"
        "**Limits:**\n"
        "- Maximum file size: **100 MB**\n"
        "- Maximum duration: **30 minutes**\n\n"
        f"**Supported formats:** {_SUPPORTED_FORMATS}\n\n"
        "Returns a `job_id` immediately. Poll `GET /soap/{job_id}` for status and result."
    ),
    responses={
        202: {"description": "Job accepted and queued"},
        400: {"description": "Empty audio file"},
        413: {"description": "File exceeds 100 MB size limit"},
        415: {"description": "Unsupported media type or invalid audio file"},
    },
)
async def enqueue_soap(
    request: Request,
    file: Annotated[
        UploadFile,
        File(description=f"Audio recording ({_SUPPORTED_FORMATS}). Max 100 MB, max 30 min."),
    ],
    language: Annotated[str, Form(description="BCP-47 language code (e.g. 'es', 'en') or 'auto'")] = "es",
) -> JobStatus:
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("audio/") and content_type not in (
        "application/octet-stream", "video/webm",  # browsers sometimes send these for audio
    ):
        raise HTTPException(status_code=415, detail="unsupported media type — audio file required")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="audio file is empty")
    if len(audio_bytes) > settings.max_audio_size_bytes:
        limit_mb = settings.max_audio_size_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"audio exceeds {limit_mb} MB limit")
    if not _is_audio(audio_bytes):
        raise HTTPException(status_code=415, detail="file does not appear to be a valid audio file")

    queue = _queue(request)
    job = await queue.enqueue_job("process_soap_job", audio_bytes, language)

    logger.info(
        "enqueued soap job",
        extra={"job_id": job.job_id, "size_bytes": len(audio_bytes), "language": language},
    )
    return JobStatus(job_id=job.job_id, status="queued")


@router.get(
    "/soap/{job_id}",
    response_model=JobStatus,
    summary="Poll SOAP job status",
    description=(
        "Returns the current status of a SOAP generation job.\n\n"
        "**Status values:**\n"
        "- `queued` — waiting in queue (includes `position`)\n"
        "- `processing` — transcription and note generation in progress\n"
        "- `done` — complete, `result` contains the SOAP note\n"
        "- `failed` — error, `error` contains the reason\n\n"
        "Results expire after 1 hour."
    ),
    responses={
        200: {"description": "Job status (check `status` field)"},
        404: {"description": "Job not found or expired"},
    },
)
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
