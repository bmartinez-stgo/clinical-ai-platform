# Clinical AI Platform — Partner Integration Runbook

## Resumen

Este documento explica cómo conectar un sistema clínico externo a la plataforma de IA para:
1. **Parsear PDFs de laboratorio** → extrae analitos, valores, rangos de referencia
2. **Ejecutar inferencia diagnóstica** → genera diagnóstico diferencial a partir de los resultados

---

## 1. Información de acceso

| Item | Valor |
|---|---|
| Base URL | `https://nahui-ai.ddns.net` |
| Swagger UI (requiere login) | `https://nahui-ai.ddns.net/auth/ui/api-docs.html` |
| SDK Python | `https://nahui-ai.ddns.net/auth/ui/clinical_ai_client.py` |
| Autenticación | OAuth2 Client Credentials (RFC 6749 §4.4) |

**`client_id` y `client_secret`** son generados por el administrador de la plataforma y se entregan por canal seguro (no se almacena el secret — se muestra solo una vez al crearlo).

---

## 2. Leer el Swagger UI

1. Ir a `https://nahui-ai.ddns.net/auth/ui/` e iniciar sesión con las credenciales entregadas
2. Navegar a `https://nahui-ai.ddns.net/auth/ui/api-docs.html`
3. La documentación interactiva carga automáticamente con el token pre-autorizado
4. "Try it out" en cada endpoint funciona directamente desde el navegador

---

## 3. Autenticación — obtener token

El sistema usa **OAuth2 Client Credentials**. El token se renueva automáticamente — no se necesita intervención humana.

### Request

```http
POST https://nahui-ai.ddns.net/auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<CLIENT_SECRET>
```

### Response

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

El token dura **1 hora**. Debe enviarse en todas las llamadas como:

```http
Authorization: Bearer <access_token>
```

---

## 4. Endpoint 1 — Parsear PDF de laboratorio

```http
POST https://nahui-ai.ddns.net/documents/labs/parse?language=es
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <PDF_BYTES>
```

- `language`: `es` (español, default) o `en`
- Tamaño máximo: **20 MB**
- Formatos: PDF, PNG, JPG, WEBP

### Response

```json
{
  "document_id": "cf287257-e2c2-4b27-864c-b4528d8ec3a7",
  "document_type": "lab_report",
  "source": {
    "filename": "hemograma_maria.pdf",
    "content_type": "application/pdf",
    "page_count": 3,
    "language": "es-MX",
    "response_language": "es"
  },
  "patient": {
    "external_id": null,
    "name": "María González",
    "sex": "female",
    "date_of_birth": "1990-03-15"
  },
  "report": {
    "laboratory_name": "Laboratorio Central",
    "report_date": "2024-11-15",
    "accession_number": "REP-2024-001"
  },
  "observation_count": 18,
  "observations": [
    {
      "observation_id": "a1b2c3d4-...",
      "panel_raw": "Biometría Hemática",
      "test_name_raw": "Hemoglobina",
      "test_name_normalized": "Hemoglobina",
      "loinc_code": "718-7",
      "value": 10.2,
      "value_type": "numeric",
      "unit_raw": "g/dl",
      "unit_ucum": "g/dL",
      "reference_range_raw": "12.0 - 16.0",
      "reference_range": {
        "low": 12.0,
        "high": 16.0,
        "unit_ucum": "g/dL"
      },
      "interpretation": "low",
      "delta_from_range": {
        "direction": "below",
        "absolute": 1.8,
        "relative_to_lower": 0.15,
        "unit_ucum": "g/dL"
      },
      "specimen": "Sangre",
      "page": 1,
      "confidence": 0.97
    }
  ],
  "requires_manual_review": false,
  "warnings": [],
  "confidence": 0.91
}
```

#### Campos clave de cada observación

| Campo | Tipo | Descripción |
|---|---|---|
| `test_name_raw` | string | Nombre exactamente como aparece en el PDF |
| `test_name_normalized` | string | Nombre canónico normalizado |
| `loinc_code` | string \| null | Código LOINC si fue mapeado, null si no |
| `value` | number \| string | Valor medido (numérico o texto como "Negativo") |
| `unit_raw` | string \| null | Unidad exacta del PDF |
| `unit_ucum` | string \| null | Unidad normalizada UCUM |
| `reference_range` | object \| null | `{low, high, unit_ucum}` — null si no parseable |
| `interpretation` | `"low"` \| `"normal"` \| `"high"` \| null | null si el valor no es numérico |
| `delta_from_range` | object \| null | `{direction, absolute, relative_to_lower/upper, unit_ucum}` |

---

## 5. Endpoint 2 — Inferencia diagnóstica

