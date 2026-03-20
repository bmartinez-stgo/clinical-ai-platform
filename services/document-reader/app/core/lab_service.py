from __future__ import annotations

from app.core.document_profile import detect_document_profile
from app.core.lab_normalization import build_normalized_response
from app.core.vision_client import extract_laboratory_observations


async def normalize_lab_document(document_payload: dict) -> dict:
    profile = detect_document_profile(document_payload)
    extraction_payload = await extract_laboratory_observations(
        {
            "document_id": document_payload["document_id"],
            "filename": document_payload["filename"],
            "content_type": document_payload["content_type"],
            "pages": [
                {
                    "page_number": page["page_number"],
                    "mime_type": page["mime_type"],
                    "image_base64": page["image_base64"],
                }
                for page in document_payload["pages"]
            ],
        }
    )
    result = build_normalized_response(document_payload, extraction_payload)
    result["extraction_profile"] = profile.profile_name
    result["requires_ocr"] = profile.requires_ocr
    result["confidence"] = calculate_result_confidence(result, profile.profile_name)
    result["source"]["text_density"] = round(profile.text_density, 2) if document_payload["character_count"] else None
    return result


def calculate_result_confidence(result: dict, profile_name: str) -> float:
    observation_count = len(result.get("observations", []))
    warnings = result.get("warnings", [])
    mapped = len([item for item in result.get("observations", []) if item.get("loinc_code")])

    if observation_count == 0:
        return 0.0

    coverage = mapped / observation_count
    penalty = min(len(warnings) * 0.05, 0.25)
    profile_bonus = 0.1 if profile_name == "digital_tabular_lab" else 0.0
    confidence = 0.7 + (coverage * 0.2) + profile_bonus - penalty
    return round(max(0.0, min(confidence, 0.99)), 2)
