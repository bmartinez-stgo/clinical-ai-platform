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


class Vitals(BaseModel):
    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    temperature_celsius: float | None = None
    heart_rate: int | None = None


class PhysicalFindings(BaseModel):
    affected_systems: list[str] = Field(default_factory=list)
    free_text: str | None = None


class ImagingStudy(BaseModel):
    study_date: str | None = None
    modality: str
    findings: str


class Biopsy(BaseModel):
    date: str | None = None
    tissue: str
    findings: str


class PatientInfo(BaseModel):
    external_id: str | None = None
    age: int
    sex: Literal["male", "female", "other"]
    ethnicity: str | None = None
    weight_kg: float | None = None
    height_cm: float | None = None


class ClinicalHistory(BaseModel):
    family_autoimmune: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    pregnancies: int | None = None
    miscarriages: int | None = None
    symptom_onset_date: str | None = None
    symptom_duration_days: int | None = None


class DiagnosticRequest(BaseModel):
    request_id: str | None = None
    patient: PatientInfo
    history: ClinicalHistory = Field(default_factory=ClinicalHistory)
    vitals: Vitals = Field(default_factory=Vitals)
    physical_findings: PhysicalFindings = Field(default_factory=PhysicalFindings)
    lab_series: list[LabSnapshot]
    imaging: list[ImagingStudy] = Field(default_factory=list)
    biopsies: list[Biopsy] = Field(default_factory=list)
    clinical_diagnosis: str
    doctor_observations: str | None = None
    focus: list[str] = Field(default_factory=lambda: ["autoimmune"])
    language: str = "es"


class AutoimmuneFlag(BaseModel):
    condition: str
    likelihood: Literal["high", "moderate", "low"]
    supporting_findings: list[str]
    missing_workup: list[str] = Field(default_factory=list)


class AbnormalMarker(BaseModel):
    test_name: str
    loinc_code: str | None = None
    value: float | str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    direction: Literal["high", "low", "critical"]
    report_date: str


class MarkerCorrelation(BaseModel):
    pattern: str
    markers_involved: list[str]
    interpretation: str


class LabAbnormalitySummary(BaseModel):
    abnormal_count: int
    abnormal_markers: list[AbnormalMarker]
    correlations: list[MarkerCorrelation]


class DiagnosticResponse(BaseModel):
    request_id: str | None = None
    lab_abnormalities: LabAbnormalitySummary = Field(
        default_factory=lambda: LabAbnormalitySummary(
            abnormal_count=0, abnormal_markers=[], correlations=[]
        )
    )
    autoimmune_flags: list[AutoimmuneFlag]
    differential: list[str]
    recommended_followup: list[str]
    reasoning: str
    confidence: Literal["high", "moderate", "low"]
    disclaimer: str = (
        "Este resultado es una herramienta de apoyo diagnóstico. "
        "El diagnóstico clínico definitivo es responsabilidad del médico tratante."
    )
