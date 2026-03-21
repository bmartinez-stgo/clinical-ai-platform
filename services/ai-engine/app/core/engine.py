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
        torch_dtype = torch.bfloat16 if settings.device_preference == "cuda" and torch.cuda.is_available() else torch.float32
        device_map = "auto" if settings.device_preference == "cuda" and torch.cuda.is_available() else "cpu"
        logger.info(
            "loading inference pipeline",
            extra={
                "engine_id": settings.engine_id,
                "device_preference": settings.device_preference,
                "device_map": device_map,
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
    generated = extractor(
        images=images,
        text=INSTRUCTION_TEXT,
        max_new_tokens=settings.max_new_tokens,
        temperature=settings.temperature,
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

    parsed = _extract_json(generated_text)
    parsed["document_id"] = payload.document_id
    logger.info(
        "completed extraction request",
        extra={
            "document_id": payload.document_id,
            "observation_count": len(parsed.get("observations", [])),
        },
    )
    return ExtractionOutput.model_validate(parsed)
