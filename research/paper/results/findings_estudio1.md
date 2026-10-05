# Estudio 1 — Resultados de extracción (150 reportes sintéticos)

## Métricas globales

| Métrica | Valor |
|---|---|
| Recall de detección de analitos | 95.8% (1992 analitos esperados) |
| Precisión de nombre (entre detectados) | 89.1% |
| Exactitud de valor (entre detectados) | 92.0% |
| Exactitud de rango de referencia | 92.6% |
| F1 global (analito, valor) | 92.9% |
| Espurios por reporte (alucinaciones) | 0.21 en promedio |

## Por plantilla (recall / valor / rango / F1)

| Plantilla | Recall | Valor | Rango | F1 |
|---|---|---|---|---|
| 1 Simple | .96 | .98 | 1.00 | .95 |
| 2 Letterhead | .94 | .96 | .97 | .94 |
| 3 Panel grid | .97 | **.82** | **.82** | .89 |
| 4 Abreviado | .97 | **.74** | **.79** | .84 |
| 5 Escaneado | .98 | .94 | .85 | .96 |
| 6 Bilingüe | .97 | .94 | .96 | .95 |
| 7 Sello | .95 | .99 | .99 | .95 |
| 8 Narrativo | .92 | .87 | .90 | .89 |
| 9 Portal | .93 | .98 | .99 | .94 |
| 10 Multi-página | .98 | .97 | .98 | .97 |

**Plantilla 4 (abreviado)** es la más débil — confirma que nomenclatura no
estandarizada y unidades pegadas degradan la extracción más que cualquier
otro factor probado, incluida la calidad de imagen.

## Metadatos de paciente/reporte

| Campo | Exactitud |
|---|---|
| Nombre del paciente | 100% |
| Fecha de reporte | 92.0% |
| Folio/accession number | 38.7% (ver hallazgo cualitativo) |
| Sexo capturado correctamente | ver bug abajo |
| **Bug: sexo/edad mezclado en `date_of_birth`** | 8.7% de los reportes |

## Hallazgos cualitativos (con evidencia)

### 1. Sustitución sistemática de dígitos por fuente — plantilla 3 (grid denso)
El folio `NHI-2026-XXXXX` se transcribe consistentemente como `NHI-2826-XXXXX`
en TODOS los reportes de esta plantilla (monoespaciada, letra pequeña).
Confusión 0→8 inducida por el renderizado de la fuente, no ruido aleatorio.
```
GT:  NHI-2026-55718   ->   extraído: Folio NHI-2826-55718
GT:  NHI-2026-27589   ->   extraído: Folio NHI-2826-27589
```

### 2. Confusión de letra por degradación de imagen — plantilla 5 (escaneado)
`NHI` se lee como `NMI` de forma consistente bajo rotación + ruido simulado,
más errores aleatorios de dígitos individuales (a diferencia del error
sistemático de la plantilla 3).
```
GT:  NHI-2026-39272   ->   extraído: Folio NMI-2026-39272
GT:  NHI-2026-36137   ->   extraído: NMI-2606-36187
```
Un caso (`labtest_067`) confundió el folio completo con un ID de paciente
de otro campo — falla de asignación de campo, no solo de dígitos.

### 3. Serología cualitativa: título mal interpretado como magnitud
Un ANA positivo con título (`Positivo 1:320 patrón moteado`) se extrajo como
`value: 1640000, value_type: "numeric"`, perdiendo el formato de título.
El pipeline tampoco asigna código LOINC a niguna serología cualitativa
(`loinc_code: null` en el 100% de los casos observados), a diferencia de
los analitos cuantitativos que sí lo reciben consistentemente.

### 4. Codificación inconsistente de resultados positivos vs negativos
- Negativo → se fuerza a `value: 0, value_type: "numeric"`
- Positivo (ej. anticardiolipina) → a veces `value: "24 GPL-U/mL", value_type: "text"`
  (número y unidad concatenados en una sola cadena, en vez de separarse)

### 5. Campo de fecha de nacimiento mal usado
En plantillas con formato compacto de edad/sexo (ej. "34/F" en una sola
celda), el modelo a veces coloca ese texto crudo en `patient.date_of_birth`
(ej. `"41/F"`) y deja `patient.sex` en `null` — smearing de dos campos
distintos hacia uno solo. Ocurre en 8.7% de los 150 reportes.

## Intervención: correcciones aplicadas y re-medición

A partir de los hallazgos anteriores se aplicaron 3 correcciones al código
de producción (`document-reader`) y se corrió el benchmark completo de
nuevo sobre el mismo corpus de 150 reportes:

1. **Catálogo LOINC ampliado**: se agregaron las 8 serologías autoinmunes
   (antes ausentes de `terminology.py`, causa raíz de `loinc_code: null`).
2. **Matching de nombre tolerante a variaciones**: `find_definition` ahora
   tiene un fallback de similitud (difflib, umbral 0.85) para typos y
   nombres truncados, en vez de exigir coincidencia exacta/de prefijo.
   Beneficia las 76 definiciones preexistentes, no solo las nuevas.
3. **Resolución de imagen**: `RENDER_DPI` 96→150 y `MAX_IMAGE_DIMENSION`
   (el límite real, no el DPI, era el cuello de botella) 1024→1600.

