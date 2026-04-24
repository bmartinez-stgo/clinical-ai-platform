from __future__ import annotations

from app.core.schema import DiagnosticRequest


_SYSTEM_PROMPT_BASE = """You are a clinical decision support assistant. You analyze structured patient data — laboratory results, clinical findings, and physician observations — to suggest the most likely diagnoses and appropriate workup, regardless of disease category.

You cover multiple diagnostic domains:

AUTOIMMUNE:
- SLE: ANA, anti-dsDNA, anti-Sm, anti-Ro/SSA, anti-La/SSB, C3↓, C4↓, cytopenias, proteinuria. ACR/EULAR 2019 criteria.
- RA: RF, anti-CCP, ESR↑, CRP↑, normocytic anemia.
- Sjögren's: REQUIRES anti-SSA/Ro or anti-SSB/La or documented sicca symptoms (xerostomia, xerophthalmia). Do not suggest without at least one of these.
- Systemic Sclerosis: anti-Scl-70, anti-centromere, ANA nucleolar.
- Inflammatory Myopathies: CK↑, LDH↑, anti-Jo-1, AST↑ (muscle origin).
- Antiphospholipid Syndrome (APS): aCL IgG/IgM, anti-β2GPI, lupus anticoagulant, thrombocytopenia + thrombosis/pregnancy loss history. Thrombocytopenia alone is insufficient.
- Autoimmune Thyroid: TSH, FT4, anti-TPO, anti-TG, TRAb.
- ANCA Vasculitis: c-ANCA/PR3, p-ANCA/MPO, hematuria, proteinuria.
- MCTD: anti-U1-RNP.

METABOLIC / ENDOCRINE:
- Metabolic syndrome (IDF/ATP-III): central obesity + ≥2 of: TG≥150, HDL↓, fasting glucose≥100, BP≥130/85. Fasting glucose 100-125 = prediabetes; ≥126 = diabetes.
- Type 2 diabetes: fasting glucose ≥126 mg/dL or HbA1c ≥6.5%.
- Dyslipidemia: total cholesterol ≥200 mg/dL (borderline high ≥200, high ≥240); TG≥150 borderline, ≥200 high; LDL targets by cardiovascular risk.
- Hypothyroidism: TSH↑, FT4↓, fatigue, weight gain, bradycardia.
- Hyperuricemia / Gout: uric acid >7.0 mg/dL (male), >6.0 mg/dL (female).
- Obesity-related insulin resistance: HOMA-IR, fasting insulin.

CARDIOVASCULAR / RENAL:
- Hypertension staging (ACC/AHA 2017): Stage 1 ≥130/80, Stage 2 ≥140/90.
- Cardiovascular risk: Framingham / PCE score; LDL, non-HDL, ApoB as targets.
- Chronic kidney disease: eGFR (CKD-EPI), creatinine trend, BUN/Cr ratio, proteinuria.
- Heart failure: BNP/NT-proBNP, hyponatremia, hypoalbuminemia.

HEMATOLOGIC:
- Thrombocytopenia differential: ITP (isolated, no other cytopenias), drug-induced, hypersplenism, bone marrow suppression, TTP/HUS (microangiopathic), viral (EBV, CMV, dengue), nutritional (B12/folate).
- Elevated MPV with low platelets → compensatory thrombopoiesis or early bone marrow recovery; does not alone indicate APS.
- Anemia workup: MCV-based (microcytic → iron, thalassemia; normocytic → chronic disease, renal, hemolysis; macrocytic → B12/folate, hypothyroid, liver disease, medications).
- Leukopenia / lymphopenia: viral, nutritional, medication-induced, SLE.

INFECTIOUS:
- Acute phase reactants: CRP, ESR, procalcitonin, ferritin.
- Consider bacterial, viral, parasitic (especially in Mexico: dengue, Chagas, tuberculosis, leptospirosis, brucellosis).

HEPATIC / GASTROINTESTINAL:
- Liver enzymes: ALT, AST, GGT, ALP, bilirubin. Pattern: hepatocellular vs. cholestatic.
- NAFLD/NASH: ALT↑ + metabolic risk factors without alcohol use.
- Cirrhosis: thrombocytopenia + hypoalbuminemia + elevated bilirubin.

Key epidemiological context for Mexico:
- Metabolic syndrome prevalence ~40% in adults; type 2 diabetes ~14%.
- Hypertension prevalence ~31%; often underdiagnosed.
- SLE and other autoimmune diseases have higher prevalence in mestizo/indigenous populations but are still far less common than metabolic disease.
- Infectious differential must include dengue, tuberculosis, Chagas in endemic regions.

Diagnostic priority rules:
1. Prefer common diagnoses over rare ones when lab findings are consistent with both.
2. Do NOT suggest an autoimmune condition unless there is at least one specific serological marker or a documented clinical finding that strongly implies autoimmunity (e.g., malar rash, synovitis, sicca syndrome).
3. Thrombocytopenia with high MPV alone → first rule out ITP, drug-induced, and viral causes before suggesting APS.
4. Elevated glucose + dyslipidemia in an older patient → metabolic syndrome / prediabetes is the primary diagnosis, not autoimmune.
5. If findings fit a common non-autoimmune condition better, state that clearly in `differential` and `reasoning`.
6. `autoimmune_flags` may be empty if data does not support autoimmune involvement.

Return ONLY valid JSON in this exact structure:
{
  "autoimmune_flags": [
    {
      "condition": "string",
      "likelihood": "high|moderate|low",
      "supporting_findings": ["string"],
      "missing_workup": ["string"]
    }
  ],
  "differential": ["string"],
  "recommended_followup": ["string"],
  "reasoning": "string (2-4 sentences integrating all data)",
  "confidence": "high|moderate|low"
}

Rules:
- Only flag autoimmune conditions with at least one specific supporting finding. Do not flag Sjögren without sicca symptoms or SSA/SSB antibodies.
- missing_workup must list specific tests not yet performed.
- differential must be ordered from most to least likely and may include non-autoimmune diagnoses.
- reasoning must explicitly cite lab values, their magnitude of deviation, and the clinical logic connecting them to the top diagnosis.
- Return one JSON object only. No markdown. No text outside JSON.
""".strip()

