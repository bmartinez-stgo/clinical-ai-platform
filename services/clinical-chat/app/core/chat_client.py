from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.prompt import build_system_prompt
from app.core.schema import ChatRequest, ChatResponse

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_chat(req: ChatRequest) -> ChatResponse:
    system_prompt = build_system_prompt(
        req.diagnostic_context,
        req.diagnostic_result,
        req.language,
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
        extra={"turn": len(req.messages), "language": req.language},
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
    logger.info("chat response received", extra={"chars": len(content)})
    return ChatResponse(message=content)
