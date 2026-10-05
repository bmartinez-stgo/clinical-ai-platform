"""Banco de analitos por panel: rango normal, unidad, LOINC y generador de valor.

Cada entrada define cómo generar un valor plausible en estado normal/alto/bajo.
Los analitos cualitativos (serologías) usan `qualitative=True` y no tienen
generador numérico — su valor lo fija directamente `case_generator.py`.
"""
import random

# (nombre, abrev, loinc, unidad, rango_low, rango_high, decimales)
NUMERIC_PANELS = {
    "Biometría Hemática": [
        ("Hemoglobina", "HGB", "718-7", "g/dL", 12.0, 16.0, 1),
        ("Hematocrito", "HCT", "4544-3", "%", 36.0, 46.0, 1),
        ("Leucocitos", "WBC", "6690-2", "x10^3/uL", 4.5, 11.0, 1),
        ("Plaquetas", "PLT", "777-3", "x10^3/uL", 150, 450, 0),
        ("Eritrocitos", "RBC", "789-8", "x10^6/uL", 4.2, 5.4, 2),
        ("VCM", "MCV", "787-2", "fL", 80, 100, 1),
    ],
    "Química Sanguínea": [
        ("Glucosa", "GLU", "2345-7", "mg/dL", 70, 100, 0),
        ("Creatinina", "CREA", "2160-0", "mg/dL", 0.6, 1.1, 1),
        ("Urea", "BUN", "3094-0", "mg/dL", 7, 20, 0),
        ("Ácido Úrico", "URIC", "3084-1", "mg/dL", 3.5, 7.2, 1),
        ("Sodio", "NA", "2951-2", "mmol/L", 136, 145, 0),
        ("Potasio", "K", "2823-3", "mmol/L", 3.5, 5.1, 1),
    ],
    "Perfil de Lípidos": [
        ("Colesterol Total", "COL-T", "2093-3", "mg/dL", 125, 200, 0),
        ("Triglicéridos", "TG", "2571-8", "mg/dL", 35, 150, 0),
        ("HDL", "HDL", "2085-9", "mg/dL", 40, 60, 0),
        ("LDL", "LDL", "13457-7", "mg/dL", 50, 130, 0),
    ],
    "Perfil Tiroideo": [
        ("TSH", "TSH", "3016-3", "uIU/mL", 0.4, 4.5, 1),
        ("T4 Libre", "FT4", "3024-7", "ng/dL", 0.8, 1.8, 1),
        ("T3 Total", "T3", "3053-6", "ng/dL", 80, 200, 0),
    ],
    "Pruebas de Función Hepática": [
        ("ALT (TGP)", "ALT", "1742-6", "U/L", 7, 40, 0),
        ("AST (TGO)", "AST", "1920-8", "U/L", 8, 40, 0),
        ("Fosfatasa Alcalina", "ALP", "6768-6", "U/L", 44, 147, 0),
        ("Bilirrubina Total", "TBIL", "1975-2", "mg/dL", 0.2, 1.2, 1),
    ],
}

# Serologías: cualitativas o con corte único. valor_pos/valor_neg son strings
# ya formateados; el "positivo" siempre cuenta como bandera H.
AUTOIMMUNE_PANEL = "Panel Serológico Autoinmune"
AUTOIMMUNE_ANALYTES = [
    # (nombre, abrev, loinc, unidad, valor_negativo, rango_ref, valor_positivo_fn)
    ("Anticuerpos Antinucleares (ANA)", "ANA", "5048-4", "", "Negativo", "Negativo",
     lambda: f"Positivo 1:{random.choice([160, 320, 640])} patrón {random.choice(['moteado', 'homogéneo', 'nucleolar'])}"),
    ("Anti-DNA de doble cadena", "Anti-dsDNA", "14169-3", "UI/mL", None, "<30",
     lambda: str(random.randint(31, 90))),
    ("Anti-SSA (Ro)", "SSA", "24081-4", "", "Negativo", "Negativo",
     lambda: "Positivo"),
    ("Anti-SSB (La)", "SSB", "24082-2", "", "Negativo", "Negativo",
     lambda: "Positivo"),
    ("Factor Reumatoide", "FR", "11572-5", "UI/mL", None, "<14",
     lambda: str(random.randint(15, 60))),
    ("Anti-CCP", "CCP", "34505-9", "U/mL", None, "<20",
     lambda: str(random.randint(21, 100))),
    ("Anticuerpos Anticardiolipina IgG", "aCL-IgG", "16097-9", "GPL-U/mL", None, "<15",
     lambda: str(random.randint(16, 60))),
    ("Anticoagulante Lúpico", "LA", "22599-7", "", "Negativo", "Negativo",
     lambda: "Positivo"),
]

# Valores "normales" por defecto para las cualitativas cuando no están alteradas.
_NEG_NUMERIC_DEFAULT = {
    "Anti-DNA de doble cadena": "18",
    "Factor Reumatoide": "8",
    "Anti-CCP": "9",
    "Anticuerpos Anticardiolipina IgG": "6",
}


def gen_numeric_value(low: float, high: float, decimals: int, status: str):
    """status: 'N' (normal), 'H' (alto), 'L' (bajo) -> (valor_str, bandera)."""
    span = high - low
    if status == "N":
        v = random.uniform(low, high)
        bandera = ""
    elif status == "H":
        v = high + random.uniform(0.05, 0.6) * span
        bandera = "H"
    else:  # "L"
        v = low - random.uniform(0.05, 0.6) * span
        v = max(v, 0)
        bandera = "L"
    if decimals == 0:
        return str(round(v)), bandera
    return f"{v:.{decimals}f}", bandera


def gen_autoimmune_value(entry, status: str):
    """status: 'N' o 'H'. Devuelve (valor_str, bandera)."""
    nombre, abrev, loinc, unidad, valor_neg, rango_ref, pos_fn = entry
    if status == "H":
        return pos_fn(), "H"
    if valor_neg is not None:
        return valor_neg, ""
    return _NEG_NUMERIC_DEFAULT.get(nombre, "10"), ""
