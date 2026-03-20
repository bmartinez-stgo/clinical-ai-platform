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
    r"(?P<low>-?\d+(?:\.\d+)?)\s*[-–]\s*(?P<high>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^%µ ]+)?"
)
GREATER_THAN_PATTERN = re.compile(
    r"^(?P<op>>|<)\s*(?P<bound>-?\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z/{}\._0-9^%µ ]+)?$"
)
QUALITATIVE_VALUES = {
    "negativo",
    "positivo",
    "claro",
    "turbio",
    "amarillo",
    "transparente",
    "escasas",
    "abundantes",
    "ausentes",
    "presente",
    "trazas",
}
IGNORED_EXACT_LINES = {
    "resultados",
    "análisis clínicos",
    "analisis clinicos",
    "prueba",
    "bajo (lr)",
    "dentro (lr)",
    "sobre (lr)",
    "limites de referencia",
    "límites de referencia",
    "nota:",
    "fuente:",
    "metodo: fotometria automatizada",
    "metodo: citometria de flujo",
}
IGNORED_PREFIXES = (
    "orden:",
    "id paciente:",
    "paciente:",
    "sexo:",
    "fecha de nacimiento:",
    "edad:",
    "fecha de registro:",
    "dirigido a:",
    "hoja:",
    "gracias por su preferencia",
    "grupo diagnostico medico",
    "sucursal",
    "www.",
    "metodo:",
    "descarga nuestra app",
    "negativo o",
    "col.",
    "aguascalientes",
    "luis donaldo colosio",
)
DATE_LIKE_PATTERN = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}")
TIME_LIKE_PATTERN = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}\s+\d")


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
    normalized_line = line.strip()
    range_match = RANGE_PATTERN.search(normalized_line)
    if range_match:
        unit = normalize_unit(range_match.group("unit"), fallback_unit)
        return {
            "type": "interval",
            "low": float(range_match.group("low")),
            "high": float(range_match.group("high")),
            "unit_ucum": unit,
        }

    greater_than_match = GREATER_THAN_PATTERN.search(normalized_line)
    if greater_than_match:
        unit = normalize_unit(greater_than_match.group("unit"), fallback_unit)
        op = greater_than_match.group("op")
        bound = float(greater_than_match.group("bound"))
        return {
            "type": "lower-bound" if op == ">" else "upper-bound",
            "low": bound if op == ">" else None,
            "high": bound if op == "<" else None,
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


def parse_value(line: str) -> tuple[Any, str] | None:
    numeric_value = parse_numeric_value(line)
    if numeric_value is not None:
        return ((int(numeric_value) if numeric_value.is_integer() else numeric_value), "numeric")

    normalized_line = normalize_text(line)
    if normalized_line in QUALITATIVE_VALUES:
        return (line.strip(), "text")

    return None


def determine_interpretation(value: Any, reference_range: dict[str, Any] | None) -> str | None:
    if not reference_range or not isinstance(value, (int, float)):
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

    if reference_range["type"] == "upper-bound":
        if value > reference_range["high"]:
            return "high"
        return "normal"

    return None


def is_ignored_line(line: str) -> bool:
    normalized_line = normalize_text(line)
    if not normalized_line or normalized_line in {"___", "====", "===================="}:
        return True

    if normalized_line in IGNORED_EXACT_LINES:
        return True

    if any(normalized_line.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return True

    if normalized_line.isdigit() and len(normalized_line) > 5:
        return True

    if normalized_line in {"masculino", "femenino"}:
        return True

    if DATE_LIKE_PATTERN.match(line.strip()) or TIME_LIKE_PATTERN.match(line.strip()):
        return True

    if "óptimo" in normalized_line or "deseable" in normalized_line or "limítrofe" in normalized_line:
        return True

    if "kdigo" in normalized_line or "cdc" in normalized_line or "aha:" in normalized_line:
        return True

    return False


def is_section_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or any(char.isdigit() for char in stripped):
        return False

    letters = [char for char in stripped if char.isalpha()]
    if not letters:
        return False

    uppercase_ratio = sum(char.isupper() for char in letters) / len(letters)
    return uppercase_ratio > 0.7 and len(stripped.split()) >= 2


def is_candidate_test_name(line: str) -> bool:
    if is_ignored_line(line):
        return False

    if parse_value(line) is not None:
        return False

    if parse_reference_range(line, None) is not None:
        return False

    if is_section_heading(line):
        return False

    if not any(char.isalpha() for char in line):
        return False

    return True


def clean_page_lines(page_lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in page_lines:
        if not line.strip():
            continue

        normalized_line = normalize_text(line)
        if normalized_line == "gracias por su preferencia.":
            break

        cleaned.append(line.strip())

    return cleaned


def build_observation(
    raw_name: str,
    raw_value: Any,
    value_type: str,
    reference_range_raw: str | None,
    reference_range: dict[str, Any] | None,
) -> dict[str, Any]:
    definition = find_lab_definition(raw_name)
    unit_ucum = None
    if reference_range and reference_range.get("unit_ucum"):
        unit_ucum = reference_range["unit_ucum"]
    elif definition:
        unit_ucum = definition.default_unit_ucum

    return {
        "test_name_raw": raw_name,
        "test_name_normalized": definition.canonical_name if definition else raw_name,
        "loinc_code": definition.loinc_code if definition else None,
        "value": raw_value,
        "value_type": value_type,
        "unit_raw": unit_ucum,
        "unit_ucum": unit_ucum,
        "reference_range_raw": reference_range_raw,
        "reference_range": reference_range,
        "interpretation": determine_interpretation(raw_value, reference_range),
        "mapping_confidence": 0.96 if definition else 0.7,
    }


def collect_table_observations(page_lines: list[str]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    index = 0

    while index < len(page_lines):
        if not is_candidate_test_name(page_lines[index]):
            index += 1
            continue

        current_definition = find_lab_definition(page_lines[index])
        if current_definition is None and not any(
            is_candidate_test_name(candidate) for candidate in page_lines[index + 1 : index + 3]
        ):
            index += 1
            continue

        names: list[str] = []
        lead_value = parse_value(page_lines[index - 1]) if index > 0 else None
        cursor = index

        while cursor < len(page_lines):
            line = page_lines[cursor]
            if line == "___":
                break
            if is_candidate_test_name(line):
                names.append(line)
            cursor += 1

        if not names:
            index += 1
            continue

        if cursor < len(page_lines) and page_lines[cursor] == "___":
            cursor += 1

        values: list[tuple[Any, str]] = []
        while cursor < len(page_lines):
            parsed_value = parse_value(page_lines[cursor])
            if parsed_value is None:
                break
            values.append(parsed_value)
            cursor += 1

        ranges: list[tuple[str, dict[str, Any]]] = []
        while cursor < len(page_lines):
            parsed_range = parse_reference_range(page_lines[cursor], None)
            if parsed_range is None:
                break
            ranges.append((page_lines[cursor], parsed_range))
            cursor += 1

        if lead_value is not None and len(values) + 1 >= len(names):
            values = [lead_value] + values

        if len(values) < len(names):
            index += 1
            continue

        for position, raw_name in enumerate(names):
            raw_value, value_type = values[position]
            reference_range_raw = ranges[position][0] if position < len(ranges) else None
            reference_range = ranges[position][1] if position < len(ranges) else None
            observations.append(
                build_observation(
                    raw_name=raw_name,
                    raw_value=raw_value,
                    value_type=value_type,
                    reference_range_raw=reference_range_raw,
                    reference_range=reference_range,
                )
            )

        index = cursor

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str | None]] = set()
    for item in observations:
        dedupe_key = (
            item["test_name_raw"],
            str(item["value"]),
            item["reference_range_raw"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(item)

    return deduped


def extract_observations(document_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    observations: list[dict[str, Any]] = []
    warnings: list[str] = []
    unmapped_items: list[str] = []

    for page in document_payload.get("pages", []):
        page_lines = clean_page_lines(page.get("lines", []))
        page_observations = collect_table_observations(page_lines)
        observations.extend(page_observations)

    deduped_observations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str | None]] = set()
    for item in observations:
        dedupe_key = (
            item["test_name_raw"],
            str(item["value"]),
            item["reference_range_raw"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_observations.append(item)
        if item["loinc_code"] is None:
            unmapped_items.append(item["test_name_raw"])

    if not deduped_observations:
        warnings.append("no laboratory observations were extracted from the document")

    return deduped_observations, warnings, sorted(set(unmapped_items))


def build_normalized_lab_result(document_payload: dict[str, Any]) -> dict[str, Any]:
    lines = document_payload.get("lines", [])
    patient = extract_patient(lines)
    observations, warnings, unmapped_items = extract_observations(document_payload)

    return {
        "document_id": document_payload["document_id"],
        "filename": document_payload["filename"],
        "document_type": "lab_report",
        "patient": patient,
        "observation_count": len(observations),
        "observations": observations,
        "unmapped_items": unmapped_items,
        "warnings": warnings,
        "source": {
            "page_count": document_payload["page_count"],
            "character_count": document_payload["character_count"],
            "content_type": document_payload["content_type"],
        },
    }
