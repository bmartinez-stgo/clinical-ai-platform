from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobStatus(BaseModel):
    job_id: str = Field(..., description="Unique job identifier. Use this to poll for status and result.")
    status: str = Field(
        ...,
        description=(
            "Current job state. One of: "
            "`queued` (waiting in line), "
            "`processing` (extraction running), "
            "`done` (result ready in `result` field), "
            "`failed` (see `error` field)."
        ),
    )
    position: int | None = Field(
        None,
        description="1-based queue position when `status` is `queued`. Null once processing starts.",
    )
    estimated_seconds: int | None = Field(
        None,
        description="Estimated seconds until processing begins. Null once processing starts.",
    )
    result: dict[str, Any] | None = Field(
        None,
        description="Parsed lab report. Populated only when `status` is `done`.",
    )
    error: str | None = Field(
        None,
        description="Error description. Populated only when `status` is `failed`.",
    )
