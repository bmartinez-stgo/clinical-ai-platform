from __future__ import annotations

import base64
import json
import logging
import os
import re
import traceback
from io import BytesIO
from typing import Any

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

from app.core.config import get_settings
from app.core.schema import ExtractionInput, ExtractionOutput

settings = get_settings()
_PROCESSOR = None
_MODEL = None
logger = logging.getLogger(__name__)

FIRST_PAGE_INSTRUCTION_TEXT = """
Please read this page image of a clinical laboratory report and return only valid JSON.

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

Rules:
- Return one JSON object only.
- Do not use markdown fences.
- Do not add explanations outside JSON.
- If a field is missing, use null.
- If there are no observations on this page, return an empty list.
- Extract only what is visible on this page.
""".strip()

CONTINUATION_PAGE_INSTRUCTION_TEXT = """
Please read this page image of a clinical laboratory report and return only valid JSON.

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

Rules:
- Return one JSON object only.
- Do not use markdown fences.
- Do not add explanations outside JSON.
- Do not include patient or report metadata on continuation pages.
- If there are no observations on this page, return an empty list.
- Extract only what is visible on this page.
""".strip()


def _get_components() -> tuple[Any, Any]:
    global _PROCESSOR, _MODEL
    if _PROCESSOR is None or _MODEL is None:
        os.environ.setdefault("HF_HOME", settings.hf_home)
        os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
        cuda_available = torch.cuda.is_available()
        if settings.device_preference == "cuda" and not cuda_available:
            raise RuntimeError("CUDA was requested for ocr-engine but no GPU is available inside the container")
        torch_dtype = torch.bfloat16 if settings.device_preference == "cuda" and cuda_available else torch.float32
        device_map = "auto" if settings.device_preference == "cuda" and cuda_available else "cpu"
        logger.info(
            "loading ocr model",
            extra={
                "engine_id": settings.engine_id,
                "device_preference": settings.device_preference,
                "device_map": device_map,
                "cuda_available": cuda_available,
                "cuda_device_count": torch.cuda.device_count(),
            },
        )
        _PROCESSOR = AutoProcessor.from_pretrained(settings.engine_id)
        _MODEL = AutoModelForImageTextToText.from_pretrained(
            pretrained_model_name_or_path=settings.engine_id,
            torch_dtype=torch_dtype,
            device_map=device_map,
        )
        logger.info("ocr model loaded")
    return _PROCESSOR, _MODEL


def warmup_pipeline() -> None:
    _get_components()


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


def sanitize_json_candidate(candidate: str) -> str:
    sanitized = candidate
    sanitized = sanitized.replace("\u201c", '"').replace("\u201d", '"')
    sanitized = sanitized.replace("\u2018", "'").replace("\u2019", "'")
    sanitized = sanitized.replace("\r\n", "\n")
    sanitized = sanitized.replace("\t", " ")
    sanitized = re.sub(r",\s*}", "}", sanitized)
    sanitized = re.sub(r",\s*]", "]", sanitized)
    return sanitized


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
        raise ValueError("ocr engine did not return a JSON object")
    return sanitize_json_candidate(candidate[start : end + 1])


def _extract_json(text: str) -> dict[str, Any]:
    return json.loads(_prepare_json_candidate(text))


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
        confidence = confidence / 100.0 if confidence > 10.0 else confidence / 10.0
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


def _generate_text(messages: list[dict[str, Any]], processor: Any, model: Any) -> str:
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    generated_ids = model.generate(**inputs, max_new_tokens=settings.max_new_tokens)
    generated_tail = generated_ids[0][inputs["input_ids"].shape[1] :]
    return processor.decode(generated_tail, skip_special_tokens=False)


