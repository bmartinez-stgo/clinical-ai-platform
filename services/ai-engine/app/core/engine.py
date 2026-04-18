from __future__ import annotations

import base64
import json
import logging
import os
import traceback
import re
from io import BytesIO
from typing import Any

import torch
from PIL import Image
from transformers import pipeline

from app.core.config import get_settings
from app.core.schema import ExtractionInput, ExtractionOutput

settings = get_settings()
_PIPELINE = None
logger = logging.getLogger(__name__)

FIRST_PAGE_INSTRUCTION_TEXT = """
Read this clinical laboratory report image and return only valid JSON.

The report may use any layout or format. Identify each individual laboratory measurement and extract its data.

Return this structure:
{
  "patient": {
    "external_id": string or null,
    "name": string or null,
    "sex": string or null,
    "date_of_birth": string or null
  },
  "report": {
    "laboratory_name": string or null,
    "report_date": string or null,
    "accession_number": string or null
  },
  "observations": [
    {
      "panel_raw": string or null,
      "test_name_raw": string,
      "value_raw": string or null,
      "unit_raw": string or null,
      "reference_range_raw": string or null,
      "specimen_raw": string or null,
      "page": integer,
      "confidence": number
    }
  ],
  "warnings": [string]
}

Field definitions:
- test_name_raw: the name of the specific analyte being measured — the individual item with its own result value (e.g., "Leucocitos", "Hemoglobina (Hb)", "Glucosa", "Creatinina"). This must be the label of the row that contains the result.
- panel_raw: the section or group header this analyte belongs to, if present (e.g., "Serie Blanca", "Quimica Sanguinea"). Null if not applicable.
- value_raw: the measured result exactly as it appears (e.g., "4,000.00", "15.20", "Negativo"). Preserve commas and decimals as printed.
- unit_raw: the measurement unit exactly as printed (e.g., "K/ul", "g/dl", "%"). Null if absent.
- reference_range_raw: the reference range exactly as printed (e.g., "4,600.00 - 10,200.00", ">0.50"). Null if absent.
- specimen_raw: the biological specimen type if explicitly stated (e.g., "Sangre", "Suero", "Orina"). Null if not stated.
- confidence: 0.0 to 1.0 extraction confidence.

Rules:
- Return one JSON object only. No markdown fences. No text outside JSON.
- One observation per analyte with an actual result value.
- Skip rows that are section or panel headers without their own result value.
- If a field is missing, use null.
- Extract only what is visible on this page.
""".strip()

CONTINUATION_PAGE_INSTRUCTION_TEXT = """
Read this clinical laboratory report image and return only valid JSON.

The report may use any layout or format. Identify each individual laboratory measurement and extract its data.

Return this structure:
{
  "observations": [
    {
      "panel_raw": string or null,
      "test_name_raw": string,
      "value_raw": string or null,
      "unit_raw": string or null,
      "reference_range_raw": string or null,
      "specimen_raw": string or null,
      "page": integer,
      "confidence": number
    }
  ],
  "warnings": [string]
}

Field definitions:
- test_name_raw: the name of the specific analyte being measured — the individual item with its own result value (e.g., "Leucocitos", "Hemoglobina (Hb)", "Glucosa"). This must be the label of the row that contains the result.
- panel_raw: the section or group header this analyte belongs to, if present. Null if not applicable.
- value_raw: the measured result exactly as it appears. Preserve commas and decimals as printed.
- unit_raw: the measurement unit exactly as printed. Null if absent.
- reference_range_raw: the reference range exactly as printed. Null if absent.
- specimen_raw: the biological specimen type if explicitly stated. Null if not stated.
- confidence: 0.0 to 1.0 extraction confidence.

Rules:
- Return one JSON object only. No markdown fences. No text outside JSON.
- One observation per analyte with an actual result value.
- Skip rows that are section or panel headers without their own result value.
- Do not include patient or report metadata.
- If a field is missing, use null.
- Extract only what is visible on this page.
""".strip()


