from __future__ import annotations

import json
import logging
import re

import httpx

from app.core.config import get_settings
from app.core.prompt import get_system_prompt, build_user_message
from app.core.schema import AutoimmuneFlag, DiagnosticRequest, DiagnosticResponse, LabSnapshot

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
    """
    Remove or downgrade autoimmune flags that the model hallucinated without
    sufficient evidence. Small LLMs often suggest conditions by keyword
    association rather than by actual diagnostic criteria.
    """
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
                # Tests ordered but not positive — keep as low
                validated.append(AutoimmuneFlag(
                    condition=flag.condition,
                    likelihood="low",
                    supporting_findings=flag.supporting_findings,
                    missing_workup=flag.missing_workup,
                ))
            elif has_thrombosis or has_pregnancy_loss:
                # Clinical history supports it, flag as low, workup needed
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
                # Don't add — not enough evidence

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
            # Keep other flags (SLE, vasculitis, myositis, etc.) — harder to validate without more context
            validated.append(flag)

    return validated


def run_diagnostic_inference(payload: DiagnosticRequest) -> DiagnosticResponse:
    user_message = build_user_message(payload)
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

    # Remove validated-out conditions from the differential too
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
