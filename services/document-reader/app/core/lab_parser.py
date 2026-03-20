from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.core.terminology import LAB_DEFINITIONS, UNIT_NORMALIZATION, LabDefinition

PATIENT_ID_PATTERNS = (
    re.compile(r"^ID Paciente:\s*(.+)$", re.IGNORECASE),
    re.compile(r"^Paciente ID:\s*(.+)$", re.IGNORECASE),
)
PATIENT_NAME_PATTERNS = (
    re.compile(r"^Paciente:\s*(.+)$", re.IGNORECASE),
    re.compile(r"^Nombre:\s*(.+)$", re.IGNORECASE),
)
NUMERIC_LINE_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")
RANGE_PATTERN = re.compile(
    r"(?P<low>-?\d+(?:\.\d+)?)\s*-\s*(?P<high>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^ ]+)?"
)
GREATER_THAN_PATTERN = re.compile(
    r"^>\s*(?P<low>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^ ]+)?$"
)


def normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"\s+", " ", ascii_text.strip().lower())
    return cleaned


def normalize_unit(unit: str | None, fallback: str | None = None) -> str | None:
    if unit:
        key = normalize_text(unit)
        normalized = UNIT_NORMALIZATION.get(key)
        if normalized:
            return normalized
        return unit.strip()
    return fallback


def find_lab_definition(line: str) -> LabDefinition | None:
    normalized_line = normalize_text(line)
    for definition in LAB_DEFINITIONS:
        if any(
            normalized_line == alias
            or normalized_line.startswith(f"{alias} ")
            or normalized_line.startswith(f"{alias}(")
            for alias in definition.aliases
        ):
            return definition
    return None


def parse_reference_range(line: str, fallback_unit: str | None) -> dict[str, Any] | None:
    range_match = RANGE_PATTERN.search(line)
    if range_match:
        unit = normalize_unit(range_match.group("unit"), fallback_unit)
        return {
            "type": "interval",
            "low": float(range_match.group("low")),
            "high": float(range_match.group("high")),
            "unit_ucum": unit,
        }

    greater_than_match = GREATER_THAN_PATTERN.search(line.strip())
    if greater_than_match:
        unit = normalize_unit(greater_than_match.group("unit"), fallback_unit)
        return {
            "type": "lower-bound",
            "low": float(greater_than_match.group("low")),
            "high": None,
            "unit_ucum": unit,
        }

    return None


def extract_patient(lines: list[str]) -> dict[str, Any]:
    patient = {"external_id": None, "name": None}

    for line in lines:
        for pattern in PATIENT_ID_PATTERNS:
            match = pattern.search(line)
            if match:
                patient["external_id"] = match.group(1).strip()
                break

        for pattern in PATIENT_NAME_PATTERNS:
            match = pattern.search(line)
            if match:
                patient["name"] = match.group(1).strip()
                break

        if patient["external_id"] and patient["name"]:
            break

    return patient


def parse_numeric_value(line: str) -> float | None:
    if not NUMERIC_LINE_PATTERN.match(line.strip()):
        return None
    return float(line.strip())


def determine_interpretation(value: float, reference_range: dict[str, Any] | None) -> str | None:
    if not reference_range:
        return None

    if reference_range["type"] == "interval":
        if value < reference_range["low"]:
            return "low"
        if value > reference_range["high"]:
            return "high"
        return "normal"

    if reference_range["type"] == "lower-bound":
        if value < reference_range["low"]:
            return "low"
        return "normal"

    return None


