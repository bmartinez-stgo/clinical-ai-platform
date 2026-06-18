from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | processing | done | failed
    position: int | None = None
    estimated_seconds: int | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
