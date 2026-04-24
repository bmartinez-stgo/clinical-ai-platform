from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LabResult(BaseModel):
    loinc_code: str | None = None
    test_name: str
    value: float | str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    interpretation: Literal["normal", "low", "high", "critical"] | None = None


class LabSnapshot(BaseModel):
    report_date: str
    results: list[LabResult]


class PatientSummary(BaseModel):
    age: int
    sex: str
    ethnicity: str | None = None


class StoreCaseRequest(BaseModel):
    case_id: str | None = None
    patient: PatientSummary
    lab_snapshot: LabSnapshot
    validated_diagnosis: str
    differential: list[str] = Field(default_factory=list)
    doctor_notes: str | None = None
    approved_by: str | None = None


class StoreCaseResponse(BaseModel):
    case_id: str
    stored: bool
    total_cases: int


class SimilarCasesRequest(BaseModel):
    patient: PatientSummary
    lab_results: list[LabResult]
    top_k: int = 3


class SimilarCase(BaseModel):
    case_id: str
    similarity: float
    patient_summary: str
    validated_diagnosis: str
    differential: list[str]
    doctor_notes: str | None = None


class SimilarCasesResponse(BaseModel):
    cases: list[SimilarCase]
    total_cases_in_store: int
