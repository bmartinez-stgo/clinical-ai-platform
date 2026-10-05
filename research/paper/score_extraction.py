"""Califica los 150 resultados extraídos contra su ground truth.

Reglas de emparejamiento y calificación (documentadas aquí porque son parte
del método, no solo del código):

- Emparejamiento: LOINC exacto primero; si falta (frecuente en serologías
  cualitativas -- el pipeline no siempre asigna LOINC ahí), se usa
  similitud de nombre dentro del mismo "bucket" de panel, con un último
  recurso de asignación por eliminación (1 esperado y 1 extra sin
  emparejar en el mismo bucket).
- Analitos cuantitativos: valor correcto = dentro de ±1% del esperado.
- Analitos cualitativos (serologías): valor correcto = concordancia de
  polaridad positivo/negativo, no el número exacto -- el pipeline a veces
  fuerza negativos a value=0 y a veces mete texto de título ("1:320") como
  si fuera magnitud, así que comparar números ahí no tiene sentido clínico.
- Rango de referencia: solo se califica en analitos cuantitativos y no
  ocluidos (ver plantilla 7 en el protocolo).
"""
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).parent
GT_DIR = BASE / "datasets" / "ground_truth"
RAW_DIR = BASE / "results" / "raw"
OUT_DIR = BASE / "results"

STOPWORDS = {"anticuerpos", "anticuerpo", "de", "la", "el", "total", "panel", "serologico",
             "autoinmune", "autoimmune", "anti"}

PANEL_BUCKETS = [
    ("autoimmune", ["serolog", "autoinmun", "autoimmun"]),
    ("hematica", ["hemat"]),
    ("hepatica", ["hepat"]),
    ("lipidos", ["lipid", "colester"]),
    ("tiroidea", ["tiroid"]),
    ("quimica", ["quimic", "sangu"]),
]


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_text(s: str) -> str:
    s = strip_accents((s or "").lower())
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def bucket_of(panel_name: str) -> str:
    n = norm_text(panel_name)
    for bucket, keys in PANEL_BUCKETS:
        if any(k in n for k in keys):
            return bucket
    return "otro"


def name_similarity(a: str, b: str) -> float:
    ta = norm_text(a)
    tb = norm_text(b)
    return SequenceMatcher(None, ta, tb).ratio()


def is_numeric_str(s: str) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def leading_number(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"-?\d+(\.\d+)?", value)
        if m:
            return float(m.group())
    return None


def qualitative_polarity(valor_gt: str) -> str:
    v = valor_gt.lower()
    if v.startswith("positivo"):
        return "positivo"
    if v.startswith("negativo"):
        return "negativo"
    return "desconocido"


def actual_polarity(obs: dict) -> str:
    """Heurística: ¿el pipeline reportó esto como positivo o negativo?"""
    ref = (obs.get("reference_range_raw") or "").lower()
    interp = (obs.get("interpretation") or "").lower()
    value = obs.get("value")
    if interp in ("high", "low", "abnormal", "positive"):
        return "positivo"
    if obs.get("value_type") == "text":
        return "positivo"  # el pipeline solo usa texto libre para valores fuera de lo trivial
    if isinstance(value, (int, float)) and value not in (0, 0.0):
        return "positivo"
    if "neg" in ref or value in (0, 0.0):
        return "negativo"
    return "desconocido"


def match_report(expected: list[dict], observations: list[dict]) -> list[dict]:
    """Empareja cada analito esperado con la observación más probable.

    Devuelve una lista de dicts {expected, actual (o None), method}.
    """
    remaining_actual = list(observations)
    matches = []

    # Paso 1: LOINC exacto
    still_expected = []
    for exp in expected:
        found = None
        if exp.get("loinc"):
            for obs in remaining_actual:
                if obs.get("loinc_code") and obs["loinc_code"] == exp["loinc"]:
                    found = obs
                    break
        if found:
            remaining_actual.remove(found)
            matches.append({"expected": exp, "actual": found, "method": "loinc"})
        else:
            still_expected.append(exp)

    # Paso 2: similitud de nombre dentro del mismo bucket de panel
    unmatched_expected = []
    for exp in still_expected:
        bucket = bucket_of(exp["panel"])
        candidates = [o for o in remaining_actual if bucket_of(o.get("panel_raw") or "") == bucket]
        best, best_score = None, 0.0
        for obs in candidates:
            score = max(
                name_similarity(exp["nombre"], obs.get("test_name_raw") or ""),
                name_similarity(exp["nombre"], obs.get("test_name_normalized") or ""),
                name_similarity(exp["abrev"], obs.get("test_name_raw") or ""),
            )
            if score > best_score:
                best, best_score = obs, score
        if best is not None and best_score >= 0.35:
            remaining_actual.remove(best)
            matches.append({"expected": exp, "actual": best, "method": f"fuzzy:{best_score:.2f}"})
        else:
            unmatched_expected.append((exp, bucket))

    # Paso 3: último recurso por eliminación (1 esperado y 1 sobrante en el mismo bucket)
    still_unmatched = []
    for exp, bucket in unmatched_expected:
        candidates = [o for o in remaining_actual if bucket_of(o.get("panel_raw") or "") == bucket]
        if len(candidates) == 1:
            obs = candidates[0]
            remaining_actual.remove(obs)
            matches.append({"expected": exp, "actual": obs, "method": "elimination"})
        else:
            still_unmatched.append(exp)

    for exp in still_unmatched:
        matches.append({"expected": exp, "actual": None, "method": "none"})

    for obs in remaining_actual:
        matches.append({"expected": None, "actual": obs, "method": "spurious"})

    return matches