```http
POST https://nahui-ai.ddns.net/diagnostics/diagnose
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Body mínimo requerido

```json
{
  "patient": {
    "age": 34,
    "sex": "female"
  },
  "lab_series": [
    {
      "report_date": "2024-11-15",
      "results": [
        {
          "loinc_code": "718-7",
          "test_name": "Hemoglobin",
          "value": 10.2,
          "unit": "g/dL",
          "interpretation": "low",
          "reference_range": "12.0-16.0"
        }
      ]
    }
  ],
  "clinical_diagnosis": "Fatiga y artralgias, descartar autoinmune",
  "language": "es"
}
```

### Response

```json
{
  "confidence": "moderate",
  "autoimmune_flags": [
    {
      "condition": "Lupus Eritematoso Sistémico (LES)",
      "likelihood": "moderate",
      "supporting_findings": ["ANA positivo", "Anemia hemolítica"],
      "missing_workup": ["Anti-dsDNA", "Complemento C3/C4"]
    }
  ],
  "differential": [
    "LES probable",
    "Síndrome antifosfolípido",
    "Artritis reumatoide"
  ],
  "recommended_followup": [
    "Solicitar anti-dsDNA y complemento",
    "Derivar a reumatología"
  ],
  "reasoning": "La combinación de anemia, artralgias y ANA positivo...",
  "disclaimer": "Este resultado es de apoyo diagnóstico y no reemplaza el criterio clínico."
}
```

---

## 6. Integración con SDK Python (recomendado)

El SDK gestiona tokens automáticamente — no necesitas manejar renovación.

### Instalación

```bash
# Descargar el SDK (requiere login previo en el navegador)
curl -H "Authorization: Bearer <token>" \
  https://nahui-ai.ddns.net/auth/ui/clinical_ai_client.py \
  -o clinical_ai_client.py

pip install requests
```

### Uso

```python
from clinical_ai_client import ClinicalAIClient, PatientContext

client = ClinicalAIClient(
    base_url="https://nahui-ai.ddns.net",
    client_id="<CLIENT_ID>",
    client_secret="<CLIENT_SECRET>",
)

# 1. Parsear PDF
report = client.parse_lab_report("hemograma_maria.pdf", language="es")

print(f"Paciente: {report.patient.name}")
print(f"Analitos: {report.observation_count}")
for obs in report.observations:
    print(f"  {obs.test_name_normalized}: {obs.value} {obs.unit_ucum} [{obs.interpretation}]")

# 2. Diagnóstico
result = client.diagnose(
    lab_report=report,
    patient=PatientContext(age=34, sex="female"),
    clinical_diagnosis="Fatiga y artralgias, descartar autoinmune",
    language="es",
)

print(f"\nConfianza: {result.confidence}")
print(f"Diferencial: {result.differential}")
for flag in result.autoimmune_flags:
    print(f"  {flag.condition} — {flag.likelihood}")
```

### Flujo automático del token

```
Primera llamada → solicita token via /auth/token
Token válido por 60 min → se reutiliza automáticamente
Expira 60s antes → SDK renueva sin intervención
Si el servidor rechaza el token → reintenta una vez automáticamente
```

---

## 7. Códigos de error relevantes

| HTTP | Significado | Acción |
|---|---|---|
| 400 | Consulta rechazada por guardrail (no clínica) | Reformular la pregunta con términos clínicos |
| 401 | Token inválido o expirado | Renovar token |
| 413 | PDF demasiado grande (>20MB) | Comprimir o dividir el PDF |
| 422 | Body mal formado | Revisar el JSON enviado contra el Swagger |
| 429 | Límite de consultas alcanzado | Esperar 60s (`Retry-After: 60`) |
| 502 | Error en el backend de inferencia | Reintentar en 30s |

---

## 8. Límites de uso

| Endpoint | Límite |
|---|---|
| `/auth/token` | 10 requests/min por IP |
| `/documents/labs/parse` | 10 requests/min por cliente |
| `/diagnostics/diagnose` | 20 requests/min por cliente |

---

## 9. Checklist de integración para Codex

- [ ] Recibir `client_id` y `client_secret` del administrador
- [ ] Descargar `clinical_ai_client.py` o revisar el Swagger en `https://nahui-ai.ddns.net/auth/ui/api-docs.html`
- [ ] Instalar `requests` (`pip install requests`)
- [ ] Instanciar `ClinicalAIClient` con las credenciales
- [ ] Probar `parse_lab_report()` con un PDF de prueba
- [ ] Probar `diagnose()` con los resultados parseados
- [ ] Usar `test_name_normalized` (no `test_name_raw`) como nombre de display
- [ ] Usar `unit_ucum` (no `unit_raw`) para unidades normalizadas
- [ ] Manejar 429 con retry usando el campo `retry_after_seconds` del response o el header `Retry-After`
