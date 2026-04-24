from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.document_profile import detect_document_profile
from app.core.lab_normalization import build_normalized_response
from app.core.vision_client import extract_laboratory_observations

settings = get_settings()
logger = logging.getLogger(__name__)


def chunk_pages(pages: list[dict], batch_size: int) -> list[list[dict]]:
    if batch_size <= 0:
        batch_size = 1
    return [pages[index : index + batch_size] for index in range(0, len(pages), batch_size)]


def merge_extraction_payloads(document_id: str, payloads: list[dict]) -> dict:
    patient: dict = {}
    report: dict = {}
    observations: list[dict] = []
    warnings: list[str] = []

    for payload in payloads:
        for key, value in payload.get("patient", {}).items():
            if patient.get(key) is None and value is not None:
                patient[key] = value
        for key, value in payload.get("report", {}).items():
            if report.get(key) is None and value is not None:
                report[key] = value
        observations.extend(payload.get("observations", []))
        warnings.extend(payload.get("warnings", []))

    return {
        "document_id": document_id,
        "patient": patient,
        "report": report,
        "observations": observations,
        "warnings": warnings,
    }


async def _extract_batch(document_payload: dict, batch: list[dict], batch_index: int, batch_count: int) -> dict:
    document_id = document_payload.get("document_id")
    include_metadata = any(page["page_number"] == 1 for page in batch)
    logger.info(
        "sending extraction batch",
        extra={
            "document_id": document_id,
            "batch_index": batch_index,
            "batch_count": batch_count,
            "page_numbers": [page["page_number"] for page in batch],
            "include_metadata": include_metadata,
            "ocr_backend": settings.ocr_backend,
        },
    )
    result = await extract_laboratory_observations(
        {
            "document_id": document_payload["document_id"],
            "filename": document_payload["filename"],
            "content_type": document_payload["content_type"],
            "include_metadata": include_metadata,
            "pages": batch,
        }
    )
    logger.info(
        "received extraction batch",
        extra={
            "document_id": document_id,
            "batch_index": batch_index,
            "observation_count": len(result.get("observations", [])),
            "warning_count": len(result.get("warnings", [])),
            "ocr_backend": settings.ocr_backend,
        },
    )
    return result


async def normalize_lab_document(document_payload: dict, language: str = "en") -> dict:
    profile = detect_document_profile(document_payload)
    logger.info(
        "normalizing laboratory document",
        extra={
            "document_id": document_payload.get("document_id"),
            "document_filename": document_payload.get("filename"),
            "content_type": document_payload.get("content_type"),
            "page_count": len(document_payload.get("pages", [])),
            "ocr_backend": settings.ocr_backend,
            "profile_name": profile.profile_name,
            "requires_ocr": profile.requires_ocr,
            "text_density": round(profile.text_density, 2) if document_payload.get("character_count") else None,
        },
    )
    pages = [
        {
            "page_number": page["page_number"],
            "mime_type": page["mime_type"],
            "image_base64": page["image_base64"],
        }
        for page in document_payload["pages"]
    ]
    page_batches = chunk_pages(pages, settings.ai_engine_page_batch_size)

    extraction_payloads: list[dict] = list(
        await asyncio.gather(
            *[
                _extract_batch(document_payload, batch, idx, len(page_batches))
                for idx, batch in enumerate(page_batches, start=1)
            ]
        )
    )

    extraction_payload = merge_extraction_payloads(document_payload["document_id"], extraction_payloads)
    result = build_normalized_response(document_payload, extraction_payload, language=language)
    result["extraction_profile"] = profile.profile_name
    result["requires_ocr"] = profile.requires_ocr
    result["confidence"] = calculate_result_confidence(result, profile.profile_name)
    result["source"]["text_density"] = round(profile.text_density, 2) if document_payload["character_count"] else None
    logger.info(
        "completed laboratory document normalization",
        extra={
            "document_id": document_payload.get("document_id"),
            "observation_count": result.get("observation_count"),
            "warning_count": len(result.get("warnings", [])),
            "review_item_count": len(result.get("review_items", [])),
            "confidence": result.get("confidence"),
            "ocr_backend": settings.ocr_backend,
        },
    )
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