def score_pair(exp: dict, obs: dict) -> dict:
    is_qual = not is_numeric_str(exp["valor"])
    name_ok = name_similarity(exp["nombre"], obs.get("test_name_raw") or "") >= 0.75 or \
        name_similarity(exp["nombre"], obs.get("test_name_normalized") or "") >= 0.75

    if is_qual:
        gt_pol = qualitative_polarity(exp["valor"])
        act_pol = actual_polarity(obs)
        value_ok = (gt_pol == act_pol) and gt_pol != "desconocido"
        range_ok = None  # no aplica
    else:
        gt_val = float(exp["valor"])
        act_val = leading_number(obs.get("value"))
        if act_val is None:
            value_ok = False
        else:
            tol = max(abs(gt_val) * 0.01, 0.01)
            value_ok = abs(act_val - gt_val) <= tol
        if exp.get("occluded"):
            range_ok = None
        else:
            rr = obs.get("reference_range") or {}
            low, high = rr.get("low"), rr.get("high")
            gt_range = exp["rango_ref"]
            gt_low, gt_high = None, None
            m = re.match(r"^([\d.]+)-([\d.]+)$", gt_range)
            if m:
                gt_low, gt_high = float(m.group(1)), float(m.group(2))
            elif gt_range.startswith("<"):
                gt_high = float(gt_range[1:])
            if gt_low is not None and low is not None:
                range_ok = abs(low - gt_low) <= 0.05 * max(gt_low, 1) and \
                    (high is not None and abs(high - gt_high) <= 0.05 * max(gt_high, 1))
            elif gt_high is not None and gt_low is None:
                range_ok = high is not None and abs(high - gt_high) <= 0.05 * max(gt_high, 1)
            else:
                range_ok = False

    return {"name_ok": name_ok, "value_ok": value_ok, "range_ok": range_ok, "is_qualitative": is_qual}


def score_metadata(gt: dict, result: dict) -> dict:
    patient = result.get("patient") or {}
    report = result.get("report") or {}
    nombre_ok = name_similarity(gt["patient"]["nombre"], patient.get("name") or "") >= 0.85
    folio_ok = (report.get("accession_number") or "").strip() == gt["folio"].strip()
    fecha_ok = (report.get("report_date") or "") == gt["fecha_reporte"]
    sexo_actual = (patient.get("sex") or "").strip().upper()[:1]
    sexo_ok = sexo_actual == gt["patient"]["sexo"]
    dob = str(patient.get("date_of_birth") or "")
    sex_merged_into_dob = (not sexo_ok) and bool(re.match(r"^\d{1,3}\s*/\s*[MF]", dob.strip(), re.I))
    return {
        "nombre_ok": nombre_ok, "folio_ok": folio_ok, "fecha_ok": fecha_ok,
        "sexo_ok": sexo_ok, "sex_merged_into_dob_bug": sex_merged_into_dob,
    }


def main():
    per_report = []
    for gt_path in sorted(GT_DIR.glob("labtest_*.json")):
        report_id = gt_path.stem
        raw_path = RAW_DIR / f"{report_id}.json"
        if not raw_path.exists():
            continue
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        result = json.loads(raw_path.read_text(encoding="utf-8"))

        matches = match_report(gt["expected"], result.get("observations") or [])
        analyte_scores = []
        for m in matches:
            if m["expected"] is None:
                analyte_scores.append({"kind": "spurious"})
                continue
            if m["actual"] is None:
                analyte_scores.append({"kind": "missed", "nombre": m["expected"]["nombre"]})
                continue
            s = score_pair(m["expected"], m["actual"])
            s["kind"] = "matched"
            s["method"] = m["method"]
            s["nombre"] = m["expected"]["nombre"]
            analyte_scores.append(s)

        meta = score_metadata(gt, result)

        per_report.append({
            "report_id": report_id,
            "template": gt["template"],
            "n_expected": len(gt["expected"]),
            "analyte_scores": analyte_scores,
            "metadata": meta,
        })

    OUT_DIR.joinpath("scored_detail.json").write_text(
        json.dumps(per_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"calificados {len(per_report)} reportes -> results/scored_detail.json")


if __name__ == "__main__":
    main()
