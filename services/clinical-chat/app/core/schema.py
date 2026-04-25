from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    diagnostic_context: dict[str, Any]
    diagnostic_result: dict[str, Any]
    messages: list[ChatMessage]
    language: str = "es"


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    message: str
