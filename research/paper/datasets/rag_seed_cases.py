"""Casos reales (PMC/Europe PMC, acceso abierto) para sembrar el store de
`clinical-rag`. Distintos a los 20 de `clinical_cases.py` (Estudio 2) a
propósito -- sembrar con los mismos contaminaría ese benchmark si se vuelve
a correr más adelante.

Formato: StoreCaseRequest de clinical-rag (patient, lab_snapshot,
validated_diagnosis, differential, doctor_notes, approved_by).
`approved_by` queda como "literatura-pmc" para dejar explícito que no es
un caso real de un paciente de esta plataforma, sino literatura curada --
si algún día se audita el store, debe ser trivial distinguir origen.
"""

SEED_CASES = [
    {
        "citation": "Samha R, Ghaddar SA, Raya M, Alhadi SA. Systemic sclerosis sine scleroderma "
                    "with atypical clinical course: a rare case report. Ann Med Surg. "
                    "2023;85(11):5656-5661. doi:10.1097/MS9.0000000000001266. PMCID: PMC10617812.",
        "request": {
            "patient": {"age": 58, "sex": "female"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "ANA", "value": "1:320", "interpretation": "high"},
                    {"test_name": "Anti-centromere (ACA)", "value": 94.8, "unit": "AU/ml", "interpretation": "high"},
                    {"test_name": "Anti-Scl-70", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Factor Reumatoide", "value": "Negativo", "interpretation": "normal"},
                ],
            },
            "validated_diagnosis": "Esclerosis sistémica sine esclerodermia",
            "differential": ["Esclerosis sistémica sine esclerodermia", "Hipertensión pulmonar idiopática", "Enfermedad mixta del tejido conectivo"],
            "doctor_notes": "Disnea progresiva de 3 años, hipertensión pulmonar, fenómeno de Raynaud, sin engrosamiento cutáneo evidente. ACA positivo confirma esclerosis sistémica pese a ausencia de esclerodermia cutánea.",
            "approved_by": "literatura-pmc",
        },
    },
    {
        "citation": "Aterini L, Gallo M, Vadalà B, Aterini S. Thrombotic Microangiopathy and "
                    "Multiple Organ Failure in Scleroderma Renal Crisis: A Case Report. Cureus. "
                    "2023;15(8):e44322. doi:10.7759/cureus.44322. PMCID: PMC10538352.",
        "request": {
            "patient": {"age": 65, "sex": "female"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "ANA", "value": "1:1280", "interpretation": "high"},
                    {"test_name": "Anti-centromere", "value": ">240", "unit": "IU/ml", "interpretation": "high"},
                    {"test_name": "Anti-Scl-70 (anti-topoisomerasa I)", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Anti-RNA Polimerasa III", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Creatinina", "value": 5.5, "unit": "mg/dL", "interpretation": "critical"},
                ],
            },
            "validated_diagnosis": "Crisis renal esclerodérmica con microangiopatía trombótica",
            "differential": ["Crisis renal esclerodérmica", "Síndrome urémico hemolítico atípico", "Síndrome antifosfolípido catastrófico"],
            "doctor_notes": "Esclerosis sistémica conocida de 4 años, descompensación aguda con taponamiento pericárdico, pancreatitis aguda y evento isquémico cerebral. Doble positividad ACA+anti-Scl-70, infrecuente.",
            "approved_by": "literatura-pmc",
        },
    },
    {
        "citation": "Zhang Y, Dai QD, Wang JA, Xu LP, Chen Q, Jin YZ. Dynamically changing "
                    "antineutrophil cytoplasmic antibodies in granulomatosis with polyangiitis: "
                    "A case report. World J Clin Cases. 2024;12(16):2881-2886. "
                    "doi:10.12998/wjcc.v12.i16.2881. PMCID: PMC11185331.",
        "request": {
            "patient": {"age": 52, "sex": "male"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "c-ANCA", "value": "Positivo (tras recaída, negativo al inicio)", "interpretation": "high"},
                    {"test_name": "PR3", "value": 100.8, "unit": "RU/mL", "interpretation": "high"},
                    {"test_name": "p-ANCA", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "PCR ultrasensible", "value": 55, "unit": "mg/L", "interpretation": "high"},
                ],
            },
            "validated_diagnosis": "Granulomatosis con poliangeítis (GPA) con glomerulonefritis activa",
            "differential": ["Granulomatosis con poliangeítis", "Vasculitis ANCA seronegativa", "Infección crónica de oído medio"],
            "doctor_notes": "Congestión nasal crónica, acúfenos e hipoacusia de 8 meses, fiebre recurrente. ANCA inicialmente negativo, se positiviza en recaída a los 3 meses -- la serología negativa inicial no descarta GPA.",
            "approved_by": "literatura-pmc",
        },
    },
    {
        "citation": "Martini WA, Querin LB, Hodgson NR, Rappaport D. Acute Renal Failure and "
                    "Generalized Weakness in a 75-Year-Old Male With Pauci-Immune Necrotizing "
                    "ANCA-Associated Vasculitis: A Case Report. Cureus. 2024;16(9):e68398. "
                    "doi:10.7759/cureus.68398. PMCID: PMC11444712.",
        "request": {
            "patient": {"age": 75, "sex": "male"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "p-ANCA", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "MPO", "value": ">8.0", "unit": "U", "ref_high": 0.4, "interpretation": "critical"},
                    {"test_name": "c-ANCA / PR3", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Creatinina", "value": 5.5, "unit": "mg/dL", "interpretation": "critical"},
                ],
            },
            "validated_diagnosis": "Vasculitis necrotizante pauci-inmune asociada a ANCA (anti-MPO)",
            "differential": ["Vasculitis ANCA (MPO)", "Glomerulonefritis rápidamente progresiva de otra causa", "Sepsis con falla renal"],
            "doctor_notes": "Debilidad generalizada e insuficiencia renal aguda en adulto mayor, confirmado por biopsia renal al día 6. p-ANCA/MPO positivo, c-ANCA/PR3 negativo.",
            "approved_by": "literatura-pmc",
        },
    },
    {
        "citation": "Zulfiqar B, Aksionav P, Bittar M, Chapman C. A Case of Anti-Jo-1 Myositis "
                    "with Unique Biopsy Findings. Case Rep Rheumatol. 2022. "
                    "doi:10.1155/2022/9096643. PMCID: PMC9192263.",
        "request": {
            "patient": {"age": 53, "sex": "female"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "Anti-Jo-1", "value": 166, "unit": "U", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "ANA", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Ro-52", "value": 78, "unit": "U", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "CPK", "value": 3261, "unit": "U/L", "ref_high": 168, "interpretation": "critical"},
                    {"test_name": "Factor Reumatoide, Anti-CCP, ANCA", "value": "Negativo", "interpretation": "normal"},
                ],
            },
            "validated_diagnosis": "Síndrome antisintetasa (miositis asociada a anti-Jo-1)",
            "differential": ["Síndrome antisintetasa", "Polimiositis idiopática", "Miopatía necrotizante inmunomediada"],
            "doctor_notes": "Debilidad muscular, edema de miembros inferiores y sensibilidad en manos. CPK muy elevada, anti-Jo-1 fuertemente positivo -- patrón clásico de síndrome antisintetasa.",
            "approved_by": "literatura-pmc",
        },
    },
    {
        "citation": "Khan AM, Ahmad F Jr, Rehman U, Jindal H, Harimohan H. A Clinical Case of "
                    "Polymyositis Complicated by Antisynthetase Syndrome. Cureus. 2021;13(1):e12737. "
                    "doi:10.7759/cureus.12737. PMCID: PMC7883527.",
        "request": {
            "patient": {"age": 18, "sex": "female"},
            "lab_snapshot": {
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "CPK", "value": 10215, "unit": "U/L", "ref_high": 145, "interpretation": "critical"},
                    {"test_name": "ANA", "value": "1:3200", "interpretation": "high"},
                    {"test_name": "Anti-Jo-1", "value": "3+ positivo", "interpretation": "high"},
                    {"test_name": "Ro-52", "value": "2+ positivo", "interpretation": "high"},
                    {"test_name": "Mi-2β", "value": "2+ positivo", "interpretation": "high"},
                ],
            },
            "validated_diagnosis": "Polimiositis complicada con síndrome antisintetasa",
            "differential": ["Polimiositis con síndrome antisintetasa", "Dermatomiositis", "Rabdomiólisis de otra causa"],
            "doctor_notes": "Paciente joven con debilidad muscular proximal de 2.5 meses tras cuadro febril. CPK marcadamente elevada, panel de miositis positivo para anti-Jo-1, Ro-52 y Mi-2β.",
            "approved_by": "literatura-pmc",
        },
    },
]

if __name__ == "__main__":
    print(f"{len(SEED_CASES)} casos de siembra cargados")
