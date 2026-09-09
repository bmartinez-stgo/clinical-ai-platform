from __future__ import annotations

from pydantic import BaseModel, Field


class PageInput(BaseModel):
    page_number: int = Field(..., ge=1)
    mime_type: str
    image_base64: str


class ExtractionInput(BaseModel):
    document_id: str
    filename: str
    content_type: str
    include_metadata: bool = True
    pages: list[PageInput]


class RawObservation(BaseModel):
    panel_raw: str | None = None
    test_name_raw: str
    value_raw: str | None = None
    unit_raw: str | None = None
    reference_range_raw: str | None = None
    specimen_raw: str | None = None
    # Optional: some models (e.g. OCR-specialized fine-tunes) don't echo
    # back a page number per observation. Defaults to the first page of
    # the batch; multi-page attribution degrades gracefully instead of
    # failing the whole extraction.
    page: int = 1
    confidence: float = Field(..., ge=0, le=1)


class ExtractionOutput(BaseModel):
    document_id: str
    patient: dict
    report: dict
    observations: list[RawObservation]
    warnings: list[str] = Field(default_factory=list)
