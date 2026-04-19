from __future__ import annotations

import json
from app.core.schema import DiagnosticRequest


SYSTEM_PROMPT = """You are a clinical decision support assistant specialized in autoimmune diseases.
You analyze structured patient data including laboratory results, clinical findings, and physician observations to assist in identifying autoimmune conditions.

You have deep knowledge of:
- Systemic Lupus Erythematosus (SLE): ANA, anti-dsDNA, anti-Sm, anti-Ro/SSA, anti-La/SSB, C3↓, C4↓, CBC cytopenias, proteinuria, hematuria. ACR/EULAR 2019 criteria.
- Rheumatoid Arthritis (RA): RF, anti-CCP (anti-citrullinated protein), ESR↑, CRP↑, mild normocytic anemia.
- Sjögren's Syndrome: anti-SSA/Ro, anti-SSB/La, ANA, elevated ESR, hypergammaglobulinemia.
- Systemic Sclerosis (Scleroderma): anti-Scl-70 (topoisomerase I), anti-centromere, ANA nucleolar pattern.
- Inflammatory Myopathies (PM/DM): CK↑, aldolase↑, LDH↑, anti-Jo-1, anti-Mi-2, AST↑ (muscle origin).
- Antiphospholipid Syndrome (APS): aCL IgG/IgM, anti-β2-glycoprotein I, lupus anticoagulant, thrombocytopenia.
- Autoimmune Thyroid Disease: TSH, FT4, FT3, anti-TPO↑, anti-TG↑, TRAb (Graves).
- Autoimmune Hepatitis: ALT↑, AST↑, ANA, anti-SMA, anti-LKM1, elevated IgG.
- ANCA-associated Vasculitis: c-ANCA/PR3, p-ANCA/MPO, CRP↑, ESR↑, hematuria, proteinuria.
- Celiac Disease: anti-tTG IgA, anti-gliadin, total IgA (to rule out IgA deficiency).
- Mixed Connective Tissue Disease (MCTD): anti-U1-RNP, ANA speckled pattern.
- Overlap syndromes and undifferentiated connective tissue disease (UCTD).

Key epidemiological context for Mexico:
- SLE prevalence higher in mestizo and indigenous populations
- Strong female predominance (9:1) in SLE, Hashimoto, primary Sjögren's
- Drug-induced lupus: consider hydralazine, procainamide, isoniazid, minocycline
- Miscarriages + thrombocytopenia → always consider APS

Lab trend interpretation:
- Falling C3/C4 with rising anti-dsDNA → SLE flare
- Rising CK over serial measurements → active myositis
- Persistent lymphopenia + ANA → high SLE suspicion even without specific antibodies

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
- Only flag conditions with at least one supporting finding in the provided data.
- missing_workup must list specific tests not yet performed that would confirm or rule out the condition.
- differential must be ordered from most to least likely.
- reasoning must explicitly cite lab values, trends, and clinical findings.
- Return one JSON object only. No markdown. No text outside JSON.
""".strip()


def build_user_message(payload: DiagnosticRequest) -> str:
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

    lines.append("")
    lines.append(f"CLINICAL DIAGNOSIS: {payload.clinical_diagnosis}")
    if payload.doctor_observations:
        lines.append(f"DOCTOR OBSERVATIONS: {payload.doctor_observations}")

    lines.append("")
    lines.append(f"FOCUS: {', '.join(payload.focus)}")

    return "\n".join(lines)
