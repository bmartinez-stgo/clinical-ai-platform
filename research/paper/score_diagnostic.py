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
#
# "sin_rag" = corrida original (results/diagnostic_raw/without_rag/), usada como
# referencia antes de que empezara la investigación de RAG.
# "final_disabled" = corrida posterior, MISMA configuración (RAG desactivado),
# hecha para confirmar el default de producción
# (results/diagnostic_raw/final_state_rag_disabled/). Al re-calificar esa corrida
# se encontraron 2 casos con resultado distinto al de la corrida original, por el
# muestreo no determinístico del modelo (temperature=0.1) -- ver manuscript.md
# Sección 4.3. case_12 cambia de correcto a incorrecto en top-1 (la autocorrección
# documentada); case_11 pierde a Sjögren del top-3 por completo (no documentado
# hasta la revisión de contenido del manuscrito del 2026-10-05).
#
# case_id -> (top1_with_rag, top3_with_rag, top1_without_rag, top3_without_rag,
#             top1_final_disabled, top3_final_disabled, nota)
JUDGMENTS = {
    "case_01_sle": (True, True, True, True, True, True, ""),
    "case_02_sle": (True, True, True, True, True, True, ""),
    "case_03_sle": (True, True, True, True, True, True, ""),
    "case_04_sle": (True, True, True, True, True, True, ""),
    "case_05_aps": (True, True, True, True, True, True, ""),
    "case_06_aps": (True, True, True, True, True, True, ""),
    "case_07_aps": (True, True, True, True, True, True,
                    "Dx confirmado es compuesto (LES+SAF 2rio); modelo puso SAF en #1 -- cuenta como correcto por ser componente real."),
    "case_08_aps": (True, True, True, True, True, True, ""),
    "case_09_aps": (True, True, True, True, True, True,
                    "SAF es 'posible' en el artículo original; SLE (componente principal) correctamente en #1."),
    "case_10_sjogren": (True, True, True, True, True, True, ""),
    "case_11_sjogren": (False, True, False, True, False, False,
                        "Tras el fix de umbral, CON RAG da top-1='Síndrome de Stevens-Johnson o Síndrome de Sjögren' "
                        "(bundled, no limpio) -- cuenta top3 no top1, igual que SIN RAG. Antes del fix, CON RAG lo "
                        "perdía por completo (ver with_rag_before_threshold_fix/). Limitación del modelo en esta "
                        "presentación, independiente de RAG. En la corrida final de confirmación (RAG desactivado, "
                        "results/diagnostic_raw/final_state_rag_disabled/) Sjögren desaparece también del top-3 "
                        "(lista de solo 2 diagnósticos, sin Sjögren) -- regresión adicional frente a la corrida "
                        "original 'sin_rag', encontrada en la revisión de contenido de 2026-10-05."),
    "case_12_sjogren": (True, True, True, True, False, True,
                        "Tras agregar el umbral mínimo de similitud (0.6) en ai-diagnostic, CON RAG ahora acierta "
                        "top-1 igual que SIN RAG. Antes del fix, CON RAG daba top-1 SAF (incorrecto) porque el único "
                        "caso en el store de clinical-rag (similarity 0.375, paciente de 69a con síndrome metabólico, "
                        "'trombocitopenia sin etiología autoinmune') se inyectaba igual pese a ser irrelevante. En la "
                        "corrida final de confirmación (RAG desactivado) el top-1 vuelve a ser incorrecto (SAF), "
                        "idéntico a la falla original pre-fix -- la autocorrección documentada en el manuscrito "
                        "Sección 4.3: el 'arreglo' observado aquí fue azar de muestreo (temperature=0.1), no un "
                        "efecto causal del umbral."),
    "case_13_ra": (True, True, True, True, True, True, ""),
    "case_14_ra_distractor": (False, False, False, False, False, False,
                              "Caso distractor: dx real es artritis paraneoplásica por adenocarcinoma gástrico, NO artritis "
                              "reumatoide. Las tres condiciones (con RAG, sin RAG, RAG desactivado) pusieron 'Artritis "
                              "Reumatoide' como top-1 pese a señales de alarma oncológica (pérdida de 12kg, anemia, "
                              "PCR/VSG muy elevados) -- el sistema no contempló malignidad como diagnóstico diferencial "
                              "en ninguna corrida."),
    "case_15_mctd": (True, True, True, True, True, True, ""),
    "case_16_mctd": (True, True, True, True, True, True, "'Síndrome de Overlap Mixto' cuenta como sinónimo de MCTD."),
    "case_17_mctd": (True, True, True, True, True, True, "'Síndrome de overlap mixto' cuenta como sinónimo de MCTD."),
    "case_18_rhupus": (True, True, True, True, True, True,
                       "Dx real es Rhupus (AR+LES). Modelo no usa el término 'Rhupus' pero top-1/2 cubren ambos componentes reales."),
    "case_19_rhupus": (True, True, True, True, True, True, "Mismo criterio que case_18."),
    "case_20_rhupus": (True, True, True, True, True, True, "Mismo criterio que case_18."),
}


def main():
    n = len(JUDGMENTS)
    top1_with = sum(1 for v in JUDGMENTS.values() if v[0])
    top3_with = sum(1 for v in JUDGMENTS.values() if v[1])
    top1_without = sum(1 for v in JUDGMENTS.values() if v[2])
    top3_without = sum(1 for v in JUDGMENTS.values() if v[3])
    top1_final = sum(1 for v in JUDGMENTS.values() if v[4])
    top3_final = sum(1 for v in JUDGMENTS.values() if v[5])

    summary = {
        "n_cases": n,
        "con_rag": {"top1_accuracy": top1_with / n, "top3_accuracy": top3_with / n},
        "sin_rag": {"top1_accuracy": top1_without / n, "top3_accuracy": top3_without / n},
        "final_disabled": {"top1_accuracy": top1_final / n, "top3_accuracy": top3_final / n},
        "casos_con_discrepancia_rag": [
            cid for cid, v in JUDGMENTS.items() if (v[0], v[1]) != (v[2], v[3])
        ],
        "casos_con_discrepancia_entre_corridas_sin_rag": [
            cid for cid, v in JUDGMENTS.items() if (v[2], v[3]) != (v[4], v[5])
        ],
        "casos": {cid: {"top1_con_rag": v[0], "top3_con_rag": v[1],
                         "top1_sin_rag": v[2], "top3_sin_rag": v[3],
                         "top1_final_disabled": v[4], "top3_final_disabled": v[5],
                         "nota": v[6]}
                  for cid, v in JUDGMENTS.items()},
    }

    Path("results/summary_diagnostic.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"N={n}")
    print(f"CON RAG:         top1={summary['con_rag']['top1_accuracy']:.0%}  top3={summary['con_rag']['top3_accuracy']:.0%}")
    print(f"SIN RAG:         top1={summary['sin_rag']['top1_accuracy']:.0%}  top3={summary['sin_rag']['top3_accuracy']:.0%}")
    print(f"RAG DESACTIVADO (corrida final): top1={summary['final_disabled']['top1_accuracy']:.0%}  top3={summary['final_disabled']['top3_accuracy']:.0%}")
    print("Discrepancias RAG (con vs sin, misma corrida):", summary["casos_con_discrepancia_rag"])
    print("Discrepancias entre corridas sin-RAG (no-determinismo):", summary["casos_con_discrepancia_entre_corridas_sin_rag"])


if __name__ == "__main__":
    main()
