from __future__ import annotations

import asyncio
import logging
import re

from app.core.config import get_settings
from app.core.document_profile import detect_document_profile
from app.core.lab_normalization import (
    build_normalized_response,
    extract_deterministic_report_fields,
    needs_second_opinion,
    parse_value,
)
from app.core.vision_client import extract_laboratory_observations, verify_observation_value

settings = get_settings()
logger = logging.getLogger(__name__)

_extraction_semaphore = asyncio.Semaphore(3)

# The verify prompt asks ai-engine for value_raw and unit_raw separately, but
# a model occasionally glues them together anyway (e.g. "147mmol/L"). Pulling
# just the leading numeric run before parsing sidesteps parse_value's
# OCR o/O->0 correction mangling a unit's letters (e.g. the "o" in "mmol")
# into a false digit, which would otherwise read as a value mismatch that
# isn't really there.
_LEADING_NUMERIC = re.compile(r"^\s*(-?[\d,]+(?:\.\d+)?)")


def _parse_second_opinion_value(value_raw: str | None):
    if value_raw is None:
        return None
    match = _LEADING_NUMERIC.match(value_raw)
    token = match.group(1) if match else value_raw
    value, _ = parse_value(token)
    return value


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
    async with _extraction_semaphore:
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


async def apply_second_opinion_verification(result: dict, document_payload: dict) -> None:
    """Re-reads, independently, the observations flagged by
    needs_second_opinion (out of range, or at decade-crossing risk).
    Mutates `result` in place: sets each checked observation's
    `verification` field, and keeps requires_manual_review set unless the
    second read agrees with the first.
    """
    if settings.ocr_backend != "ai-engine" or not settings.second_opinion_enabled:
        return

    images_by_page = {page["page_number"]: page for page in document_payload.get("pages", [])}
    observations = result.get("observations", [])
    targets = [
        obs
        for obs in observations
        if obs.get("value_type") == "numeric"
        and needs_second_opinion(obs.get("interpretation"), obs.get("decade_crossing_risk", False))
    ]
    if not targets:
        return

    logger.info(
        "running second-opinion verification",
        extra={"document_id": result.get("document_id"), "flagged_count": len(targets)},
    )

    async def _verify(observation: dict) -> None:
        page = images_by_page.get(observation.get("page"))
        if page is None:
            return
        response = await verify_observation_value(
            {
                "document_id": result.get("document_id"),
                "page_number": page["page_number"],
                "mime_type": page["mime_type"],
                "image_base64": page["image_base64"],
                "test_name_raw": observation["test_name_raw"],
                "panel_raw": observation.get("panel_raw"),
            }
        )
        if response is None:
            observation["verification"] = {"status": "failed", "second_value_raw": None}
            return

        second_value = _parse_second_opinion_value(response.get("value_raw"))
        agrees = second_value is not None and second_value == observation["value"]
        observation["verification"] = {
            "status": "agrees" if agrees else "disagrees",
            "second_value_raw": response.get("value_raw"),
        }
        if not agrees:
            result["review_items"].append(
                {
                    "stage": "interpretation",
                    "reason": "second_opinion_disagreement",
                    "message": (
                        f"Independent re-read of this value disagreed with the first extraction: "
                        f"{observation['value']!r} vs {response.get('value_raw')!r}."
                    ),
                    "page": observation.get("page"),
                    "panel_raw": observation.get("panel_raw"),
                    "test_name_raw": observation.get("test_name_raw"),
                    "value_raw": observation["value"],
                    "unit_raw": observation.get("unit_raw"),
                    "reference_range_raw": observation.get("reference_range_raw"),
                    "specimen_raw": observation.get("specimen"),
                    "confidence": observation.get("confidence", 0.0),
                }
            )
            result["requires_manual_review"] = True

    await asyncio.gather(*[_verify(obs) for obs in targets])


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

    await apply_second_opinion_verification(result, document_payload)

    # Override determinístico de fecha de reporte / folio a partir del texto
    # embebido del PDF, cuando existe uno confiable (documento no-escaneado).
    # El modelo de visión sigue siendo la única fuente para los analitos.
    if not profile.requires_ocr and document_payload.get("pages"):
        first_page_text = document_payload["pages"][0].get("text", "")
        deterministic = extract_deterministic_report_fields(first_page_text)
        if deterministic["report_date"]:
            result["report"]["report_date"] = deterministic["report_date"]
        if deterministic["accession_number"]:
            result["report"]["accession_number"] = deterministic["accession_number"]
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
