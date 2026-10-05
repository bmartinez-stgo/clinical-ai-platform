# Estudio 2 — Resultados del diagnóstico asistido (20 casos clínicos reales)

## Fuente de los casos

20 casos de publicaciones reales, acceso abierto en PMC/Europe PMC, citados
individualmente con DOI/PMCID en `datasets/clinical_cases.py`. Cobertura:
4 LES, 5 SAF, 3 Sjögren, 1 AR + 1 distractor (artritis paraneoplásica con
serología positiva para AR), 3 EMTC, 3 Rhupus. Los hallazgos de laboratorio
enviados a `ai-diagnostic` son exactamente los reportados en cada artículo
—ningún valor fue inventado— y `clinical_diagnosis` (motivo de consulta)
nunca contiene el diagnóstico final.

## Resultado final (configuración desplegada a producción: RAG desactivado)

Corrida inicial sin RAG (`without_rag/`, usada como referencia antes de
empezar la investigación de RAG):

| Métrica | Valor |
|---|---|
| Exactitud top-1 | 90% (18/20) |
| Exactitud top-3 | 95% (19/20) |

Corrida final de confirmación, misma configuración, hecha después de
desactivar RAG en producción (`final_state_rag_disabled/`) — ver hallazgo
6b abajo:

| Métrica | Valor |
|---|---|
| Exactitud top-1 | 85% (17/20) |
| Exactitud top-3 | 90% (18/20) |

`case_14` (distractor, artritis paraneoplásica) falla en las 4 corridas,
sin excepción — ver sección dedicada abajo. `case_11` (Sjögren con
acidosis tubular renal e hipopotasemia severa) falla siempre en top-1,
pero su estatus en top-3 varía entre corridas de la misma configuración
(ver hallazgo 6b): el modelo nunca prioriza Sjögren como causa raíz pese
a anti-SSA/SSB claramente positivos, el cuadro metabólico dramático
domina su razonamiento. Limitación real del modelo, no de RAG.

## Cronología de la investigación del RAG — incluye una autocorrección

Esto se documenta en detalle porque el proceso de llegar al resultado final
es, en sí, el hallazgo más relevante del estudio.

