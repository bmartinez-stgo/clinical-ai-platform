from __future__ import annotations

import re
import unicodedata
from typing import Any
from uuid import uuid4

from app.core.terminology import LAB_DEFINITIONS, UNIT_NORMALIZATION

RANGE_PATTERN = re.compile(
    r"(?P<low>-?\d+(?:\.\d+)?)\s*[-–]\s*(?P<high>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^%µ ]+)?"
)
BOUND_PATTERN = re.compile(
    r"^(?P<op>>|<)\s*(?P<bound>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^%µ ]+)?$"
)
NUMERIC_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")


def normalize_text(value: str) -> str:
    value = value.replace("µ", "u").replace("μ", "u")
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.strip().lower())


def normalize_unit(unit: str | None, fallback: str | None = None) -> str | None:
    if unit:
        key = normalize_text(unit)
        return UNIT_NORMALIZATION.get(key, unit.strip())
    return fallback


def normalize_sex(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_text(value)
    if normalized in {"masculino", "male"}:
        return "male"
    if normalized in {"femenino", "female"}:
        return "female"
    return None


def find_definition(test_name_raw: str) -> Any:
    normalized = normalize_text(test_name_raw)
    matches: list[tuple[int, Any]] = []
    for definition in LAB_DEFINITIONS:
        for alias in definition.aliases:
            if (
                normalized == alias
                or normalized.startswith(f"{alias} ")
                or normalized.startswith(f"{alias}(")
            ):
                matches.append((len(alias), definition))
                break

    if matches:
        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]
    return None


def parse_reference_range(reference_range_raw: str | None, fallback_unit: str | None) -> dict[str, Any] | None:
    if not reference_range_raw:
        return None

    value = reference_range_raw.strip()
    match = RANGE_PATTERN.search(value)
    if match:
        return {
            "low": float(match.group("low")),
            "high": float(match.group("high")),
            "unit_ucum": normalize_unit(match.group("unit"), fallback_unit),
        }

    match = BOUND_PATTERN.search(value)
    if match:
        op = match.group("op")
        bound = float(match.group("bound"))
        return {
            "low": bound if op == ">" else None,
            "high": bound if op == "<" else None,
            "unit_ucum": normalize_unit(match.group("unit"), fallback_unit),
        }

    return None


def parse_value(raw_value: str | None) -> tuple[Any, str]:
    if raw_value is None:
        return (None, "text")
    stripped = raw_value.strip()
    if NUMERIC_PATTERN.match(stripped):
        value = float(stripped)
        return ((int(value) if value.is_integer() else value), "numeric")
    return (stripped, "text")


def determine_interpretation(value: Any, reference_range: dict[str, Any] | None) -> str | None:
    if reference_range is None or not isinstance(value, (int, float)):
        return None

    low = reference_range.get("low")
    high = reference_range.get("high")
    if low is not None and value < low:
        return "low"
    if high is not None and value > high:
        return "high"
    if low is not None or high is not None:
        return "normal"
    return None


def normalize_observation(raw_observation: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    definition = find_definition(raw_observation.get("test_name_raw", ""))
    raw_value, value_type = parse_value(raw_observation.get("value_raw"))
    reference_range = parse_reference_range(
        raw_observation.get("reference_range_raw"),
        definition.default_unit_ucum if definition else normalize_unit(raw_observation.get("unit_raw")),
    )
    unit_ucum = (
        reference_range["unit_ucum"]
        if reference_range and reference_range.get("unit_ucum")
        else normalize_unit(raw_observation.get("unit_raw"), definition.default_unit_ucum if definition else None)
    )

    normalized = {
        "observation_id": str(uuid4()),
        "panel_raw": raw_observation.get("panel_raw"),
        "test_name_raw": raw_observation.get("test_name_raw"),
        "test_name_normalized": definition.canonical_name if definition else raw_observation.get("test_name_raw"),
        "loinc_code": definition.loinc_code if definition else None,
        "value": raw_value,
        "value_type": value_type,
        "unit_raw": raw_observation.get("unit_raw"),
        "unit_ucum": unit_ucum,
        "reference_range_raw": raw_observation.get("reference_range_raw"),
        "reference_range": reference_range,
        "interpretation": determine_interpretation(raw_value, reference_range),
        "specimen": raw_observation.get("specimen_raw"),
        "page": raw_observation.get("page"),
        "confidence": raw_observation.get("confidence", 0.0),
    }

    requires_review = normalized["loinc_code"] is None or (value_type == "numeric" and normalized["unit_ucum"] is None)
    return normalized, requires_review


def build_normalized_response(document_payload: dict[str, Any], extraction_payload: dict[str, Any]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    unmapped_items: list[str] = []
    requires_manual_review = False

    for raw_observation in extraction_payload.get("observations", []):
        normalized_observation, review_required = normalize_observation(raw_observation)
        observations.append(normalized_observation)
        if review_required:
            unmapped_items.append(normalized_observation["test_name_raw"])
            requires_manual_review = True

    patient_payload = extraction_payload.get("patient", {})
    report_payload = extraction_payload.get("report", {})
    average_confidence = round(
        sum(item["confidence"] for item in observations) / len(observations),
        2,
    ) if observations else 0.0

    return {
        "document_id": document_payload["document_id"],
        "document_type": "lab_report",
        "source": {
            "filename": document_payload["filename"],
            "content_type": document_payload["content_type"],
            "page_count": document_payload["page_count"],
            "language": "es-MX",
        },
        "patient": {
            "external_id": patient_payload.get("external_id"),
            "name": patient_payload.get("name"),
            "sex": normalize_sex(patient_payload.get("sex")),
            "date_of_birth": patient_payload.get("date_of_birth"),
        },
        "report": {
            "laboratory_name": report_payload.get("laboratory_name"),
            "report_date": report_payload.get("report_date"),
            "accession_number": report_payload.get("accession_number"),
        },
        "observation_count": len(observations),
        "observations": observations,
        "unmapped_items": sorted(set(unmapped_items)),
        "warnings": extraction_payload.get("warnings", []),
        "confidence": average_confidence,
        "requires_manual_review": requires_manual_review,
    }
