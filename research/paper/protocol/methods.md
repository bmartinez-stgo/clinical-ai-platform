# Protocolo de evaluación — Clinical AI Platform

Objetivo: reunir evidencia empírica para un artículo original en Revista Mexicana de
Ingeniería Biomédica (RMIB), sección Informática Médica / Ingeniería Clínica.

Declaración ética (para el manuscrito): en ninguna etapa se usan datos identificables
de pacientes reales. El benchmark de extracción usa reportes de laboratorio
enteramente sintéticos. El benchmark de diagnóstico usa casos clínicos ya publicados
y de acceso abierto (PubMed Central), es decir, datos secundarios ya de-identificados
por la publicación original — se cita cada fuente.

---

## Estudio 1 — Precisión de extracción de reportes de laboratorio

**Diseño:** N=150 reportes de laboratorio sintéticos, 10 plantillas visuales
distintas (15 c/u), cada una dirigida a un modo de falla real distinto:
1. Tabla genérica de una columna (estilo laboratorio clínico pequeño) — línea base
2. Dos columnas con membrete corporativo — línea base de formato
3. Formato condensado por panel (estilo laboratorio de referencia grande)
4. Abreviaturas y unidades no estandarizadas (estrés de nomenclatura)
5. Apariencia de escaneo/foto con rotación y ruido (estrés de calidad de imagen)
6. Encabezados bilingües ES/EN (estrés de nomenclatura)
7. Sello y firma superpuestos (ruido visual sin alterar los datos)
8. Resultados en prosa, sin tabla (estrés de estructura no tabular)
9. Portal digital con QR simulado y flags tipo checkbox (formato moderno)
10. Multi-página, folio en continuación sin repetir datos del paciente
    (ejercita el merge de páginas de `document-reader`)

**Contenido por reporte:** 5–25 analitos (mediana ~13, variable según cuántos
paneles se solicitan en cada caso, igual que en la práctica real) con nombre,
valor, unidad, rango de referencia y código LOINC conocido (ground truth en
JSON). Paneles cubiertos:
BH completa, química sanguínea, perfil de lípidos, perfil tiroideo, y el panel
serológico autoinmune que es la especialidad del sistema (ANA, anti-dsDNA,
SSA/SSB, FR, anti-CCP, anticuerpos antifosfolípido).

**Procedimiento:** cada PDF se renderiza a imagen igual que en producción
(PyMuPDF) y se envía al endpoint real `/labs/parse` de `document-reader`
(`OCR_BACKEND=ai-engine`, backend desplegado). Se registra la respuesta cruda.

**Métricas** (por reporte y agregadas):
- Exactitud de metadatos de paciente/reporte
- Recall de detección de analitos (detectados / esperados)
- Precisión de nombre de analito (correctos / detectados)
- Exactitud de valor (coincidencia exacta o tolerancia numérica ±1%)
- Exactitud de rango de referencia
- F1 global tratando cada par (analito, valor) esperado como objetivo de recuperación
- Análisis cualitativo de modos de falla por plantilla

---

## Estudio 2 — Precisión del diferencial diagnóstico asistido

**Diseño:** N=20 casos clínicos reales publicados en PMC (open access), con
hallazgos serológicos autoinmunes reportados explícitamente y diagnóstico final
confirmado en el texto. Búsqueda dirigida a: LES, síndrome antifosfolípido,
Sjögren, artritis reumatoide, enfermedad mixta del tejido conectivo.

**Procedimiento:** de cada caso se extraen las anormalidades de laboratorio y
serologías reportadas y se convierten al formato de entrada de `ai-diagnostic`.
Se corre el pipeline real dos veces por caso (ablación):
- `clinical_rag_enabled=true` (con contexto de `clinical-rag`)
- `clinical_rag_enabled=false`

Se registra el diferencial diagnóstico completo generado por `vllm-reasoning`.

**Calificación:** comparación manual (un solo evaluador, limitación declarada
en el manuscrito) del diferencial contra el diagnóstico final publicado,
con equivalencia de sinónimos. Métricas: exactitud top-1, exactitud top-3
(el diagnóstico correcto aparece entre las primeras 3 opciones), comparando
con y sin RAG.

**Trazabilidad:** cada caso fuente se cita con DOI/PMCID en el apéndice del
manuscrito. Ningún caso se parafrasea sin verificar contra el texto original.

---

## Limitaciones a declarar en el manuscrito

- N pequeño en ambos estudios (piloto, no ensayo clínico)
- Extracción evaluada solo con datos sintéticos, no reportes reales de laboratorio
- Calificación diagnóstica por un solo evaluador no clínico titulado
- Versión específica de modelos (Qwen3-VL-8B-Instruct, Qwen2.5-32B-Instruct-AWQ)
  fijada al momento del estudio — resultados no generalizan a otras versiones
- Sistema no validado clínicamente ni aprobado para uso diagnóstico real
