"""Calificación del Estudio 2 (diagnóstico asistido) contra los 20 casos reales.

La calificación de concordancia (top-1/top-3 contra el diagnóstico publicado,
con equivalencia de sinónimos y diagnósticos compuestos) requiere juicio
clínico -- se documenta aquí como un solo evaluador no clínico titulado
(limitación declarada en el protocolo), con la nota de cada decisión no
obvia para que sea auditable.

Reglas de equivalencia aplicadas:
- Síndrome de "overlap"/"conectivopatía mixta" cuenta como match de MCTD.
- Para diagnósticos compuestos (ej. "LES con SAF secundario", "Rhupus" =
  AR+LES), que el modelo mencione CUALQUIERA de los componentes reales en
  el top-1 cuenta como top-1 correcto -- son, ambos, parte del diagnóstico
  verdadero, no alternativas incorrectas.
- Para el caso distractor (case_14, diagnóstico real = artritis
  paraneoplásica, NO artritis reumatoide), "Artritis Reumatoide" en
  cualquier posición cuenta como INCORRECTO -- es exactamente lo que el
  caso está diseñado para distinguir.
"""
import json
from pathlib import Path

# Segunda corrida de "con RAG" tras agregar un umbral mínimo de similitud
# (CLINICAL_RAG_MIN_SIMILARITY=0.6) en ai-diagnostic -- la corrida original
# (antes del fix) queda archivada en results/diagnostic_raw/with_rag_before_threshold_fix/.
# case_id -> (top1_with_rag, top3_with_rag, top1_without_rag, top3_without_rag, nota)
JUDGMENTS = {
    "case_01_sle": (True, True, True, True, ""),
    "case_02_sle": (True, True, True, True, ""),
    "case_03_sle": (True, True, True, True, ""),
    "case_04_sle": (True, True, True, True, ""),
    "case_05_aps": (True, True, True, True, ""),
    "case_06_aps": (True, True, True, True, ""),
    "case_07_aps": (True, True, True, True,
                    "Dx confirmado es compuesto (LES+SAF 2rio); modelo puso SAF en #1 -- cuenta como correcto por ser componente real."),
    "case_08_aps": (True, True, True, True, ""),
    "case_09_aps": (True, True, True, True,
                    "SAF es 'posible' en el artículo original; SLE (componente principal) correctamente en #1."),
    "case_10_sjogren": (True, True, True, True, ""),
    "case_11_sjogren": (False, True, False, True,
                        "Tras el fix de umbral, CON RAG da top-1='Síndrome de Stevens-Johnson o Síndrome de Sjögren' "
                        "(bundled, no limpio) -- cuenta top3 no top1, igual que SIN RAG. Antes del fix, CON RAG lo "
                        "perdía por completo (ver with_rag_before_threshold_fix/). Limitación del modelo en esta "
                        "presentación, independiente de RAG."),
    "case_12_sjogren": (True, True, True, True,
                        "Tras agregar el umbral mínimo de similitud (0.6) en ai-diagnostic, CON RAG ahora acierta "
                        "top-1 igual que SIN RAG. Antes del fix, CON RAG daba top-1 SAF (incorrecto) porque el único "
                        "caso en el store de clinical-rag (similarity 0.375, paciente de 69a con síndrome metabólico, "
                        "'trombocitopenia sin etiología autoinmune') se inyectaba igual pese a ser irrelevante."),
    "case_13_ra": (True, True, True, True, ""),
    "case_14_ra_distractor": (False, False, False, False,
                              "Caso distractor: dx real es artritis paraneoplásica por adenocarcinoma gástrico, NO artritis "
                              "reumatoide. Ambas condiciones (con y sin RAG) pusieron 'Artritis Reumatoide' como top-1 pese a "
                              "señales de alarma oncológica (pérdida de 12kg, anemia, PCR/VSG muy elevados) -- el sistema no "
                              "contempló malignidad como diagnóstico diferencial en ninguna corrida."),
    "case_15_mctd": (True, True, True, True, ""),
    "case_16_mctd": (True, True, True, True, "'Síndrome de Overlap Mixto' cuenta como sinónimo de MCTD."),
    "case_17_mctd": (True, True, True, True, "'Síndrome de overlap mixto' cuenta como sinónimo de MCTD."),
    "case_18_rhupus": (True, True, True, True,
                       "Dx real es Rhupus (AR+LES). Modelo no usa el término 'Rhupus' pero top-1/2 cubren ambos componentes reales."),
    "case_19_rhupus": (True, True, True, True, "Mismo criterio que case_18."),
    "case_20_rhupus": (True, True, True, True, "Mismo criterio que case_18."),
}


def main():
    n = len(JUDGMENTS)
    top1_with = sum(1 for v in JUDGMENTS.values() if v[0])
    top3_with = sum(1 for v in JUDGMENTS.values() if v[1])
    top1_without = sum(1 for v in JUDGMENTS.values() if v[2])
    top3_without = sum(1 for v in JUDGMENTS.values() if v[3])

    summary = {
        "n_cases": n,
        "con_rag": {"top1_accuracy": top1_with / n, "top3_accuracy": top3_with / n},
        "sin_rag": {"top1_accuracy": top1_without / n, "top3_accuracy": top3_without / n},
        "casos_con_discrepancia_rag": [
            cid for cid, v in JUDGMENTS.items() if (v[0], v[1]) != (v[2], v[3])
        ],
        "casos": {cid: {"top1_con_rag": v[0], "top3_con_rag": v[1],
                         "top1_sin_rag": v[2], "top3_sin_rag": v[3], "nota": v[4]}
                  for cid, v in JUDGMENTS.items()},
    }

    Path("results/summary_diagnostic.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"N={n}")
    print(f"CON RAG:  top1={summary['con_rag']['top1_accuracy']:.0%}  top3={summary['con_rag']['top3_accuracy']:.0%}")
    print(f"SIN RAG:  top1={summary['sin_rag']['top1_accuracy']:.0%}  top3={summary['sin_rag']['top3_accuracy']:.0%}")
    print("Discrepancias RAG:", summary["casos_con_discrepancia_rag"])


if __name__ == "__main__":
    main()
