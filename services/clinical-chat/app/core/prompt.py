from __future__ import annotations

from typing import Any


_SYSTEM_ES = """Eres un asistente clínico de apoyo diagnóstico en modo conversacional. \
Ya se realizó una inferencia diagnóstica inicial sobre el paciente. \
Tu rol es responder preguntas de seguimiento del médico con base en los datos clínicos \
y el resultado diagnóstico proporcionados.

Reglas:
- Sé conciso y clínico. Máximo 3-4 oraciones por respuesta.
- Cita valores de laboratorio específicos cuando sean relevantes.
- No emitas diagnósticos definitivos; usa lenguaje de probabilidad ("sugiere", "es compatible con", "requiere descartar").
- Si la pregunta está fuera del alcance de los datos disponibles, indícalo claramente.
- Responde siempre en español."""

_SYSTEM_EN = """You are a clinical decision support assistant in conversational mode. \
A diagnostic inference was already performed on the patient. \
Your role is to answer follow-up questions from the physician based on the clinical data \
and diagnostic result provided.

Rules:
- Be concise and clinical. Maximum 3-4 sentences per response.
- Cite specific lab values when relevant.
- Do not issue definitive diagnoses; use probabilistic language ("suggests", "is compatible with", "requires ruling out").
- If the question is outside the scope of available data, state so clearly.
- Always respond in English."""


def build_system_prompt(
    diagnostic_context: dict[str, Any],
    diagnostic_result: dict[str, Any],
    language: str,
) -> str:
    base = _SYSTEM_EN if language == "en" else _SYSTEM_ES
    lines: list[str] = [base, ""]

    p = diagnostic_context.get("patient", {})
    lines.append(f"PACIENTE: {p.get('age', '?')}a {p.get('sex', '?')}" +
                 (f", {p.get('ethnicity')}" if p.get("ethnicity") else ""))

    history = diagnostic_context.get("history", {})
    comorbidities = history.get("comorbidities", [])
    medications = history.get("current_medications", [])
    if comorbidities:
        lines.append(f"Comorbilidades: {', '.join(comorbidities)}")
    if medications:
        lines.append(f"Medicamentos: {', '.join(medications)}")

    lab_series = diagnostic_context.get("lab_series", [])
    if lab_series:
        latest = lab_series[-1]
        lines.append(f"\nÚLTIMOS LABORATORIOS [{latest.get('report_date', '')}]:")
        for r in latest.get("results", []):
            interp = f" [{r.get('interpretation', '').upper()}]" if r.get("interpretation") else ""
            lines.append(f"  {r.get('test_name')}: {r.get('value')} {r.get('unit') or ''}{interp}")

    lines.append(f"\nDIAGNÓSTICO CLÍNICO: {diagnostic_context.get('clinical_diagnosis', '')}")

    flags = diagnostic_result.get("autoimmune_flags", [])
    differential = diagnostic_result.get("differential", [])
    reasoning = diagnostic_result.get("reasoning", "")
    confidence = diagnostic_result.get("confidence", "")

    if flags:
        lines.append("\nBANDERAS AUTOINMUNES:")
        for f in flags:
            findings = ", ".join(f.get("supporting_findings", []))
            lines.append(f"  - {f.get('condition')} ({f.get('likelihood')}): {findings}")
    else:
        lines.append("\nSin banderas autoinmunes.")

    if differential:
        lines.append(f"\nDIFERENCIAL: {', '.join(differential[:5])}")

    lines.append(f"\nRAZONAMIENTO IA: {reasoning}")
    lines.append(f"CONFIANZA: {confidence}")

    return "\n".join(lines)
