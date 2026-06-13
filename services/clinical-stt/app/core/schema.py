from __future__ import annotations

from pydantic import BaseModel


class ICD10Code(BaseModel):
    code: str
    description: str
    confidence: str  # high | medium | low


class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    transcript: str
    language: str
    duration_seconds: float | None = None
    icd10_suggestions: list[ICD10Code] = []


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | processing | done | failed
    position: int | None = None
    result: SOAPNote | None = None
    error: str | None = None