def run_extraction(payload: ExtractionInput) -> ExtractionOutput:
    logger.info(
        "starting ocr extraction request",
        extra={
            "document_id": payload.document_id,
            "document_filename": payload.filename,
            "content_type": payload.content_type,
            "page_count": len(payload.pages),
        },
    )
    logger.info("stage=get_components", extra={"document_id": payload.document_id})
    try:
        processor, model = _get_components()
    except Exception as exc:
        logger.exception("failed to get ocr model components")
        raise ValueError(f"failed to initialize ocr engine: {exc}") from exc

    logger.info("stage=decode_pages_start", extra={"document_id": payload.document_id})
    try:
        images = _decode_pages(payload)
        logger.info("stage=decode_pages_done", extra={"document_id": payload.document_id, "image_count": len(images)})
    except Exception as exc:
        logger.exception("failed to decode input pages", extra={"document_id": payload.document_id})
        raise ValueError(f"failed to decode input pages: {exc}") from exc

    logger.info("stage=build_messages_start", extra={"document_id": payload.document_id})
    try:
        instruction_text = FIRST_PAGE_INSTRUCTION_TEXT if payload.include_metadata else CONTINUATION_PAGE_INSTRUCTION_TEXT
        messages = _build_messages(images, instruction_text)
        logger.info("stage=build_messages_done", extra={"document_id": payload.document_id, "message_count": len(messages)})
    except Exception as exc:
        logger.exception("failed to build multimodal messages", extra={"document_id": payload.document_id})
        raise ValueError(f"failed to build multimodal messages: {exc}") from exc

    try:
        logger.info("stage=model_invoke_start", extra={"document_id": payload.document_id})
        logger.info(
            "invoking ocr model",
            extra={"document_id": payload.document_id, "engine_id": settings.engine_id, "max_new_tokens": settings.max_new_tokens},
        )
        generated_text = _generate_text(messages, processor, model)
        logger.info("stage=model_invoke_done", extra={"document_id": payload.document_id})
    except Exception as exc:
        logger.exception("ocr model invocation failed", extra={"document_id": payload.document_id})
        raise ValueError(f"ocr model invocation failed: {exc}") from exc

    logger.info("received ocr model output", extra={"document_id": payload.document_id, "generated_type": type(generated_text).__name__})
    if settings.debug_logging:
        logger.debug("ocr model output preview document_id=%s preview=%s", payload.document_id, str(generated_text)[: settings.generated_preview_chars])

    try:
        parsed = _extract_json(generated_text)
    except Exception as exc:
        generated_preview = str(generated_text)[: settings.generated_preview_chars]
        logger.exception("failed to parse ocr extraction output", extra={"document_id": payload.document_id})
        logger.error("failed to parse ocr extraction output preview document_id=%s preview=%s", payload.document_id, generated_preview)
        if isinstance(exc, json.JSONDecodeError):
            logger.error(
                "failed to parse ocr extraction output context document_id=%s line=%s column=%s position=%s context=%s",
                payload.document_id,
                exc.lineno,
                exc.colno,
                exc.pos,
                _json_error_context(str(generated_text), exc.pos),
            )
        logger.error("failed to parse ocr extraction output trace document_id=%s traceback=%s", payload.document_id, traceback.format_exc())
        recovered = _recover_partial_payload(str(generated_text), payload.include_metadata)
        if recovered.get("observations"):
            logger.warning(
                "recovered partial ocr extraction output document_id=%s observation_count=%s include_metadata=%s",
                payload.document_id,
                len(recovered["observations"]),
                payload.include_metadata,
            )
            parsed = recovered
        else:
            raise ValueError(f"failed to parse ocr model output: {exc}") from exc

    parsed = _normalize_parsed_payload(parsed, payload.include_metadata)
    parsed["document_id"] = payload.document_id
    logger.info("completed ocr extraction request", extra={"document_id": payload.document_id, "observation_count": len(parsed.get("observations", []))})
    try:
        return ExtractionOutput.model_validate(parsed)
    except Exception as exc:
        logger.exception("failed to validate ocr extraction output", extra={"document_id": payload.document_id})
        logger.error(
            "failed to validate ocr extraction output preview document_id=%s parsed=%s",
            payload.document_id,
            str(parsed)[: settings.generated_preview_chars],
        )
        logger.error("failed to validate ocr extraction output trace document_id=%s traceback=%s", payload.document_id, traceback.format_exc())
        raise ValueError(f"failed to validate ocr model output: {exc}") from exc