def _get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        os.environ.setdefault("HF_HOME", settings.hf_home)
        os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
        cuda_available = torch.cuda.is_available()
        if settings.device_preference == "cuda" and not cuda_available:
            raise RuntimeError("CUDA was requested for ai-engine but no GPU is available inside the container")
        torch_dtype = torch.bfloat16 if settings.device_preference == "cuda" and cuda_available else torch.float32
        device_map = "auto" if settings.device_preference == "cuda" and cuda_available else "cpu"
        logger.info(
            "loading inference pipeline",
            extra={
                "engine_id": settings.engine_id,
                "device_preference": settings.device_preference,
                "device_map": device_map,
                "cuda_available": cuda_available,
                "cuda_device_count": torch.cuda.device_count(),
            },
        )
        _PIPELINE = pipeline(
            task="image-text-to-text",
            model=settings.engine_id,
            device_map=device_map,
            torch_dtype=torch_dtype,
        )
        logger.info("inference pipeline loaded")
    return _PIPELINE


def warmup_pipeline() -> None:
    _get_pipeline()


def _decode_pages(payload: ExtractionInput) -> list[Image.Image]:
    images: list[Image.Image] = []
    for page in payload.pages:
        image_bytes = base64.b64decode(page.image_base64)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        if settings.debug_logging:
            logger.debug(
                "decoded page image",
                extra={
                    "document_id": payload.document_id,
                    "page_number": page.page_number,
                    "mime_type": page.mime_type,
                    "width": image.width,
                    "height": image.height,
                },
            )
        images.append(image)
    return images


def _build_messages(images: list[Image.Image], instruction_text: str) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for image in images:
        content.append(
            {
                "type": "image",
                "image": image,
            }
        )
    content.append(
        {
            "type": "text",
            "text": instruction_text,
        }
    )
    return [
        {
            "role": "user",
            "content": content,
        }
    ]


def _prepare_json_candidate(text: str) -> str:
    candidate = text.strip()
    if "```" in candidate:
        fragments = [fragment.strip() for fragment in candidate.split("```") if fragment.strip()]
        for fragment in fragments:
            if fragment.startswith("json"):
                fragment = fragment[4:].strip()
            if fragment.startswith("{") and fragment.endswith("}"):
                candidate = fragment
                break

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("inference engine did not return a JSON object")
    return sanitize_json_candidate(candidate[start : end + 1])


def _extract_json(text: str) -> dict[str, Any]:
    return json.loads(_prepare_json_candidate(text))


def sanitize_json_candidate(candidate: str) -> str:
    sanitized = candidate
    sanitized = sanitized.replace("\u201c", '"').replace("\u201d", '"')
    sanitized = sanitized.replace("\u2018", "'").replace("\u2019", "'")
    sanitized = sanitized.replace("\r\n", "\n")
    sanitized = sanitized.replace("\t", " ")
    sanitized = re.sub(r",\s*}", "}", sanitized)
    sanitized = re.sub(r",\s*]", "]", sanitized)
    return sanitized


def _json_error_context(text: str, position: int, radius: int = 120) -> str:
    start = max(0, position - radius)
    end = min(len(text), position + radius)
    snippet = text[start:end]
    pointer_offset = position - start
    pointer = " " * max(0, pointer_offset) + "^"
    return f"{snippet}\n{pointer}"


def _extract_balanced_segment(text: str, start_index: int, open_char: str, close_char: str) -> tuple[str | None, int]:
    depth = 0
    in_string = False
    escape = False

    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1], index + 1

    return None, start_index


def _extract_named_object(candidate: str, key: str) -> dict[str, Any] | None:
    marker = f'"{key}"'
    key_index = candidate.find(marker)
    if key_index == -1:
        return None
    object_start = candidate.find("{", key_index)
    if object_start == -1:
        return None
    segment, _ = _extract_balanced_segment(candidate, object_start, "{", "}")
    if not segment:
        return None
    return json.loads(sanitize_json_candidate(segment))


def _extract_named_array(candidate: str, key: str) -> list[Any] | None:
    marker = f'"{key}"'
    key_index = candidate.find(marker)
    if key_index == -1:
        return None
    array_start = candidate.find("[", key_index)
    if array_start == -1:
        return None
    segment, _ = _extract_balanced_segment(candidate, array_start, "[", "]")
    if not segment:
        return None
    return json.loads(sanitize_json_candidate(segment))


