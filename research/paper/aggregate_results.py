"""Consolida results/scored_detail.json en métricas globales y por plantilla."""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
DETAIL = json.loads((BASE / "results" / "scored_detail.json").read_text(encoding="utf-8"))


def summarize(reports: list[dict]) -> dict:
    n_expected = sum(r["n_expected"] for r in reports)
    matched = spurious = missed = 0
    name_ok = value_ok = 0
    range_total = range_ok = 0
    tp = fp = fn = 0

    for r in reports:
        for a in r["analyte_scores"]:
            if a["kind"] == "spurious":
                spurious += 1
                fp += 1
            elif a["kind"] == "missed":
                missed += 1
                fn += 1
            else:  # matched
                matched += 1
                if a["name_ok"]:
                    name_ok += 1
                if a["value_ok"]:
                    value_ok += 1
                    tp += 1
                else:
                    fn += 1
                if a["range_ok"] is not None:
                    range_total += 1
                    if a["range_ok"]:
                        range_ok += 1

    precision = tp / (tp + fp) if (tp + fp) else None
    recall_f1 = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall_f1 / (precision + recall_f1)) if precision and recall_f1 else None

    meta_n = len(reports)
    meta_agg = defaultdict(int)
    for r in reports:
        for k, v in r["metadata"].items():
            if v:
                meta_agg[k] += 1

    return {
        "n_reports": len(reports),
        "n_expected_analytes": n_expected,
        "recall_deteccion": matched / n_expected if n_expected else None,
        "precision_nombre": name_ok / matched if matched else None,
        "exactitud_valor": value_ok / matched if matched else None,
        "exactitud_rango": range_ok / range_total if range_total else None,
        "f1_global": f1,
        "precision_global": precision,
        "recall_global": recall_f1,
        "espurios_por_reporte": spurious / meta_n if meta_n else None,
        "metadata": {k: v / meta_n for k, v in meta_agg.items()},
    }


def main():
    overall = summarize(DETAIL)
    by_template = defaultdict(list)
    for r in DETAIL:
        by_template[r["template"]].append(r)

    result = {
        "overall": overall,
        "by_template": {t: summarize(rs) for t, rs in sorted(by_template.items())},
    }
    Path(BASE / "results" / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=== GLOBAL ===")
    for k, v in overall.items():
        if k != "metadata":
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    print("  metadata:")
    for k, v in overall["metadata"].items():
        print(f"    {k}: {v:.3f}")

    print("\n=== POR PLANTILLA (recall / valor / rango / f1) ===")
    for t, s in sorted(result["by_template"].items()):
        def fmt(x):
            return f"{x:.2f}" if isinstance(x, float) else "N/A"
        print(f"  {t:28s} recall={fmt(s['recall_deteccion'])} "
              f"valor={fmt(s['exactitud_valor'])} "
              f"rango={fmt(s['exactitud_rango'])} "
              f"f1={fmt(s['f1_global'])}")


if __name__ == "__main__":
    main()
