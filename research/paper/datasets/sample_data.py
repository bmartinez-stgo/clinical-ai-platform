"""Datos de ejemplo compartidos por las 4 plantillas de reporte de laboratorio.

Un mismo caso clínico (paciente + resultados) representado de 4 formas visuales
distintas, para comparar cómo cada plantilla codifica la misma información.

Cada analito trae, además de sus campos canónicos (los del ground truth),
variantes "messy" (abrev, unidad/valor pegados, rango como texto libre) que
solo usa la plantilla 4 (estrés del parser).
"""

REPORT = {
    "lab_name": "Laboratorio Clínico Nahui",
    "lab_address": "Av. Insurgentes Sur 1234, Col. Del Valle, CDMX",
    "lab_phone": "55-1234-5678",
    "folio": "NHI-2026-08341",
    "fecha_toma": "2026-08-14",
    "fecha_reporte": "2026-08-15",
    "medico_solicitante": "Dra. Fernanda Ríos Landa",
    "patient": {
        "nombre": "María Elena Cordero Vázquez",
        "edad": 34,
        "sexo": "F",
        "id": "MCV-880213-MZ7",
    },
    "panels": [
        {
            "name": "Biometría Hemática",
            "analytes": [
                {"nombre": "Hemoglobina", "abrev": "HGB", "loinc": "718-7",
                 "valor": "10.8", "unidad": "g/dL", "rango_ref": "12.0-16.0",
                 "valor_unidad_messy": "10.8g/dL", "rango_messy": "N: 12-16",
                 "bandera": "L"},
                {"nombre": "Hematocrito", "abrev": "HCT", "loinc": "4544-3",
                 "valor": "33.1", "unidad": "%", "rango_ref": "36.0-46.0",
                 "valor_unidad_messy": "33.1%", "rango_messy": "N: 36-46",
                 "bandera": "L"},
                {"nombre": "Leucocitos", "abrev": "WBC", "loinc": "6690-2",
                 "valor": "4.1", "unidad": "x10^3/uL", "rango_ref": "4.5-11.0",
                 "valor_unidad_messy": "4.1 x10e3/ul", "rango_messy": "4.5 - 11.0",
                 "bandera": "L"},
                {"nombre": "Plaquetas", "abrev": "PLT", "loinc": "777-3",
                 "valor": "142", "unidad": "x10^3/uL", "rango_ref": "150-450",
                 "valor_unidad_messy": "142x10e3/ul", "rango_messy": "150-450",
                 "bandera": "L"},
            ],
        },
        {
            "name": "Química Sanguínea",
            "analytes": [
                {"nombre": "Glucosa", "abrev": "GLU", "loinc": "2345-7",
                 "valor": "91", "unidad": "mg/dL", "rango_ref": "70-100",
                 "valor_unidad_messy": "91mg/dl", "rango_messy": "Normal 70-100",
                 "bandera": ""},
                {"nombre": "Creatinina", "abrev": "CREA", "loinc": "2160-0",
                 "valor": "0.7", "unidad": "mg/dL", "rango_ref": "0.6-1.1",
                 "valor_unidad_messy": "0.7mg/dl", "rango_messy": "0.6-1.1",
                 "bandera": ""},
            ],
        },
        {
            "name": "Perfil Tiroideo",
            "analytes": [
                {"nombre": "TSH", "abrev": "TSH", "loinc": "3016-3",
                 "valor": "2.1", "unidad": "uIU/mL", "rango_ref": "0.4-4.5",
                 "valor_unidad_messy": "2.1uIU/ml", "rango_messy": "0.4 - 4.5",
                 "bandera": ""},
            ],
        },
        {
            "name": "Panel Serológico Autoinmune",
            "analytes": [
                {"nombre": "Anticuerpos Antinucleares (ANA)", "abrev": "ANA",
                 "loinc": "5048-4", "valor": "Positivo 1:320 patrón moteado",
                 "unidad": "", "rango_ref": "Negativo",
                 "valor_unidad_messy": "POS 1:320 moteado", "rango_messy": "Neg",
                 "bandera": "H"},
                {"nombre": "Anti-DNA de doble cadena", "abrev": "Anti-dsDNA",
                 "loinc": "14169-3", "valor": "38", "unidad": "UI/mL",
                 "rango_ref": "<30", "valor_unidad_messy": "38UI/ml",
                 "rango_messy": "Normal <30", "bandera": "H"},
                {"nombre": "Anti-SSA (Ro)", "abrev": "SSA", "loinc": "24081-4",
                 "valor": "Negativo", "unidad": "", "rango_ref": "Negativo",
                 "valor_unidad_messy": "NEG", "rango_messy": "Neg", "bandera": ""},
                {"nombre": "Factor Reumatoide", "abrev": "FR", "loinc": "11572-5",
                 "valor": "9", "unidad": "UI/mL", "rango_ref": "<14",
                 "valor_unidad_messy": "9UI/ml", "rango_messy": "Normal <14",
                 "bandera": ""},
                {"nombre": "Anticuerpos Anticardiolipina IgG", "abrev": "aCL-IgG",
                 "loinc": "16097-9", "valor": "22", "unidad": "GPL-U/mL",
                 "rango_ref": "<15", "valor_unidad_messy": "22GPL",
                 "rango_messy": "Normal <15", "bandera": "H"},
            ],
        },
    ],
}