**1. Primera corrida (con RAG, store con 1 caso irrelevante).** Top-1 85%
vs. 90% sin RAG — `clinical-rag` solo tenía un caso guardado (hombre de 69
años, síndrome metabólico), y se inyectaba en cada consulta sin importar la
relevancia (similarity 0.375), con una nota ("trombocitopenia sin etiología
autoinmune") que desvió al modelo en `case_12` (dio SAF en vez de Sjögren).

**2. Primera corrección: umbral mínimo de similitud (0.6).** Se agregó
`CLINICAL_RAG_MIN_SIMILARITY` en `ai-diagnostic` para descartar coincidencias
débiles. Al re-correr, `case_12` dio el diagnóstico correcto (Sjögren) y el
resultado con RAG igualó al de sin RAG (90%/95%). **En su momento se
interpretó esto como la corrección exitosa del problema.**

**3. Intento de poblar el store con 6 casos reales nuevos** (esclerosis
sistémica, vasculitis ANCA, síndrome antisintetasa — categorías distintas a
las de los 20 casos de prueba, para no contaminar el benchmark). Al
re-correr: **15 de 20 casos cambiaron su top-1**, varios hacia respuestas
abiertamente incorrectas (ej. `case_02`, un LES confirmado, dio "Síndrome
antisintetasa" como top-1).

**4. Diagnóstico de causa raíz: no hay separación confiable entre
coincidencias genuinas y falsas.** Se probó consultando `clinical-rag`
directamente con perfiles casi idénticos a los casos sembrados:

| Consulta | Similarity | ¿Caso correcto recuperado? |
|---|---|---|
| Perfil ≈idéntico al caso de síndrome antisintetasa sembrado | **0.844** | Sí |
| Mismo caso de síndrome antisintetasa, consultado con el perfil de LES de `case_02` (sin relación) | 0.746 | — (falso positivo) |
| Perfil ≈idéntico al caso de vasculitis ANCA sembrado | **0.749** | Sí, pero empatado con el rango de falsos positivos |
| Perfil ≈idéntico al caso de esclerosis sistémica sembrado | **0.685** | **No** — recuperó el caso equivocado (síndrome antisintetasa) |

Una coincidencia genuina puede dar *menor* similitud (0.685) que una
coincidencia espuria (0.746). No existe un umbral que separe limpiamente lo
correcto de lo incorrecto con este embedding (sentence-transformer
multilingüe genérico sobre texto concatenado de edad/sexo/analitos) y este
tamaño de store. Subir el número no resuelve un problema de falta de señal.

**5. Decisión: desactivar RAG en producción** (`clinicalRagEnabled: false`
en el chart). Se re-corrieron los 20 casos con RAG desactivado para
confirmar el estado final.

**6. Autocorrección importante:** con RAG desactivado, `case_12` **volvió a
fallar** (SAF en vez de Sjögren, aunque Sjögren queda en el top-3). Esto
revela que el "arreglo" observado en el paso 2 fue **coincidencia de
muestreo del modelo** (`temperature=0.1`, no determinístico), no un efecto
causal del umbral de RAG — con el mismo contexto efectivo (sin información
de RAG útil) el modelo da respuestas distintas en corridas distintas para
este caso límite. Se corrige aquí la interpretación original en vez de
dejarla como estaba: es un ejemplo real de por qué una sola corrida no basta
para atribuir causalidad en un sistema con muestreo estocástico.

**6b. Segundo hallazgo, encontrado en la revisión de contenido del
manuscrito del 2026-10-05 (no detectado antes):** en esa misma corrida
final (RAG desactivado), `case_11` **también cambió** respecto a la
corrida original `without_rag/`: Sjögren desaparece por completo de su
lista de top-3 (antes aparecía en 2do lugar, ahora la lista solo tiene
2 diagnósticos y ninguno es Sjögren). Esto significa que el resultado
agregado de la corrida final de confirmación (RAG desactivado) es
**top-1 85% (17/20), top-3 90% (18/20)** -- NO igual al baseline original
de 90%/95% como se había asumido y reportado inicialmente en la Tabla 2
del manuscrito (la fila "final state" copiaba el número del baseline sin
volver a calificar la corrida real). Corregido en `score_diagnostic.py`
(columnas `top1_final_disabled`/`top3_final_disabled`, regenera
`results/summary_diagnostic.json`) y en `manuscript.md` (Abstract, §3.2,
Tabla 2, §4.3, Conclusiones). El hallazgo refuerza, no debilita, el
argumento metodológico: incluso la configuración "sin RAG", corrida dos
veces de forma idéntica, no es perfectamente reproducible.

## Hallazgo secundario: el sistema no contempla malignidad como diferencial

El caso distractor (`case_14`, artritis paraneoplásica por adenocarcinoma
gástrico con FR y anti-CCP falsamente positivos) **falló en las 4 corridas**
— top-1 siempre fue "Artritis Reumatoide", pese a señales de alarma
oncológica explícitas (pérdida de 12 kg, anemia microcítica, PCR 17.3 mg/dL,
VSG 94 mm/h). El sistema ancla al diagnóstico sugerido por la serología
positiva sin generar alternativas que consideren un proceso neoplásico
subyacente, consistentemente, con o sin RAG.

## Diagnósticos compuestos y de superposición

En los 3 casos de Rhupus (AR+LES) y el de LES con SAF secundario, el
sistema nunca usó el término de síndrome de superposición, pero listó
ambos componentes reales del diagnóstico en el top-2 de forma consistente.

## Conclusión sobre RAG para el manuscrito

`clinical-rag`, tal como está implementado (embedding de texto genérico
concatenado + ChromaDB, sin ponderar coincidencia de código LOINC/analito
específico), **no demostró beneficio en ninguna configuración probada**, y
con un store mínimamente poblado demostró poder **degradar activamente**
el diferencial. La causa no es la falta de datos por sí sola, sino que el
método de similitud no tiene señal suficiente para discriminar relevancia
clínica real en embeddings de texto corto y estructurado. Repensar el
mecanismo de recuperación (ej. ponderar por superposición de códigos LOINC
o patrones de serología específicos, no solo similitud semántica de texto)
es un prerequisito antes de volver a intentar poblar el store, no solo
agregar más casos.

## Limitaciones de este estudio

- N=20, piloto — no alcanza para significancia estadística
- Calificación top-1/top-3 por un solo evaluador no clínico titulado, con
  equivalencia de sinónimos documentada caso por caso en `score_diagnostic.py`
- El modelo de lenguaje (`vllm-reasoning`, temperature=0.1) no es
  determinístico — se observó directamente en `case_12` que el mismo
  contexto efectivo puede dar respuestas distintas entre corridas; los
  resultados de top-1/top-3 reportados son de una sola corrida por
  condición, no un promedio de múltiples corridas
- El toggle de RAG es a nivel de servicio, no por solicitud — las corridas
  se hicieron secuencialmente, no intercaladas
