from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentProfile:
    profile_name: str
    requires_ocr: bool
    text_density: float
    has_structured_blocks: bool


def detect_document_profile(document_payload: dict[str, Any]) -> DocumentProfile:
    page_count = max(document_payload.get("page_count", 0), 1)
    character_count = document_payload.get("character_count", 0)
    pages = document_payload.get("pages", [])
    lines = document_payload.get("lines", [])

    text_density = character_count / page_count
    has_structured_blocks = any(page.get("blocks") for page in pages)
    has_tabular_markers = any(
        marker in line.lower()
        for line in lines
        for marker in ("límite", "limites", "referencia", "resultado", "prueba")
    )

    if text_density < 50:
        return DocumentProfile(
            profile_name="scanned_or_low_text",
            requires_ocr=True,
            text_density=text_density,
            has_structured_blocks=has_structured_blocks,
        )

    if has_structured_blocks and has_tabular_markers:
        return DocumentProfile(
            profile_name="digital_tabular_lab",
            requires_ocr=False,
            text_density=text_density,
            has_structured_blocks=True,
        )

    return DocumentProfile(
        profile_name="digital_generic_lab",
        requires_ocr=False,
        text_density=text_density,
        has_structured_blocks=has_structured_blocks,
    )
