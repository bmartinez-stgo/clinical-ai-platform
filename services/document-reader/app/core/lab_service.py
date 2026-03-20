from __future__ import annotations

from typing import Any

from app.core.document_profile import detect_document_profile
from app.core.lab_parser import build_normalized_lab_result


def normalize_lab_document(document_payload: dict[str, Any]) -> dict[str, Any]:
    profile = detect_document_profile(document_payload)

    if profile.requires_ocr:
        return {
            "document_id": document_payload["document_id"],
            "filename": document_payload["filename"],
            "document_type": "lab_report",
            "extraction_profile": profile.profile_name,
            "confidence": 0.0,
            "requires_ocr": True,
            "patient": {"external_id": None, "name": None},
            "observation_count": 0,
            "observations": [],
            "unmapped_items": [],
            "warnings": ["document requires OCR-capable extraction"],
            "source": {
                "page_count": document_payload["page_count"],
                "character_count": document_payload["character_count"],
                "content_type": document_payload["content_type"],
                "text_density": round(profile.text_density, 2),
            },
        }

    result = build_normalized_lab_result(document_payload)
    result["extraction_profile"] = profile.profile_name
    result["requires_ocr"] = False
    result["confidence"] = calculate_result_confidence(result, profile.profile_name)
    result["source"]["text_density"] = round(profile.text_density, 2)
    return result


def calculate_result_confidence(result: dict[str, Any], profile_name: str) -> float:
    observation_count = result.get("observation_count", 0)
    warnings = result.get("warnings", [])
    mapped = len([item for item in result.get("observations", []) if item.get("loinc_code")])

    if observation_count == 0:
        return 0.0

    coverage = mapped / observation_count
    penalty = min(len(warnings) * 0.05, 0.25)
    profile_bonus = 0.1 if profile_name == "digital_tabular_lab" else 0.0
    confidence = 0.7 + (coverage * 0.2) + profile_bonus - penalty
    return round(max(0.0, min(confidence, 0.99)), 2)
