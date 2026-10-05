"""Genera los 150 casos (10 plantillas x 15) con paciente, paneles y ground truth.

Reproducible: semilla fija. No usa datos de pacientes reales bajo ninguna
circunstancia -- todo se sortea de bancos de nombres/valores sintéticos.
"""
import random
from datetime import date, timedelta

from analyte_library import (
    AUTOIMMUNE_ANALYTES,
    AUTOIMMUNE_PANEL,
    NUMERIC_PANELS,
    gen_autoimmune_value,
    gen_numeric_value,
)

SEED = 42

TEMPLATES = [
    "template_1_simple",
    "template_2_letterhead",
    "template_3_panel_grid",
    "template_4_abbreviated",
    "template_5_scanned",
    "template_6_bilingual",
    "template_7_stamped",
    "template_8_narrative",
    "template_9_portal",
    "template_10_multipage",
]
CASES_PER_TEMPLATE = 15

FIRST_NAMES_F = [
    "María Elena", "Ana Sofía", "Guadalupe", "Fernanda", "Alejandra",
    "Patricia", "Daniela", "Verónica", "Claudia", "Mónica",
]
FIRST_NAMES_M = [
    "José Luis", "Carlos Alberto", "Roberto", "Miguel Ángel", "Ricardo",
    "Jorge", "Francisco", "Eduardo", "Sergio", "Arturo",
]
LAST_NAMES = [
    "Cordero Vázquez", "Hernández Ruiz", "García Mendoza", "López Torres",
    "Martínez Soto", "Ramírez Ortiz", "Flores Aguilar", "Gómez Reyes",
    "Sánchez Peña", "Díaz Cabrera", "Rojas Medina", "Castillo Nava",
]
DOCTORS = [
    "Dra. Fernanda Ríos Landa", "Dr. Alberto Núñez Casillas",
    "Dra. Silvia Rangel Ochoa", "Dr. Iván Cortés Beltrán",
    "Dra. Paulina Zamudio Elías",
]

PANEL_NAMES = list(NUMERIC_PANELS.keys())


def _rand_status(weights=(0.65, 0.20, 0.15)):
    return random.choices(["N", "H", "L"], weights=weights, k=1)[0]


def _messify_range(rango_ref: str) -> str:
    if rango_ref == "Negativo":
        return "Neg"
    if rango_ref.startswith("<"):
        return f"Normal {rango_ref}"
    if "-" in rango_ref:
        return f"N: {rango_ref}"
    return rango_ref


def _build_analyte(nombre, abrev, loinc, unidad, rango_ref, valor, bandera):
    return {
        "nombre": nombre,
        "abrev": abrev,
        "loinc": loinc,
        "valor": valor,
        "unidad": unidad,
        "rango_ref": rango_ref,
        "bandera": bandera,
        "valor_unidad_messy": f"{valor}{unidad}" if unidad else valor,
        "rango_messy": _messify_range(rango_ref),
        "occluded": False,
    }


def _gen_patient(rng_id: int) -> dict:
    sexo = random.choice(["F", "M"])
    first = random.choice(FIRST_NAMES_F if sexo == "F" else FIRST_NAMES_M)
    nombre = f"{first} {random.choice(LAST_NAMES)}"
    edad = random.randint(18, 82)
    initials = "".join(w[0] for w in nombre.split())[:3].upper()
    pid = f"{initials}-{random.randint(700101,991231)}-{random.choice('ABCDEFGHJKLMNPQRSTVWXYZ')}{random.randint(1,9)}"
    return {"nombre": nombre, "edad": edad, "sexo": sexo, "id": pid}


def generate_cases() -> list[dict]:
    random.seed(SEED)
    base_date = date(2026, 3, 1)
    cases = []
    report_num = 1

    for template in TEMPLATES:
        for _ in range(CASES_PER_TEMPLATE):
            report_id = f"labtest_{report_num:03d}"
            report_num += 1

            # 2-4 paneles numéricos + 45% de probabilidad de panel autoinmune
            n_panels = random.randint(2, 4)
            chosen_panel_names = random.sample(PANEL_NAMES, n_panels)
            include_autoimmune = random.random() < 0.45

            panels = []
            expected = []
            for i, pname in enumerate(chosen_panel_names):
                analytes_pool = NUMERIC_PANELS[pname]
                k = random.randint(3, len(analytes_pool)) if i == 0 else random.randint(2, len(analytes_pool))
                chosen = random.sample(analytes_pool, k)
                panel_analytes = []
                for j, (nombre, abrev, loinc, unidad, low, high, dec) in enumerate(chosen):
                    status = _rand_status()
                    valor, bandera = gen_numeric_value(low, high, dec, status)
                    rango_ref = f"{low}-{high}" if dec else f"{int(low)}-{int(high)}"
                    a = _build_analyte(nombre, abrev, loinc, unidad, rango_ref, valor, bandera)
                    # Oclusión determinística: plantilla 7, primer panel, primeras 3 filas.
                    if template == "template_7_stamped" and i == 0 and j < 3:
                        a["occluded"] = True
                    panel_analytes.append(a)
                    expected.append({"panel": pname, **a})
                panels.append({"name": pname, "analytes": panel_analytes})

            if include_autoimmune:
                k = random.randint(3, len(AUTOIMMUNE_ANALYTES))
                chosen = random.sample(AUTOIMMUNE_ANALYTES, k)
                panel_analytes = []
                for entry in chosen:
                    nombre, abrev, loinc, unidad, valor_neg, rango_ref, pos_fn = entry
                    status = random.choices(["N", "H"], weights=(0.75, 0.25), k=1)[0]
                    valor, bandera = gen_autoimmune_value(entry, status)
                    a = _build_analyte(nombre, abrev, loinc, unidad, rango_ref, valor, bandera)
                    panel_analytes.append(a)
                    expected.append({"panel": AUTOIMMUNE_PANEL, **a})
                panels.append({"name": AUTOIMMUNE_PANEL, "analytes": panel_analytes})

            fecha_toma = base_date + timedelta(days=random.randint(0, 180))
            fecha_reporte = fecha_toma + timedelta(days=1)

            report = {
                "lab_name": "Laboratorio Clínico Nahui",
                "lab_address": "Av. Insurgentes Sur 1234, Col. Del Valle, CDMX",
                "lab_phone": "55-1234-5678",
                "folio": f"NHI-2026-{random.randint(10000,99999)}",
                "fecha_toma": fecha_toma.isoformat(),
                "fecha_reporte": fecha_reporte.isoformat(),
                "medico_solicitante": random.choice(DOCTORS),
                "patient": _gen_patient(report_num),
                "panels": panels,
            }

            cases.append({
                "report_id": report_id,
                "template": template,
                "report": report,
                "expected": expected,
            })

    return cases


if __name__ == "__main__":
    cases = generate_cases()
    print(f"generated {len(cases)} cases")
    sizes = [len(c["expected"]) for c in cases]
    print(f"analytes per report: min={min(sizes)} max={max(sizes)} avg={sum(sizes)/len(sizes):.1f}")
