from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.soap_prompt import ICD10_SYSTEM_PROMPT, SYSTEM_PROMPT, build_icd10_prompt, build_soap_prompt
from app.core.whisper_engine import transcribe

logger = logging.getLogger(__name__)


async def process_soap_job(ctx: dict, audio_bytes: bytes, language: str) -> dict[str, Any]:
    settings = get_settings()

    logger.info("transcribing audio", extra={"language": language, "size_bytes": len(audio_bytes)})
    try:
        transcript, duration = transcribe(
            audio_bytes,
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
            language=language,
        )
    except Exception as exc:
        logger.exception("transcription failed")
        raise ValueError(f"transcription failed: {exc}") from exc

    if not transcript:
        raise ValueError("transcription is empty — audio may be silent or too short")

    logger.info(
        "transcription done",
        extra={"duration_seconds": round(duration, 1), "transcript_chars": len(transcript)},
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_soap_prompt(transcript, language)},
    ]
    body = {
        "model": settings.vllm_reasoning_model,
        "messages": messages,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
    }

    logger.info("generating soap note")
    try:
        async with httpx.AsyncClient(timeout=settings.vllm_timeout_seconds) as client:
            resp = await client.post(
                f"{settings.vllm_reasoning_url}/v1/chat/completions", json=body
            )
            resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.exception("soap generation failed")
        raise ValueError(f"soap generation failed: {exc}") from exc

    # strip markdown fences if model wrapped the JSON
    if "```" in raw:
        for fragment in raw.split("```"):
            fragment = fragment.strip()
            if fragment.startswith("json"):
                fragment = fragment[4:].strip()
            if fragment.startswith("{"):
                raw = fragment
                break

    try:
        start = raw.find("{")
        end = raw.rfind("}")
        soap = json.loads(raw[start : end + 1])
    except Exception as exc:
        logger.error("failed to parse soap json preview=%s", raw[:300])
        raise ValueError(f"model returned invalid JSON: {exc}") from exc

    logger.info("soap note generated")

    assessment = soap.get("assessment", "")
    icd10_suggestions = []
    if assessment and assessment != "No documentado en esta consulta":
        icd10_suggestions = await _suggest_icd10(assessment, settings)

    return {
        "subjective": soap.get("subjective", "No documentado en esta consulta"),
        "objective": soap.get("objective", "No documentado en esta consulta"),
        "assessment": assessment or "No documentado en esta consulta",
        "plan": soap.get("plan", "No documentado en esta consulta"),
        "transcript": transcript,
        "language": language,
        "duration_seconds": round(duration, 1),
        "icd10_suggestions": icd10_suggestions,
    }


async def _suggest_icd10(assessment: str, settings) -> list[dict]:
    body = {
        "model": settings.vllm_reasoning_model,
        "messages": [
            {"role": "system", "content": ICD10_SYSTEM_PROMPT},
            {"role": "user", "content": build_icd10_prompt(assessment)},
        ],
        "max_tokens": 512,
        "temperature": 0.0,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.vllm_timeout_seconds) as client:
            resp = await client.post(
                f"{settings.vllm_reasoning_url}/v1/chat/completions", json=body
            )
            resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

        if "```" in raw:
            for fragment in raw.split("```"):
                fragment = fragment.strip()
                if fragment.startswith("json"):
                    fragment = fragment[4:].strip()
                if fragment.startswith("["):
                    raw = fragment
                    break

        start = raw.find("[")
        end = raw.rfind("]")
        codes = json.loads(raw[start : end + 1])
        return [c for c in codes if isinstance(c, dict) and "code" in c and "description" in c]
    except Exception:
        logger.warning("icd10 suggestion failed, returning empty list")
        return []


def get_worker_settings(redis_url: str):
    class WorkerSettings:
        functions = [process_soap_job]
        redis_settings = RedisSettings.from_dsn(redis_url)
        max_jobs = 1  # serialize: one job at a time per worker pod
        job_timeout = 300
        keep_result = 3600

    return WorkerSettings