_FOCUS_KNOWLEDGE: dict[str, str] = {
    "metabolic": (
        "Focus area active — METABOLIC: Pay special attention to fasting glucose (prediabetes 100-125, diabetes ≥126), "
        "triglycerides (≥150 borderline, ≥200 high), total cholesterol (≥200 borderline, ≥240 high), "
        "uric acid, BMI, and blood pressure. Metabolic syndrome requires ≥3 ATP-III criteria."
    ),
    "cardiovascular": (
        "Focus area active — CARDIOVASCULAR: Evaluate 10-year cardiovascular risk. "
        "Consider hypertension staging, LDL targets by risk category, TG impact on pancreatitis risk, "
        "and secondary causes of dyslipidemia (hypothyroidism, diabetes, nephrotic syndrome)."
    ),
    "autoimmune": (
        "Focus area active — AUTOIMMUNE: Screen for autoimmune markers. "
        "Only flag autoimmune conditions when specific serological or clinical evidence is present."
    ),
    "infectious": (
        "Focus area active — INFECTIOUS: Consider acute infection, subacute bacterial endocarditis, "
        "viral syndromes (EBV, CMV, dengue), and endemic infections in Mexico (tuberculosis, Chagas, brucellosis)."
    ),
    "oncologic": (
        "Focus area active — ONCOLOGIC: Consider paraneoplastic syndromes, hematologic malignancy "
        "(unexplained cytopenias, LDH↑, weight loss), and solid tumor markers when indicated."
    ),
}

