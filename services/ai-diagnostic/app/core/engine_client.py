from __future__ import annotations

import json
import logging
import re

import httpx

from app.core.config import get_settings
from app.core.prompt import get_system_prompt, build_user_message
from app.core.schema import (
    AbnormalMarker,
    AutoimmuneFlag,
    DiagnosticRequest,
    DiagnosticResponse,
    LabAbnormalitySummary,
    LabResult,
    LabSnapshot,
    MarkerCorrelation,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# LOINC codes for specific autoimmune serologies
_APS_SEROLOGY_LOINC = {"32286-7", "20546-1", "30025-4", "30026-2"}  # aCL IgG/IgM, β2GPI
_ANA_LOINC = {"14082-5", "9638-5", "71946-0"}
_SSA_SSB_LOINC = {"26974-6", "27276-9", "27079-5"}  # anti-Ro/SSA, anti-La/SSB
_RF_LOINC = {"11572-5", "15183-0"}
_CCP_LOINC = {"32146-3", "32222-2"}

# Keywords in test names for serologies when LOINC is missing
_APS_KEYWORDS = {"anticl", "acl", "antifosfol", "antifosfo", "β2gpi", "b2gpi", "anticoagulante lupico", "lupus anticoagulant"}
_SSA_SSB_KEYWORDS = {"ssa", "ssb", "anti-ro", "anti-la", "ro/ssa", "la/ssb"}
_RF_KEYWORDS = {"factor reumatoide", "rheumatoid factor", "rf "}
_CCP_KEYWORDS = {"anti-ccp", "anti ccp", "citrulinated", "citrullinado"}


def _has_serology(lab_series: list[LabSnapshot], loinc_set: set[str], keyword_set: set[str]) -> bool:
    for snap in lab_series:
        for r in snap.results:
            if r.loinc_code and r.loinc_code in loinc_set:
                return True
            name_lower = r.test_name.lower()
            if any(kw in name_lower for kw in keyword_set):
                return True
    return False


def _has_positive_serology(lab_series: list[LabSnapshot], loinc_set: set[str], keyword_set: set[str]) -> bool:
    for snap in lab_series:
        for r in snap.results:
            matched = (r.loinc_code and r.loinc_code in loinc_set) or any(
                kw in r.test_name.lower() for kw in keyword_set
            )
            if matched and r.interpretation in ("high", "critical"):
                return True
    return False


def _condition_key(condition: str) -> str:
    return re.sub(r"[^a-z]", "", condition.lower())


def _validate_autoimmune_flags(
    flags: list[AutoimmuneFlag],
    payload: DiagnosticRequest,
) -> list[AutoimmuneFlag]:
    history = payload.history
    lab_series = payload.lab_series

    has_aps_serology = _has_serology(lab_series, _APS_SEROLOGY_LOINC, _APS_KEYWORDS)
    has_positive_aps = _has_positive_serology(lab_series, _APS_SEROLOGY_LOINC, _APS_KEYWORDS)
    has_thrombosis = any(
        "trombosis" in c.lower() or "thrombosis" in c.lower() or "embolia" in c.lower()
        or "stroke" in c.lower() or "tep" in c.lower() or "dvt" in c.lower()
        for c in history.comorbidities
    )
    has_pregnancy_loss = (history.miscarriages or 0) >= 3

    has_ssa_ssb = _has_positive_serology(lab_series, _SSA_SSB_LOINC, _SSA_SSB_KEYWORDS)
    has_sicca = any(
        kw in " ".join(history.comorbidities + [payload.clinical_diagnosis + (payload.doctor_observations or "")]).lower()
        for kw in ("sicca", "xerostomia", "xeroftalmia", "ojo seco", "boca seca", "dry eye", "dry mouth")
    )

    has_rf_or_ccp = _has_positive_serology(lab_series, _RF_LOINC | _CCP_LOINC, _RF_KEYWORDS | _CCP_KEYWORDS)

    validated: list[AutoimmuneFlag] = []
    for flag in flags:
        key = _condition_key(flag.condition)

        if "antifosfol" in key or "antiphospholipid" in key or "aps" == key:
            if has_positive_aps:
                validated.append(flag)
            elif has_aps_serology:
                validated.append(AutoimmuneFlag(
                    condition=flag.condition,
                    likelihood="low",
                    supporting_findings=flag.supporting_findings,
                    missing_workup=flag.missing_workup,
                ))
            elif has_thrombosis or has_pregnancy_loss:
                validated.append(AutoimmuneFlag(
                    condition=flag.condition,
                    likelihood="low",
                    supporting_findings=flag.supporting_findings,
                    missing_workup=flag.missing_workup or ["aCL IgG/IgM, anti-β2-glicoproteína I, anticoagulante lúpico"],
                ))
            else:
                logger.info(
                    "removed APS flag: no serology, no thrombosis history, no pregnancy loss",
                    extra={"request_id": payload.request_id},
                )

        elif "sjogren" in key or "sjögren" in key:
            if has_ssa_ssb or has_sicca:
                validated.append(flag)
            else:
                logger.info(
                    "removed Sjögren flag: no SSA/SSB serology and no sicca symptoms",
                    extra={"request_id": payload.request_id},
                )

        elif "artritis" in key or "rheumatoid" in key or "reumatoide" in key:
            if has_rf_or_ccp:
                validated.append(flag)
            else:
                logger.info(
                    "removed RA flag: no RF or anti-CCP",
                    extra={"request_id": payload.request_id},
                )

        else:
            validated.append(flag)

    return validated


# ── Lab abnormality analysis (deterministic, no LLM) ─────────────────────────

_CORRELATION_RULES: list[dict] = [
    {
        "pattern": "Anemia microcítica",
        "checks": [
            ({"hemoglobin", "hemoglobina", "hgb"}, "low"),
            ({"mcv", "vcm", "vol. corp", "corpuscular medio"}, "low"),
        ],
        "min_match": 2,
        "interp": (
            "Anemia con VCM reducido. Las causas más frecuentes son déficit de hierro, "
            "talasemia minor y anemia de enfermedad crónica severa. "
            "Solicitar hierro sérico, ferritina y saturación de transferrina."
        ),
    },
    {
        "pattern": "Anemia macrocítica",
        "checks": [
            ({"hemoglobin", "hemoglobina", "hgb"}, "low"),
            ({"mcv", "vcm", "vol. corp", "corpuscular medio"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Anemia con VCM elevado. Considerar déficit de vitamina B12 o folato, "
            "hipotiroidismo, hepatopatía o efecto de fármacos (metotrexato, hidroxicloroquina)."
        ),
    },
    {
        "pattern": "Pancitopenia",
        "checks": [
            ({"hemoglobin", "hemoglobina", "hgb"}, "low"),
            ({"leucocit", "leukocit", "wbc", "leucos"}, "low"),
            ({"plaqueta", "platelet", "trombocit"}, "low"),
        ],
        "min_match": 3,
        "interp": (
            "Tres series hematológicas disminuidas. El diferencial incluye hipoplasia medular, "
            "LES, infiltración medular, infecciones virales (VIH, EBV, CMV) y hiperesplenismo."
        ),
    },
    {
        "pattern": "Patrón inflamatorio sistémico",
        "checks": [
            ({"pcr", "crp", "proteína c reactiva", "c-reactive"}, "high"),
            ({"vsg", "esr", "eritrosediment", "velocidad de sedim"}, "high"),
            ({"ferritin"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Reactantes de fase aguda elevados. Indica inflamación sistémica activa: "
            "puede corresponder a infección bacteriana, enfermedad autoinmune en actividad, "
            "neoplasia o vasculitis."
        ),
    },
    {
        "pattern": "Síndrome metabólico",
        "checks": [
            ({"glucos", "glicemi", "glucose"}, "high"),
            ({"triglicérid", "triglycerid", "tg "}, "high"),
            ({"colesterol total", "total cholesterol"}, "high"),
            ({"hdl"}, "low"),
        ],
        "min_match": 3,
        "interp": (
            "Tres o más componentes del síndrome metabólico presentes. "
            "Se asocia a riesgo cardiovascular elevado, resistencia a la insulina "
            "y progresión a diabetes tipo 2."
        ),
    },
    {
        "pattern": "Dislipidemia mixta",
        "checks": [
            ({"triglicérid", "triglycerid", "tg "}, "high"),
            ({"ldl"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Elevación concurrente de triglicéridos y LDL. Hiperlipidemia mixta (tipo IIb). "
            "Aumenta el riesgo coronario. Descartar causas secundarias: hipotiroidismo, "
            "síndrome nefrótico, diabetes."
        ),
    },
    {
        "pattern": "Riesgo cardiovascular elevado",
        "checks": [
            ({"ldl"}, "high"),
            ({"colesterol total", "total cholesterol"}, "high"),
            ({"triglicérid", "triglycerid", "tg "}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Múltiples lípidos aterogénicos elevados. Calcular score de riesgo a 10 años "
            "(Framingham / PCE). Establecer meta de LDL según categoría de riesgo cardiovascular."
        ),
    },
    {
        "pattern": "Daño hepatocelular",
        "checks": [
            ({"alt", "tgp", "alanin", "alanina transaminasa"}, "high"),
            ({"ast", "tgo", "aspartato", "aspartat"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Elevación de transaminasas con patrón hepatocelular. Considerar hepatitis viral, "
            "HGNA/EHNA, daño por fármacos o toxinas, o hepatitis autoinmune."
        ),
    },
    {
        "pattern": "Patrón colestásico",
        "checks": [
            ({"ggt", "gamma-gt", "gammaglutamil"}, "high"),
            ({"fosfatasa alcalina", "alkaline phosph", "alp", "fal "}, "high"),
            ({"bilirrub", "bilirubin"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Elevación de GGT y/o fosfatasa alcalina con posible hiperbilirrubinemia. "
            "Patrón colestásico: descartar obstrucción biliar, colangitis biliar primaria "
            "o colestasis intrahepática."
        ),
    },
    {
        "pattern": "Hepatopatía avanzada",
        "checks": [
            ({"albumin", "albúmin"}, "low"),
            ({"plaqueta", "platelet", "trombocit"}, "low"),
            ({"bilirrub", "bilirubin"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Hipoalbuminemia, trombocitopenia e hiperbilirrubinemia concurrentes. "
            "Sugestivo de hepatopatía crónica avanzada con insuficiencia hepatocelular "
            "e hipertensión portal (cirrosis)."
        ),
    },
    {
        "pattern": "Disfunción renal",
        "checks": [
            ({"creatinin"}, "high"),
            ({"bun", "urea", "nitrógeno ureico", "nitrogeno ureico"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Creatinina y BUN/urea elevados. Calcular eGFR para estadificar ERC. "
            "Descartar causas prerrenales (hipovolemia), intrínsecas (glomerulonefritis, NTA) "
            "y posrenales."
        ),
    },
    {
        "pattern": "Citopenia inmunomediada",
        "checks": [
            ({"plaqueta", "platelet", "trombocit"}, "low"),
            ({"leucocit", "leukocit", "wbc", "leucos"}, "low"),
            ({"linfocit", "lymphocyt"}, "low"),
        ],
        "min_match": 2,
        "interp": (
            "Trombocitopenia y/o leucopenia/linfopenia concurrentes. "
            "Patrón sugestivo de citopenia inmunomediada: evaluar LES (ANA, anti-dsDNA, "
            "complemento), fármacos y causas virales (VIH, EBV)."
        ),
    },
    {
        "pattern": "Consumo de complemento",
        "checks": [
            ({"c3", "complemento c3", "complement c3"}, "low"),
            ({"c4", "complemento c4", "complement c4"}, "low"),
        ],
        "min_match": 1,
        "interp": (
            "Complemento sérico reducido (C3 y/o C4). Indica consumo por complejos inmunes: "
            "patrón característico de LES activo. También presente en crioglobulinemia "
            "y endocarditis bacteriana subaguda."
        ),
    },
    {
        "pattern": "Patrón miopático",
        "checks": [
            ({"ck ", " ck", "creatincinasa", "creatinfosfoquinasa", "cpk", "creatine kinase"}, "high"),
            ({"ldh", "lactato deshidrogenas", "lactic dehydrogen"}, "high"),
            ({"ast", "tgo", "aspartato"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "CK elevada con LDH y/o AST aumentados. Patrón de daño muscular: considerar "
            "miopatía inflamatoria (polimiositis, dermatomiositis), rabdomiólisis "
            "o miopatía por fármacos (estatinas)."
        ),
    },
    {
        "pattern": "Alteración tiroidea",
        "checks": [
            ({"tsh", "hormona estimulante tiroid", "thyroid stimulat"}, None),
            ({"t4 libre", "t4l", "ft4", "tiroxina libre", "free t4"}, None),
        ],
        "min_match": 2,
        "interp": (
            "TSH y T4 libre simultáneamente alterados. "
            "TSH↑ + T4↓ = hipotiroidismo primario. TSH↓ + T4↑ = hipertiroidismo. "
            "Correlacionar con anti-TPO y anti-TG para determinar etiología autoinmune."
        ),
    },
    {
        "pattern": "Hiperuricemia con riesgo metabólico",
        "checks": [
            ({"ácido úrico", "acido urico", "uric acid", "urato"}, "high"),
            ({"triglicérid", "triglycerid", "tg "}, "high"),
            ({"glucos", "glicemi", "glucose"}, "high"),
        ],
        "min_match": 2,
        "interp": (
            "Hiperuricemia asociada a alteraciones metabólicas. Este cluster se asocia a "
            "resistencia a la insulina y síndrome metabólico, y aumenta el riesgo de "
            "gota y enfermedad cardiovascular."
        ),
    },
]


def _is_abnormal(r: LabResult) -> tuple[bool, str]:
    if r.interpretation == "critical":
        return True, "critical"
    if r.interpretation in ("high", "low"):
        return True, r.interpretation
    if r.interpretation == "normal":
        return False, ""
    # interpretation is None — infer from numeric ref range
    if isinstance(r.value, (int, float)):
        val = float(r.value)
        if r.ref_high is not None and val > r.ref_high:
            return True, "high"
        if r.ref_low is not None and val < r.ref_low:
            return True, "low"
    return False, ""


def _kw_match(test_name: str, keywords: set[str]) -> bool:
    name = test_name.lower()
    return any(kw in name for kw in keywords)


def _compute_correlations(abnormals: list[AbnormalMarker]) -> list[MarkerCorrelation]:
    results: list[MarkerCorrelation] = []
    for rule in _CORRELATION_RULES:
        matched_names: list[str] = []
        for (keywords, direction) in rule["checks"]:
            for m in abnormals:
                if _kw_match(m.test_name, keywords):
                    if direction is None or m.direction == direction:
                        matched_names.append(m.test_name)
                        break  # one match per check criterion is enough
        if len(matched_names) >= rule["min_match"]:
            results.append(MarkerCorrelation(
                pattern=rule["pattern"],
                markers_involved=matched_names,
                interpretation=rule["interp"],
            ))
    return results


def compute_lab_abnormalities(payload: DiagnosticRequest) -> LabAbnormalitySummary:
    abnormals: list[AbnormalMarker] = []
    for snap in payload.lab_series:
        for r in snap.results:
            is_abn, direction = _is_abnormal(r)
            if is_abn:
                abnormals.append(AbnormalMarker(
                    test_name=r.test_name,
                    loinc_code=r.loinc_code,
                    value=r.value,
                    unit=r.unit,
                    ref_low=r.ref_low,
                    ref_high=r.ref_high,
                    direction=direction,
                    report_date=snap.report_date,
                ))

    abnormals.sort(key=lambda m: (m.report_date, m.test_name))

    # Use the latest value per test for correlation matching
    latest: dict[str, AbnormalMarker] = {}
    for m in abnormals:
        latest[m.test_name.lower().strip()] = m

    correlations = _compute_correlations(list(latest.values()))

    return LabAbnormalitySummary(
        abnormal_count=len(abnormals),
        abnormal_markers=abnormals,
        correlations=correlations,
    )


# ── RAG context ────────────────────────────────────────────────────────────────

def _fetch_rag_context(payload: DiagnosticRequest) -> str:
    s = get_settings()
    if not s.clinical_rag_enabled or not s.clinical_rag_url:
        return ""

    all_results = [r for snap in payload.lab_series for r in snap.results]
    if not all_results:
        return ""

    rag_payload = {
        "patient": {
            "age": payload.patient.age,
            "sex": payload.patient.sex,
            "ethnicity": payload.patient.ethnicity,
        },
        "lab_results": [r.model_dump() for r in all_results],
        "top_k": s.clinical_rag_top_k,
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{s.clinical_rag_url}/cases/similar", json=rag_payload)
            resp.raise_for_status()

        data = resp.json()
        cases = data.get("cases", [])
        total = data.get("total_cases_in_store", 0)

        if not cases or total == 0:
            return ""

        lines = ["REFERENCE CASES FROM VALIDATED DATABASE (use as clinical context):"]
        for c in cases:
            line = f"  - {c['patient_summary']} | similarity {c['similarity']} | Diagnosis: {c['validated_diagnosis']}"
            if c.get("differential"):
                line += f" | Differential: {', '.join(c['differential'][:3])}"
            if c.get("doctor_notes"):
                line += f" | Notes: {c['doctor_notes']}"
            lines.append(line)

        logger.info(
            "RAG retrieved %d similar cases (total in store: %d)",
            len(cases), total,
            extra={"request_id": payload.request_id},
        )
        return "\n".join(lines)

    except Exception as exc:
        logger.warning(
            "RAG retrieval failed, continuing without context: %s", exc,
            extra={"request_id": payload.request_id},
        )
        return ""


def run_diagnostic_inference(payload: DiagnosticRequest) -> DiagnosticResponse:
    rag_context = _fetch_rag_context(payload)
    user_message = build_user_message(payload, rag_context=rag_context)
    system_prompt = get_system_prompt(payload.language, payload.focus)

    body = {
        "model": settings.vllm_reasoning_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
    }

    logger.info("sending diagnostic inference request", extra={"request_id": payload.request_id})

    with httpx.Client(timeout=settings.vllm_timeout_seconds) as client:
        resp = client.post(f"{settings.vllm_reasoning_url}/v1/chat/completions", json=body)
        resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"]
    logger.debug("raw model output", extra={"output_preview": raw[:500]})

    result = _parse_response(raw, payload.request_id)
    result.autoimmune_flags = _validate_autoimmune_flags(result.autoimmune_flags, payload)
    result.lab_abnormalities = compute_lab_abnormalities(payload)

    validated_conditions = {_condition_key(f.condition) for f in result.autoimmune_flags}
    result.differential = [
        d for d in result.differential
        if not any(
            _condition_key(d).startswith(vc[:6]) for vc in validated_conditions
        ) or _condition_key(d) in validated_conditions
    ]

    return result


def _parse_response(text: str, request_id: str | None) -> DiagnosticResponse:
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in model output")
    obj, _ = json.JSONDecoder().raw_decode(text, start)
    obj["request_id"] = request_id
    return DiagnosticResponse(**obj)
