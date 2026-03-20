from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabDefinition:
    canonical_name: str
    loinc_code: str
    aliases: tuple[str, ...]
    default_unit_ucum: str | None = None


LAB_DEFINITIONS: tuple[LabDefinition, ...] = (
    LabDefinition(
        canonical_name="Glucose",
        loinc_code="2345-7",
        aliases=("glucosa", "glucose"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Urea nitrogen",
        loinc_code="3094-0",
        aliases=("nitrogeno de urea en sangre", "bun", "blood urea nitrogen"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Urea",
        loinc_code="3094-0",
        aliases=("urea",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Creatinine",
        loinc_code="2160-0",
        aliases=("creatinina", "creatinine"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Urea nitrogen/Creatinine",
        loinc_code="3097-3",
        aliases=("relacion bun/creat", "razon bun/creatinina"),
        default_unit_ucum=None,
    ),
    LabDefinition(
        canonical_name="Urate",
        loinc_code="3084-1",
        aliases=("acido urico", "uric acid"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Phosphate",
        loinc_code="2777-1",
        aliases=("fosforo", "phosphorus"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Calcium",
        loinc_code="17861-6",
        aliases=("calcio", "calcium"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Magnesium",
        loinc_code="19123-9",
        aliases=("magnesio", "magnesium"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Sodium",
        loinc_code="2951-2",
        aliases=("sodio", "sodium"),
        default_unit_ucum="meq/L",
    ),
    LabDefinition(
        canonical_name="Potassium",
        loinc_code="2823-3",
        aliases=("potasio", "potassium"),
        default_unit_ucum="meq/L",
    ),
    LabDefinition(
        canonical_name="Chloride",
        loinc_code="2075-0",
        aliases=("cloro", "chloride"),
        default_unit_ucum="meq/L",
    ),
    LabDefinition(
        canonical_name="Estimated glomerular filtration rate",
        loinc_code="98979-8",
        aliases=(
            "tasa de filtracion glomerular estimada",
            "tfge",
            "egfr",
        ),
        default_unit_ucum="mL/min/{1.73_m2}",
    ),
)


UNIT_NORMALIZATION = {
    "mg/dl": "mg/dL",
    "mg / dl": "mg/dL",
    "mgdl": "mg/dL",
    "meq/l": "meq/L",
    "meq / l": "meq/L",
    "ml/min/1.73m2": "mL/min/{1.73_m2}",
    "ml/min/1.73 m2": "mL/min/{1.73_m2}",
    "ml/min/1.73m^2": "mL/min/{1.73_m2}",
    "ml/min/1.73 m^2": "mL/min/{1.73_m2}",
}