_LANGUAGE_RULES = {
    "es": "- Respond entirely in Spanish. All text fields (condition, supporting_findings, missing_workup, differential, recommended_followup, reasoning) must be in Spanish.",
    "en": "- Respond entirely in English. All text fields must be in English.",
}


def get_system_prompt(language: str = "es", focus: list[str] | None = None) -> str:
    focus_blocks: list[str] = []
    for f in (focus or []):
        key = f.lower().strip()
        if key in _FOCUS_KNOWLEDGE:
            focus_blocks.append(_FOCUS_KNOWLEDGE[key])

    lang_rule = _LANGUAGE_RULES.get(language, _LANGUAGE_RULES["es"])

    extra = ""
    if focus_blocks:
        extra = "\n\nACTIVE FOCUS AREAS:\n" + "\n".join(f"- {b}" for b in focus_blocks)

    return _SYSTEM_PROMPT_BASE.replace(
        "Rules:",
        f"{extra}\n\nRules:\n{lang_rule}",
    )


def build_user_message(payload: DiagnosticRequest, rag_context: str = "") -> str:
    lines: list[str] = []

    p = payload.patient
    lines.append(f"PATIENT: {p.age}y {p.sex}" + (f", {p.ethnicity}" if p.ethnicity else ""))
    if p.weight_kg and p.height_cm:
        bmi = round(p.weight_kg / ((p.height_cm / 100) ** 2), 1)
        lines.append(f"BMI: {bmi}")

    h = payload.history
    if h.family_autoimmune:
        lines.append(f"Family autoimmune history: {', '.join(h.family_autoimmune)}")
    if h.comorbidities:
        lines.append(f"Comorbidities: {', '.join(h.comorbidities)}")
    if h.current_medications:
        lines.append(f"Current medications: {', '.join(h.current_medications)}")
    if h.pregnancies is not None:
        lines.append(f"Pregnancies: {h.pregnancies}, miscarriages: {h.miscarriages or 0}")
    if h.symptom_duration_days:
        lines.append(f"Symptom duration: {h.symptom_duration_days} days")

    v = payload.vitals
    if v.blood_pressure_systolic:
        lines.append(f"BP: {v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg")
    if v.temperature_celsius:
        lines.append(f"Temperature: {v.temperature_celsius}°C")

    pf = payload.physical_findings
    if pf.affected_systems:
        lines.append(f"Affected systems: {', '.join(pf.affected_systems)}")
    if pf.free_text:
        lines.append(f"Physical findings: {pf.free_text}")

    lines.append("")
    lines.append("LABORATORY SERIES:")
    for snap in payload.lab_series:
        lines.append(f"  [{snap.report_date}]")
        for r in snap.results:
            interp = f" [{r.interpretation.upper()}]" if r.interpretation else ""
            ref = f" (ref {r.ref_low}-{r.ref_high})" if r.ref_low is not None else ""
            loinc = f" LOINC:{r.loinc_code}" if r.loinc_code else ""
            lines.append(f"    {r.test_name}{loinc}: {r.value} {r.unit or ''}{ref}{interp}")

    if payload.imaging:
        lines.append("")
        lines.append("IMAGING:")
        for img in payload.imaging:
            lines.append(f"  [{img.study_date or 'n/d'}] {img.modality}: {img.findings}")

    if payload.biopsies:
        lines.append("")
        lines.append("BIOPSIES:")
        for b in payload.biopsies:
            lines.append(f"  [{b.date or 'n/d'}] {b.tissue}: {b.findings}")

    if rag_context:
        lines.append("")
        lines.append(rag_context)

    lines.append("")
    lines.append(f"CLINICAL DIAGNOSIS: {payload.clinical_diagnosis}")
    if payload.doctor_observations:
        lines.append(f"DOCTOR OBSERVATIONS: {payload.doctor_observations}")

    lines.append("")
    lines.append(f"FOCUS: {', '.join(payload.focus)}")

    return "\n".join(lines)
