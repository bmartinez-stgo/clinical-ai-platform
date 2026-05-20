from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.guardrails import is_medical_query, is_valid_response
from app.core.prompt import build_system_prompt
from app.core.schema import ChatRequest, ChatResponse

settings = get_settings()
logger = logging.getLogger(__name__)


_GUARDRAIL_MSG = {
    "injection": {
        "es": "Consulta no permitida. El mensaje contiene patrones no autorizados en este sistema clínico.",
        "en": "Query not allowed. The message contains patterns that are not permitted in this clinical system.",
    },
    "off_topic": {
        "es": "Consulta fuera de contexto. Este asistente está diseñado exclusivamente para seguimiento clínico del paciente. Por favor formula una pregunta relacionada con el diagnóstico, los resultados de laboratorio o el tratamiento.",
        "en": "Off-topic query. This assistant is designed exclusively for clinical patient follow-up. Please ask a question related to the diagnosis, lab results, or treatment.",
    },
    "no_medical": {
        "es": "Tu consulta no parece estar relacionada con un tema clínico o médico. Por favor formula una pregunta sobre el paciente, sus resultados o su diagnóstico.",
        "en": "Your query does not appear to be related to a clinical or medical topic. Please ask a question about the patient, their results, or their diagnosis.",
    },
}


def _guardrail_detail(reason: str | None, language: str) -> str:
    lang = "en" if language == "en" else "es"
    if reason and "injection" in reason.lower():
        return _GUARDRAIL_MSG["injection"][lang]
    if reason and ("appears to be about" in reason or "no está relacionad" in reason):
        return _GUARDRAIL_MSG["off_topic"][lang]
    return _GUARDRAIL_MSG["no_medical"][lang]


async def run_chat(req: ChatRequest) -> ChatResponse:
    # Extract language from request
    language = req.language if hasattr(req, 'language') else 'es'

    # SECURITY: Validate latest user message for medical relevance
    if req.messages:
        latest_user_msg = next(
            (m.content for m in reversed(req.messages) if m.role == "user"),
            None
        )
        if latest_user_msg:
            is_medical, rejection_reason = is_medical_query(latest_user_msg, language)
            if not is_medical:
                logger.warning(
                    "query_rejected_guardrail",
                    extra={
                        "reason": rejection_reason,
                        "query": latest_user_msg[:100],
                        "user_id": getattr(req, 'user_id', 'unknown'),
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=_guardrail_detail(rejection_reason, language),
                )

    system_prompt = build_system_prompt(
        req.diagnostic_context,
        req.diagnostic_result,
        language,
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    body = {
        "model": settings.vllm_reasoning_model,
        "messages": messages,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
    }

    url = f"{settings.vllm_reasoning_url}/v1/chat/completions"
    timeout = httpx.Timeout(settings.vllm_timeout_seconds)

    logger.info(
        "sending chat request to vllm",
        extra={
            "turn": len(req.messages),
            "language": language,
            "model": settings.vllm_reasoning_model,
        },
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        logger.error("vllm chat timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="inference timeout",
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.error("vllm chat http error: %s", exc.response.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="inference backend error",
        ) from exc

    content = response.json()["choices"][0]["message"]["content"].strip()

    # SECURITY: Validate response stays in clinical context
    is_valid, validation_reason = is_valid_response(content, language)
    if not is_valid:
        logger.warning(
            "response_failed_validation",
            extra={"reason": validation_reason, "response": content[:100]},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Response validation failed. Model deviated from clinical context.",
        )

    logger.info(
        "chat response received",
        extra={"chars": len(content), "valid": is_valid},
    )
    return ChatResponse(message=content)