def collect_sequential_results(lines: list[str]) -> tuple[list[dict[str, Any]], set[int]]:
    results: list[dict[str, Any]] = []
    consumed_indexes: set[int] = set()
    index = 0

    while index < len(lines):
        definition = find_lab_definition(lines[index])
        if not definition:
            index += 1
            continue

        definitions = [(definition, index, lines[index])]
        first_definition_index = index
        cursor = index + 1

        while cursor < len(lines):
            if lines[cursor] == "___":
                break

            nested_definition = find_lab_definition(lines[cursor])
            if nested_definition:
                definitions.append((nested_definition, cursor, lines[cursor]))

            cursor += 1

        if cursor >= len(lines) or lines[cursor] != "___":
            index += 1
            continue

        lead_value = None
        if first_definition_index > 0:
            lead_value = parse_numeric_value(lines[first_definition_index - 1])

        cursor += 1
        values: list[float] = []
        while cursor < len(lines):
            parsed_value = parse_numeric_value(lines[cursor])
            if parsed_value is None:
                break
            values.append(parsed_value)
            cursor += 1

        ranges: list[dict[str, Any] | None] = []
        range_lines: list[str | None] = []
        while cursor < len(lines):
            parsed_range = parse_reference_range(lines[cursor], None)
            if not parsed_range:
                break
            ranges.append(parsed_range)
            range_lines.append(lines[cursor])
            cursor += 1

        if lead_value is not None:
            values = [lead_value] + values

        if len(values) < len(definitions):
            index += 1
            continue

        for position, (current_definition, line_index, raw_line) in enumerate(definitions):
            reference_range = ranges[position] if position < len(ranges) else None
            reference_range_raw = range_lines[position] if position < len(range_lines) else None
            unit_ucum = (
                reference_range["unit_ucum"]
                if reference_range and reference_range.get("unit_ucum")
                else current_definition.default_unit_ucum
            )
            current_value = values[position]

            results.append(
                {
                    "test_name_raw": raw_line,
                    "test_name_normalized": current_definition.canonical_name,
                    "loinc_code": current_definition.loinc_code,
                    "value": int(current_value) if current_value.is_integer() else current_value,
                    "value_type": "numeric",
                    "unit_raw": unit_ucum,
                    "unit_ucum": unit_ucum,
                    "reference_range_raw": reference_range_raw,
                    "reference_range": reference_range,
                    "interpretation": determine_interpretation(current_value, reference_range),
                    "mapping_confidence": 0.96,
                }
            )
            consumed_indexes.add(line_index)

        index = cursor

    deduped_results: list[dict[str, Any]] = []
    dedupe_keys: set[tuple[str, float, str | None]] = set()
    for item in results:
        dedupe_key = (
            item["test_name_normalized"],
            float(item["value"]),
            item["reference_range_raw"],
        )
        if dedupe_key in dedupe_keys:
            continue
        dedupe_keys.add(dedupe_key)
        deduped_results.append(item)

    return deduped_results, consumed_indexes


def extract_observations(lines: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    observations, consumed_indexes = collect_sequential_results(lines)
    warnings: list[str] = []
    consumed_names: set[tuple[str, float]] = set()

    for observation in observations:
        consumed_names.add((observation["test_name_normalized"], float(observation["value"])))

    for index, line in enumerate(lines):
        if index in consumed_indexes:
            continue

        definition = find_lab_definition(line)
        if not definition:
            continue

        value = None
        reference_range = None
        reference_range_raw = None
        unit_ucum = definition.default_unit_ucum

        for candidate in lines[index + 1 : index + 6]:
            if value is None:
                parsed_value = parse_numeric_value(candidate)
                if parsed_value is not None:
                    value = parsed_value
                    continue

            if reference_range is None:
                parsed_range = parse_reference_range(candidate, definition.default_unit_ucum)
                if parsed_range:
                    reference_range = parsed_range
                    reference_range_raw = candidate
                    unit_ucum = parsed_range["unit_ucum"]

        if value is None:
            if any(item["test_name_normalized"] == definition.canonical_name for item in observations):
                continue
            warnings.append(f"no numeric value found for '{line}'")
            continue

        dedupe_key = (definition.canonical_name, value)
        if dedupe_key in consumed_names:
            continue
        consumed_names.add(dedupe_key)

        observations.append(
            {
                "test_name_raw": line,
                "test_name_normalized": definition.canonical_name,
                "loinc_code": definition.loinc_code,
                "value": int(value) if value.is_integer() else value,
                "value_type": "numeric",
                "unit_raw": unit_ucum,
                "unit_ucum": unit_ucum,
                "reference_range_raw": reference_range_raw,
                "reference_range": reference_range,
                "interpretation": determine_interpretation(value, reference_range),
                "mapping_confidence": 0.9,
            }
        )

    return observations, warnings


def build_normalized_lab_result(document_payload: dict[str, Any]) -> dict[str, Any]:
    lines = document_payload.get("lines", [])
    patient = extract_patient(lines)
    observations, warnings = extract_observations(lines)

    return {
        "document_id": document_payload["document_id"],
        "filename": document_payload["filename"],
        "document_type": "lab_report",
        "patient": patient,
        "observation_count": len(observations),
        "observations": observations,
        "unmapped_items": [],
        "warnings": warnings,
        "source": {
            "page_count": document_payload["page_count"],
            "character_count": document_payload["character_count"],
            "content_type": document_payload["content_type"],
        },
    }