def _extract_observations_array(candidate: str) -> list[dict[str, Any]]:
    marker = '"observations"'
    key_index = candidate.find(marker)
    if key_index == -1:
        return []

    array_start = candidate.find("[", key_index)
    if array_start == -1:
        return []

    observations: list[dict[str, Any]] = []
    cursor = array_start + 1
    while cursor < len(candidate):
        next_object = candidate.find("{", cursor)
        next_array_end = candidate.find("]", cursor)

        if next_array_end != -1 and (next_object == -1 or next_array_end < next_object):
            break
        if next_object == -1:
            break

        segment, next_cursor = _extract_balanced_segment(candidate, next_object, "{", "}")
        if not segment:
            break

        try:
            observations.append(json.loads(sanitize_json_candidate(segment)))
        except Exception:
            pass
        cursor = next_cursor

    return observations


def _recover_partial_payload(text: str, include_metadata: bool) -> dict[str, Any]:
    candidate = sanitize_json_candidate(text)
    recovered: dict[str, Any] = {
        "patient": {},
        "report": {},
        "observations": [],
        "warnings": [],
    }

    if include_metadata:
        patient = _extract_named_object(candidate, "patient")
        report = _extract_named_object(candidate, "report")
        if patient is not None:
            recovered["patient"] = patient
        if report is not None:
            recovered["report"] = report

    warnings = _extract_named_array(candidate, "warnings")
    if isinstance(warnings, list):
        recovered["warnings"] = [item for item in warnings if isinstance(item, str)]

    recovered["observations"] = _extract_observations_array(candidate)
    return recovered


