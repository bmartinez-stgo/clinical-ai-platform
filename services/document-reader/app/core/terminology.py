from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabDefinition:
    canonical_name: str
    loinc_code: str | None
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
    LabDefinition(
        canonical_name="Cholesterol",
        loinc_code="2093-3",
        aliases=("colesterol", "cholesterol"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="HDL Cholesterol",
        loinc_code="2085-9",
        aliases=("colesterol hdl", "hdl cholesterol"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="LDL Cholesterol",
        loinc_code="18262-6",
        aliases=("colesterol ldl directo", "ldl cholesterol direct", "ldl directo"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Triglyceride",
        loinc_code="2571-8",
        aliases=("trigliceridos", "triglycerides"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Non-HDL Cholesterol",
        loinc_code="43396-1",
        aliases=("colesterol no-hdl", "non-hdl cholesterol"),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Atherogenic index",
        loinc_code=None,
        aliases=("indice aterogenico",),
        default_unit_ucum=None,
    ),
    LabDefinition(
        canonical_name="LDL/HDL Ratio",
        loinc_code=None,
        aliases=("relacion ldl/hdl",),
        default_unit_ucum=None,
    ),
    LabDefinition(
        canonical_name="Small dense LDL",
        loinc_code=None,
        aliases=("sd ldl",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="VLDL Cholesterol",
        loinc_code="13458-5",
        aliases=("vldl colesterol",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Total lipids",
        loinc_code=None,
        aliases=("lipidos totales",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Serum phospholipids",
        loinc_code=None,
        aliases=("fosfolipidos en suero",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="High sensitivity C reactive protein",
        loinc_code="30522-7",
        aliases=("proteina c reactiva ultrasensible",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Total bilirubin",
        loinc_code="1975-2",
        aliases=("bilirrubina total",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Direct bilirubin",
        loinc_code="1968-7",
        aliases=("bilirrubina directa",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Indirect bilirubin",
        loinc_code="1971-1",
        aliases=("bilirrubina indirecta",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Aspartate aminotransferase",
        loinc_code="1920-8",
        aliases=("ast (tgo)", "ast"),
        default_unit_ucum="U/L",
    ),
    LabDefinition(
        canonical_name="Alanine aminotransferase",
        loinc_code="1742-6",
        aliases=("alt (tgp)", "alt"),
        default_unit_ucum="U/L",
    ),
    LabDefinition(
        canonical_name="AST/ALT Ratio",
        loinc_code=None,
        aliases=("relacion: ast/alt", "ast/alt"),
        default_unit_ucum=None,
    ),
    LabDefinition(
        canonical_name="Gamma glutamyl transferase",
        loinc_code="2324-2",
        aliases=("gama glutamil transpeptidasa",),
        default_unit_ucum="U/L",
    ),
    LabDefinition(
        canonical_name="Total protein",
        loinc_code="2885-2",
        aliases=("proteinas totales",),
        default_unit_ucum="g/dL",
    ),
    LabDefinition(
        canonical_name="Albumin",
        loinc_code="1751-7",
        aliases=("albumina",),
        default_unit_ucum="g/dL",
    ),
    LabDefinition(
        canonical_name="Globulin",
        loinc_code="10834-0",
        aliases=("globulinas",),
        default_unit_ucum="g/dL",
    ),
    LabDefinition(
        canonical_name="Albumin/Globulin Ratio",
        loinc_code=None,
        aliases=("relacion a/g",),
        default_unit_ucum=None,
    ),
    LabDefinition(
        canonical_name="Alkaline phosphatase",
        loinc_code="6768-6",
        aliases=("f. alcalina total", "fosfatasa alcalina total"),
        default_unit_ucum="U/L",
    ),
    LabDefinition(
        canonical_name="Lactate dehydrogenase",
        loinc_code="14804-9",
        aliases=("ldh",),
        default_unit_ucum="U/L",
    ),
    LabDefinition(
        canonical_name="Iron",
        loinc_code="2498-4",
        aliases=("hierro",),
        default_unit_ucum="ug/dL",
    ),
    LabDefinition(
        canonical_name="Unsaturated iron binding capacity",
        loinc_code="2501-6",
        aliases=("uibc",),
        default_unit_ucum="ug/dL",
    ),
    LabDefinition(
        canonical_name="Total iron binding capacity",
        loinc_code="2500-8",
        aliases=("captacion de hierro",),
        default_unit_ucum="ug/dL",
    ),
    LabDefinition(
        canonical_name="Iron saturation",
        loinc_code="2502-4",
        aliases=("porcentaje de saturacion de hierro",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Immunoglobulin G",
        loinc_code="2465-3",
        aliases=("inmunoglobulina g",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Immunoglobulin A",
        loinc_code="2458-8",
        aliases=("inmunoglobulina a",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Immunoglobulin M",
        loinc_code="2472-9",
        aliases=("inmunoglobulina m",),
        default_unit_ucum="mg/dL",
    ),
    LabDefinition(
        canonical_name="Leukocytes",
        loinc_code="6690-2",
        aliases=("leucocitos",),
    ),
    LabDefinition(
        canonical_name="Erythrocytes",
        loinc_code="789-8",
        aliases=("eritrocitos",),
    ),
    LabDefinition(
        canonical_name="Hemoglobin",
        loinc_code="718-7",
        aliases=("hemoglobina",),
        default_unit_ucum="g/dL",
    ),
    LabDefinition(
        canonical_name="Hematocrit",
        loinc_code="4544-3",
        aliases=("hematocrito",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Mean corpuscular volume",
        loinc_code="787-2",
        aliases=("volumen corpuscular medio", "volumen corp. medio", "vcm"),
        default_unit_ucum="fL",
    ),
    LabDefinition(
        canonical_name="Mean corpuscular hemoglobin",
        loinc_code="785-6",
        aliases=("hemoglobina corpuscular media", "hemoglobina corp. media", "hcm"),
        default_unit_ucum="pg",
    ),
    LabDefinition(
        canonical_name="Mean corpuscular hemoglobin concentration",
        loinc_code="786-4",
        aliases=("conc. de hb corpuscular media", "conc. media de hemoglobina corp.", "chcm", "chorr"),
        default_unit_ucum="g/dL",
    ),
    LabDefinition(
        canonical_name="Erythrocyte distribution width CV",
        loinc_code="788-0",
        aliases=("ancho de distrib. de eritrocitos (cv)",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Erythrocyte distribution width SD",
        loinc_code=None,
        aliases=("ancho de distrib. de eritrocitos (sd)",),
        default_unit_ucum="fL",
    ),
    LabDefinition(
        canonical_name="Platelets",
        loinc_code="777-3",
        aliases=("plaquetas", "plequetas"),
    ),
    LabDefinition(
        canonical_name="Mean platelet volume",
        loinc_code="32623-1",
        aliases=("volumen plaquetario medio",),
        default_unit_ucum="fL",
    ),
    LabDefinition(
        canonical_name="Neutrophils Percent",
        loinc_code="770-8",
        aliases=("neutrofilos", "segmentados"),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Band neutrophils Percent",
        loinc_code="26507-4",
        aliases=("bandas",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Metamyelocytes Percent",
        loinc_code="28541-1",
        aliases=("metamielocitos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Myelocytes Percent",
        loinc_code="26498-6",
        aliases=("mielocitos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Lymphocytes Percent",
        loinc_code="736-9",
        aliases=("linfocitos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Monocytes Percent",
        loinc_code="5905-5",
        aliases=("monocitos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Eosinophils Percent",
        loinc_code="713-8",
        aliases=("eosinofilos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Basophils Percent",
        loinc_code="706-2",
        aliases=("basofilos",),
        default_unit_ucum="%",
    ),
    LabDefinition(
        canonical_name="Urine color",
        loinc_code="5778-6",
        aliases=("color",),
    ),
    LabDefinition(
        canonical_name="Urine appearance",
        loinc_code="5767-9",
        aliases=("aspecto",),
    ),
    LabDefinition(
        canonical_name="Urine specific gravity",
        loinc_code="5811-5",
        aliases=("densidad",),
    ),
    LabDefinition(
        canonical_name="Urine pH",
        loinc_code="5803-2",
        aliases=("ph",),
    ),
    LabDefinition(
        canonical_name="Urine leukocyte esterase",
        loinc_code="5799-2",
        aliases=("esterasa leucocitaria",),
    ),
    LabDefinition(
        canonical_name="Urine nitrite",
        loinc_code="5802-4",
        aliases=("nitritos",),
    ),
    LabDefinition(
        canonical_name="Urine protein",
        loinc_code="20454-5",
        aliases=("proteinas",),
    ),
    LabDefinition(
        canonical_name="Urine glucose",
        loinc_code="53328-1",
        aliases=("glucosa",),
    ),
    LabDefinition(
        canonical_name="Urine ketones",
        loinc_code="57734-6",
        aliases=("cetonas",),
    ),
    LabDefinition(
        canonical_name="Urine bilirubin",
        loinc_code="5770-3",
        aliases=("bilirrubina",),
    ),
    LabDefinition(
        canonical_name="Urine urobilinogen",
        loinc_code="5818-0",
        aliases=("urobilinogeno",),
    ),
    LabDefinition(
        canonical_name="Urine hemoglobin",
        loinc_code="5794-3",
        aliases=("hemoglobina",),
    ),
)


UNIT_NORMALIZATION = {
    "mg/dl": "mg/dL",
    "mg / dl": "mg/dL",
    "mgdl": "mg/dL",
    "meq/l": "meq/L",
    "meq / l": "meq/L",
    "u/l": "U/L",
    "g/dl": "g/dL",
    "ug/dl": "ug/dL",
    "µg/dl": "ug/dL",
    "pg": "pg",
    "fl": "fL",
    "%": "%",
    "ml/min/1.73m2": "mL/min/{1.73_m2}",
    "ml/min/1.73 m2": "mL/min/{1.73_m2}",
    "ml/min/1.73m^2": "mL/min/{1.73_m2}",
    "ml/min/1.73 m^2": "mL/min/{1.73_m2}",
}