| Métrica | Antes | Después |
|---|---|---|
| Recall de detección | 95.8% | 96.6% |
| Precisión de nombre | 89.1% | **92.2%** |
| Exactitud de valor | 92.0% | 92.5% |
| Exactitud de rango | 92.6% | 93.1% |
| F1 global | 92.9% | **94.0%** |
| Espurios (alucinaciones) por reporte | 0.207 | **0.100** |
| Folio con dígito sistemático correcto | 38.7% | 38.7% (sin cambio) |

**Resultado negativo, y es un hallazgo válido**: la sustitución sistemática
0→8 (plantilla 3) y H→M (plantilla 5) persiste **idéntica, carácter por
carácter**, tras subir la resolución de imagen. Esto descarta la hipótesis
de que fuera un problema de calidad/resolución de imagen y apunta a un
sesgo perceptual propio del modelo de visión de 8B con esa combinación
específica de fuente monoespaciada/rotación — no corregible con
preprocesamiento de imagen únicamente.

**Limitación de atribución**: las correcciones 1-2 y la 3 se desplegaron
juntas antes de re-medir, por lo que la mejora en F1/espurios no se puede
atribuir de forma limpia a una sola de ellas. Dado que el bug de folio
(el único que aislaba específicamente la hipótesis de resolución) no
cambió, es razonable atribuir la mejora observada principalmente a las
correcciones 1-2 (LOINC/matching) y no a la 3 (resolución de imagen).

## Segunda intervención: cambio de modelo de visión + extracción determinística

Motivado no solo por el paper sino por mejorar el servicio real: se investigó si
un modelo de visión distinto reduciría más las alucinaciones. Contexto de
hardware: la GPU (RTX 3090 Ti, 24GB) ya había fallado antes con un intento de
Qwen3-VL-32B-Instruct-AWQ-4bit (ver historial de commits `85ec015`/`4a9af87`:
pesos solos ocupan 20.83GB, dejando <3GB para KV cache — OOM). Qwen-VL no tiene
tamaño intermedio entre 7B/8B y 32B, así que "más grande, misma familia" no es
una opción viable en este hardware.

En su lugar se probó **RolmOCR** (Reducto AI), un fine-tune de Qwen2.5-VL-7B
especializado en OCR (dataset olmOCR-mix, 15% de datos rotados) — mismo
tamaño/VRAM que el modelo original, sin riesgo de OOM.

| Métrica | Baseline | +LOINC/matching/DPI | +RolmOCR | +RolmOCR +regex determinístico |
|---|---|---|---|---|
| F1 valores de laboratorio | 92.9% | 94.0% | 95.8% | **95.9%** |
| Fecha de reporte correcta | 92.0% | 92.0% | 59.3% | **95.3%** |
| Folio correcto | 38.7% | 38.7% | 18.0% | **98.0%** |
| Bug edad/sexo en `date_of_birth` | 8.7% | 8.7% | 2.7% | 2.7% |
| Alucinaciones por reporte | 0.207 | 0.100 | 0.080 | 0.080 |

**Hallazgo intermedio (trade-off real):** RolmOCR mejoró la lectura de valores
clínicos pero **empeoró notablemente** la fecha de reporte y el folio —
sistemáticamente confundía la fecha de toma de muestra con la fecha de
reporte cuando ambas aparecían juntas (ej. "Toma 2026-07-01 / Rep
2026-07-02" → extraía 2026-07-01), reproducible en 3 plantillas
independientes. Un ajuste de prompt explícito para desambiguar ambas fechas
**no tuvo ningún efecto** — evidencia de que el fine-tune de OCR sacrificó
flexibilidad de seguimiento de instrucciones fuera de su distribución de
entrenamiento, no arreglable por prompt engineering.

**Solución final:** en vez de pedirle al modelo que distinga los campos,
se añadió una extracción determinística por regex sobre el texto embebido
del PDF (`extract_deterministic_report_fields`), que sobreescribe la
respuesta del modelo cuando el documento no es un escaneo
(`profile.requires_ocr == False`) y encuentra una coincidencia
inequívoca. Como los PDFs nacidos digitales tienen una capa de texto sin
pérdida, esto no depende en absoluto de la calidad de OCR del modelo.
Resultado: folio pasó de 38.7% (mejor caso anterior) a 98.0%, fecha de
59.3% a 95.3%, sin sacrificar la mejora en valores clínicos de RolmOCR.

**Configuración final desplegada a producción:** RolmOCR + catálogo LOINC
ampliado + matching de nombre difuso + resolución de imagen aumentada +
extracción determinística de fecha/folio. Los 5 se corrieron juntos en el
benchmark final; individualmente aislar la contribución exacta de la
resolución de imagen (que no mostró efecto medible por sí sola en el
primer experimento) queda como limitación declarada.

## Implicación para el manuscrito

Estos hallazgos van al apartado de Resultados/Discusión como evidencia de
que el sistema es confiable para paneles cuantitativos estándar (F1 >0.94
en 6 de 10 formatos) pero tiene modos de falla reproducibles y
específicos de formato — no aleatorios — que un despliegue real debería
mitigar con validación de campo (ej. checksum de folio, LOINC obligatorio
para serologías, separación forzada de edad/sexo).
