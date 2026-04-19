from __future__ import annotations

import json
import logging

import httpx

from app.core.config import get_settings
from app.core.prompt import SYSTEM_PROMPT, build_user_message
from app.core.schema import DiagnosticRequest, DiagnosticResponse

settings = get_settings()
logger = logging.getLogger(__name__)


def run_diagnostic_inference(payload: DiagnosticRequest) -> DiagnosticResponse:
    user_message = build_user_message(payload)

    body = {
        "model": settings.vllm_reasoning_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
    }

    logger.info("sending diagnostic inference request", extra={"request_id": payload.request_id})

    with httpx.Client(timeout=settings.vllm_timeout_seconds) as client:
        resp = client.post(f"{settings.vllm_reasoning_url}/v1/chat/completions", json=body)
        resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"]
    logger.debug("raw model output", extra={"output_preview": raw[:500]})

    result = _parse_response(raw, payload.request_id)
    return result


def _parse_response(text: str, request_id: str | None) -> DiagnosticResponse:
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in model output")
    obj, _ = json.JSONDecoder().raw_decode(text, start)
    obj["request_id"] = request_id
    return DiagnosticResponse(**obj)