def _normalize_confidence_value(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0

    if confidence > 1.0:
        confidence = confidence / 10.0
    return max(0.0, min(confidence, 1.0))


def _normalize_parsed_payload(parsed: dict[str, Any], include_metadata: bool) -> dict[str, Any]:
    normalized_patient = parsed.get("patient", {}) if include_metadata else {}
    normalized_report = parsed.get("report", {}) if include_metadata else {}
    normalized_warnings = parsed.get("warnings", [])
    normalized_observations: list[dict[str, Any]] = []

    for item in parsed.get("observations", []):
        if not isinstance(item, dict):
            continue
        normalized_item = dict(item)
        normalized_item["confidence"] = _normalize_confidence_value(item.get("confidence"))
        normalized_observations.append(normalized_item)

    return {
        "patient": normalized_patient if isinstance(normalized_patient, dict) else {},
        "report": normalized_report if isinstance(normalized_report, dict) else {},
        "observations": normalized_observations,
        "warnings": [warning for warning in normalized_warnings if isinstance(warning, str)] if isinstance(normalized_warnings, list) else [],
    }


def run_extraction(payload: ExtractionInput) -> ExtractionOutput:
    logger.info(
        "starting extraction request",
        extra={
            "document_id": payload.document_id,
            "document_filename": payload.filename,
            "content_type": payload.content_type,
            "page_count": len(payload.pages),
        },
    )
    logger.info("stage=get_pipeline", extra={"document_id": payload.document_id})
    try:
        extractor = _get_pipeline()
    except Exception as exc:
        logger.exception("failed to get inference pipeline")
        raise ValueError(f"failed to initialize inference pipeline: {exc}") from exc

    logger.info("stage=decode_pages_start", extra={"document_id": payload.document_id})
    try:
        images = _decode_pages(payload)
        logger.info(
            "stage=decode_pages_done",
            extra={
                "document_id": payload.document_id,
                "image_count": len(images),
            },
        )
    except Exception as exc:
        logger.exception(
            "failed to decode input pages",
            extra={"document_id": payload.document_id},
        )
        raise ValueError(f"failed to decode input pages: {exc}") from exc

    logger.info("stage=build_messages_start", extra={"document_id": payload.document_id})
    try:
        instruction_text = FIRST_PAGE_INSTRUCTION_TEXT if payload.include_metadata else CONTINUATION_PAGE_INSTRUCTION_TEXT
        messages = _build_messages(images, instruction_text)
        logger.info(
            "stage=build_messages_done",
            extra={
                "document_id": payload.document_id,
                "message_count": len(messages),
                "content_items": len(messages[0].get("content", [])) if messages else 0,
            },
        )
        if settings.debug_logging:
            logger.debug(
                "built multimodal messages",
                extra={
                    "document_id": payload.document_id,
                    "message_count": len(messages),
                    "content_items": len(messages[0].get("content", [])) if messages else 0,
                },
            )
    except Exception as exc:
        logger.exception(
            "failed to build multimodal messages",
            extra={"document_id": payload.document_id},
        )
        raise ValueError(f"failed to build multimodal messages: {exc}") from exc

    try:
        logger.info(
            "stage=model_invoke_start",
            extra={"document_id": payload.document_id},
        )
        logger.info(
            "invoking multimodal model",
            extra={
                "document_id": payload.document_id,
                "engine_id": settings.engine_id,
                "max_new_tokens": settings.max_new_tokens,
            },
        )
        generated = extractor(
            text=messages,
            max_new_tokens=settings.max_new_tokens,
            return_full_text=False,
        )
        logger.info(
            "stage=model_invoke_done",
            extra={"document_id": payload.document_id},
        )
    except Exception as exc:
        logger.exception(
            "model invocation failed",
            extra={"document_id": payload.document_id},
        )
        raise ValueError(f"model invocation failed: {exc}") from exc

    if not generated:
        raise ValueError("inference engine returned no content")

    if isinstance(generated, list):
        if isinstance(generated[0], dict):
            generated_text = generated[0].get("generated_text", "")
        else:
            generated_text = str(generated[0])
    else:
        generated_text = str(generated)

    if isinstance(generated_text, list):
        assistant_messages = [item for item in generated_text if isinstance(item, dict) and item.get("role") == "assistant"]
        if not assistant_messages:
            raise ValueError("inference engine did not return assistant content")
        assistant_content = assistant_messages[-1].get("content", [])
        text_fragments = []
        for item in assistant_content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_fragments.append(item.get("text", ""))
        generated_text = "\n".join(fragment for fragment in text_fragments if fragment)

    logger.info(
        "received model output",
        extra={
            "document_id": payload.document_id,
            "generated_type": type(generated_text).__name__,
        },
    )
    if settings.debug_logging:
        logger.debug(
            "model output preview document_id=%s preview=%s",
            payload.document_id,
            str(generated_text)[: settings.generated_preview_chars],
        )

    try:
        parsed = _extract_json(generated_text)
    except Exception as exc:
        generated_preview = str(generated_text)[: settings.generated_preview_chars]
        logger.exception(
            "failed to parse extraction output",
            extra={
                "document_id": payload.document_id,
            },
        )
        logger.error("failed to parse extraction output preview document_id=%s preview=%s", payload.document_id, generated_preview)
        if isinstance(exc, json.JSONDecodeError):
            logger.error(
                "failed to parse extraction output context document_id=%s line=%s column=%s position=%s context=%s",
                payload.document_id,
                exc.lineno,
                exc.colno,
                exc.pos,
                _json_error_context(str(generated_text), exc.pos),
            )
        logger.error("failed to parse extraction output trace document_id=%s traceback=%s", payload.document_id, traceback.format_exc())
        recovered = _recover_partial_payload(str(generated_text), payload.include_metadata)
        if recovered.get("observations"):
            logger.warning(
                "recovered partial extraction output document_id=%s observation_count=%s include_metadata=%s",
                payload.document_id,
                len(recovered["observations"]),
                payload.include_metadata,
            )
            parsed = recovered
        else:
            raise ValueError(f"failed to parse model output: {exc}") from exc
    parsed = _normalize_parsed_payload(parsed, payload.include_metadata)
    parsed["document_id"] = payload.document_id
    logger.info(
        "completed extraction request",
        extra={
            "document_id": payload.document_id,
            "observation_count": len(parsed.get("observations", [])),
        },
    )
    try:
        return ExtractionOutput.model_validate(parsed)
    except Exception as exc:
        logger.exception(
            "failed to validate extraction output",
            extra={
                "document_id": payload.document_id,
            },
        )
        logger.error(
            "failed to validate extraction output preview document_id=%s parsed=%s",
            payload.document_id,
            str(parsed)[: settings.generated_preview_chars],
        )
        logger.error("failed to validate extraction output trace document_id=%s traceback=%s", payload.document_id, traceback.format_exc())
        raise ValueError(f"failed to validate model output: {exc}") from exc
