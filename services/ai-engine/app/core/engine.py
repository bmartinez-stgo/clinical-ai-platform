from __future__ import annotations

import base64
import json
import logging
import os
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

INSTRUCTION_TEXT = """
Read every page image of this clinical laboratory report and return only valid JSON.

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

Do not omit observations that appear in tables, scanned sections, or mixed layouts.
Do not add explanations outside JSON.
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
        images.append(image)
    return images


def _build_messages(images: list[Image.Image]) -> list[dict[str, Any]]:
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
            "text": INSTRUCTION_TEXT,
        }
    )
    return [
        {
            "role": "user",
            "content": content,
        }
    ]


def _extract_json(text: str) -> dict[str, Any]:
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
    return json.loads(candidate[start : end + 1])


def run_extraction(payload: ExtractionInput) -> ExtractionOutput:
    logger.info(
        "starting extraction request",
        extra={
            "document_id": payload.document_id,
            "page_count": len(payload.pages),
        },
    )
    extractor = _get_pipeline()
    images = _decode_pages(payload)
    messages = _build_messages(images)
    generated = extractor(
        text=messages,
        max_new_tokens=settings.max_new_tokens,
        return_full_text=False,
    )

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

    try:
        parsed = _extract_json(generated_text)
    except Exception as exc:
        logger.exception(
            "failed to parse extraction output",
            extra={
                "document_id": payload.document_id,
                "generated_preview": str(generated_text)[:1000],
            },
        )
        raise ValueError(f"failed to parse model output: {exc}") from exc
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
                "parsed_preview": str(parsed)[:1000],
            },
        )
        raise ValueError(f"failed to validate model output: {exc}") from exc
