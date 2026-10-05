"""20 casos clínicos reales, publicados en PMC/Europe PMC (acceso abierto),
usados como ground truth del Estudio 2 (diagnóstico asistido).

Cada caso trae su cita completa (para el apéndice del manuscrito) y el
diagnóstico final CONFIRMADO en el artículo original -- este campo nunca se
envía a `ai-diagnostic`, se usa solo para calificar después. El campo
`request` es el payload real que se envía a POST /diagnostics/diagnose,
construido únicamente a partir de los hallazgos de laboratorio/serología
reportados en el texto del artículo (nunca se inventa ningún valor).

`clinical_diagnosis` dentro de `request` es el motivo de consulta/sospecha
inicial -- lo que un médico real escribiría al pedir el estudio -- nunca el
diagnóstico final, para no contaminar la prueba.
"""

CASES = [
    # ---------------------------------------------------------------- SLE
    {
        "case_id": "case_01_sle",
        "citation": "Nanneboyina KS, Avila J. A Case of a 31-Year-Old Female Patient With "
                    "Systemic Lupus Erythematosus Presenting With Lupus-Associated Pleural "
                    "Effusions and Newly Diagnosed Lupus Nephritis. Cureus. 2026. "
                    "doi:10.7759/cureus.104625. PMCID: PMC12956268.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico con nefritis lúpica (clase IV+V) y derrame pleural asociado",
        "request": {
            "patient": {"external_id": "case-01", "age": 31, "sex": "female"},
            "history": {"comorbidities": ["lupus eritematoso sistémico (diagnóstico previo)"]},
            "physical_findings": {"free_text": "Disnea, dolor pleurítico, edema"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "Positivo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": ">1:2560", "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 47, "unit": "mg/dL", "ref_low": 88, "ref_high": 165, "interpretation": "low"},
                    {"test_name": "Complemento C4", "value": 8, "unit": "mg/dL", "ref_low": 14, "ref_high": 44, "interpretation": "low"},
                    {"test_name": "Leucocitos", "value": 3.7, "unit": "x10^3/uL", "ref_low": 3.8, "ref_high": 11.0, "interpretation": "low"},
                    {"test_name": "Hemoglobina", "value": 11.8, "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "interpretation": "low"},
                    {"test_name": "Albúmina", "value": 1.8, "unit": "g/dL", "ref_low": 3.5, "ref_high": 5.7, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Disnea y dolor pleurítico en paciente con antecedente de enfermedad autoinmune, descartar actividad renal",
            "language": "es",
        },
    },
    {
        "case_id": "case_02_sle",
        "citation": "Alesaeidi S, Daraei M, Salami Khanshan A, Zainaldain H. A multisystem "
                    "syndrome compatible with systemic lupus erythematosus: Case report and "
                    "review of literature. Caspian J Intern Med. 2021;12(Suppl 2):S482-S486. "
                    "PMCID: PMC8559634.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico seronegativo (ANA inicial negativo) con nefritis lúpica clase III",
        "request": {
            "patient": {"external_id": "case-02", "age": 27, "sex": "female"},
            "history": {"comorbidities": ["talasemia menor"]},
            "physical_findings": {"free_text": "Dolor abdominal agudo, poliserositis"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "Positivo 1:320", "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 77, "unit": "ng/dL", "ref_low": 90, "ref_high": 190, "interpretation": "low"},
                    {"test_name": "Plaquetas", "value": 50, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "low"},
                    {"test_name": "Creatinina", "value": 4.3, "unit": "mg/dL", "ref_low": 0.6, "ref_high": 1.1, "interpretation": "high"},
                    {"test_name": "Proteinuria", "value": "4+", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Dolor abdominal agudo, anemia hemolítica y lesión renal aguda de origen a estudiar",
            "language": "es",
        },
    },
    {
        "case_id": "case_03_sle",
        "citation": "Del Porto F, Tatarelli C, Di Napoli A, Proietta M. Systemic lupus "
                    "erythematosus and myelofibrosis: A case report and revision of literature. "
                    "Leukemia Research Reports. 2018;9:58-64. doi:10.1016/j.lrr.2018.04.004. "
                    "PMCID: PMC5909024.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico complicado con mielofibrosis autoinmune",
        "request": {
            "patient": {"external_id": "case-03", "age": 43, "sex": "female"},
            "physical_findings": {"free_text": "Anemia severa, trombocitopenia progresiva"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:640 homogéneo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "1:20 positivo", "interpretation": "high"},
                    {"test_name": "Coombs directo", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 78, "unit": "mg/dL", "ref_low": 90, "ref_high": 180, "interpretation": "low"},
                    {"test_name": "Complemento C4", "value": 9, "unit": "mg/dL", "ref_low": 10, "ref_high": 40, "interpretation": "low"},
                    {"test_name": "Hemoglobina", "value": 7.4, "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "interpretation": "low"},
                    {"test_name": "Plaquetas", "value": 6, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Anemia severa y trombocitopenia refractaria, estudio hematológico y autoinmune",
            "language": "es",
        },
    },
    {
        "case_id": "case_04_sle",
        "citation": "Del Río Zanatta H, Zambrano Zambrano A, Belmont Nava P, Puntos Guízar CL, "
                    "Martinez Salazar J. Comprehensive Evaluation of Neuropsychiatric and "
                    "Mucocutaneous Manifestations in the Diagnosis of Systemic Lupus "
                    "Erythematosus. Cureus. 2023;15(10):e47380. doi:10.7759/cureus.47380. "
                    "PMCID: PMC10657573.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico con manifestaciones neuropsiquiátricas y mucocutáneas",
        "request": {
            "patient": {"external_id": "case-04", "age": 31, "sex": "female"},
            "physical_findings": {"free_text": "Manifestaciones mucocutáneas y síntomas neuropsiquiátricos"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "+++ 1:80, patrón DNA doble cadena", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": 995.19, "unit": "UI/mL", "ref_high": 200, "interpretation": "high"},
                    {"test_name": "Anti-RNP", "value": 67.9, "ref_high": 20, "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 38.21, "unit": "mg/dL", "ref_low": 90, "ref_high": 180, "interpretation": "low"},
                    {"test_name": "Complemento C4", "value": 2.88, "unit": "mg/dL", "ref_low": 10, "ref_high": 40, "interpretation": "low"},
                    {"test_name": "Anti-Sm", "value": 16.4, "ref_high": 20, "interpretation": "normal"},
                    {"test_name": "Hemoglobina", "value": 10.1, "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Lesiones mucocutáneas y alteraciones neuropsiquiátricas de novo, descartar enfermedad del tejido conectivo",
            "language": "es",
        },
    },
    # ---------------------------------------------------------------- APS
    {
        "case_id": "case_05_aps",
        "citation": "Mazzoccoli C, Comitangelo D, D'Introno A, Mastropierro V, Sabbà C, "
                    "Perrone A. Antiphospholipid syndrome: a case report with an unusual wide "
                    "spectrum of clinical manifestations. Autoimmunity Highlights. 2019. "
                    "doi:10.1186/s13317-019-0119-3. PMCID: PMC7065311.",
        "confirmed_diagnosis": "Síndrome antifosfolípido primario",
        "request": {
            "patient": {"external_id": "case-05", "age": 43, "sex": "male"},
            "history": {"symptom_duration_days": 3285},
            "physical_findings": {"free_text": "Trombocitopenia, endocarditis no bacteriana, pancreatitis aguda"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "Anti-β2GPI IgG", "value": 113.4, "unit": "U/mL", "interpretation": "high"},
                    {"loinc_code": "16097-9", "test_name": "Anticardiolipina IgG", "value": ">640", "unit": "U/mL", "interpretation": "high"},
                    {"loinc_code": "22599-7", "test_name": "Anticoagulante lúpico", "value": "Positivo", "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "Negativo", "interpretation": "normal"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Plaquetas", "value": 25, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Trombocitopenia y pancreatitis aguda de origen a estudiar, 9 años de síntomas inespecíficos",
            "language": "es",
        },
    },
    {
        "case_id": "case_06_aps",
        "citation": "Huo L, Hou C, Cao C, Peng X, Liu J. Primary antiphospholipid syndrome "
                    "complicated by recurrent acute ST-elevation myocardial infarction: a case "
                    "report. Frontiers in Cardiovascular Medicine. 2026;12:1656890. "
                    "doi:10.3389/fcvm.2025.1656890. PMCID: PMC12819726.",
        "confirmed_diagnosis": "Síndrome antifosfolípido primario con infarto agudo recurrente",
        "request": {
            "patient": {"external_id": "case-06", "age": 35, "sex": "male"},
            "history": {"comorbidities": ["psoriasis", "hígado graso", "dislipidemia"]},
            "physical_findings": {"free_text": "Infarto agudo de miocardio recurrente, disfunción microvascular coronaria"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "22599-7", "test_name": "Anticoagulante lúpico (dRVVT-R)", "value": 1.34, "ref_low": 0.8, "ref_high": 1.2, "interpretation": "high"},
                    {"loinc_code": "16097-9", "test_name": "Anticardiolipina IgG", "value": 63.7, "unit": "U/mL", "ref_high": 10, "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:80 positivo", "interpretation": "high"},
                    {"test_name": "Anti-β2-glicoproteína I", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Plaquetas", "value": 56, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Infarto agudo de miocardio recurrente en paciente joven sin factores de riesgo coronario clásicos",
            "language": "es",
        },
    },
    {
        "case_id": "case_07_aps",
        "citation": "Irugu HS, Dhananjayan K, Kalaichelvi S, Selvaraj C. Primary "
                    "antiphospholipid syndrome as the initial manifestation of systemic lupus "
                    "erythematosus in a male: A case report. J Postgrad Med. 2025;71(3):151-152. "
                    "doi:10.4103/jpgm.jpgm_552_25. PMCID: PMC12534099.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico con síndrome antifosfolípido secundario",
        "request": {
            "patient": {"external_id": "case-07", "age": 37, "sex": "male"},
            "physical_findings": {"free_text": "Pancitopenia, proteinuria, ESR elevado"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "16097-9", "test_name": "Anticardiolipina IgG", "value": 75, "unit": "GPL", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "Anti-β2GP1 IgG", "value": 90, "unit": "SGU", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "22599-7", "test_name": "Anticoagulante lúpico (dRVVT)", "value": "Positivo", "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "3+ patrón moteado", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Anti-SSA/Ro-52", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 84.3, "ref_low": 90, "ref_high": 180, "interpretation": "low"},
                    {"test_name": "Complemento C4", "value": 11.2, "ref_low": 15, "ref_high": 45, "interpretation": "low"},
                    {"test_name": "Proteinuria 24h", "value": 3053, "unit": "mg/día", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Pancitopenia y proteinuria en varón joven, estudio de enfermedad del tejido conectivo",
            "language": "es",
        },
    },
    {
        "case_id": "case_08_aps",
        "citation": "Tsiakas S, Skalioti C, Kotsi P, Boletis I, Marinaki S. Case of an unusual "
                    "diagnosis of primary antiphospholipid syndrome with multiple clinical "
                    "complications. Oxford Medical Case Reports. 2020;2020(12):omaa117. "
                    "doi:10.1093/omcr/omaa117. PMCID: PMC7768524.",
        "confirmed_diagnosis": "Síndrome antifosfolípido primario triple-positivo",
        "request": {
            "patient": {"external_id": "case-08", "age": 25, "sex": "male"},
            "physical_findings": {"free_text": "Hipertensión de novo, microangiopatía renal, valvulopatía"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "22599-7", "test_name": "Anticoagulante lúpico", "value": "Positivo", "interpretation": "high"},
                    {"loinc_code": "16097-9", "test_name": "Anticardiolipina IgG", "value": ">90", "unit": "GPLU/mL", "ref_high": 15, "interpretation": "high"},
                    {"test_name": "Anti-β2-GPI IgG", "value": 100, "unit": "U/mL", "ref_high": 9, "interpretation": "high"},
                    {"test_name": "Autoanticuerpos LES (panel)", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "TTPa", "value": 86.9, "unit": "seg", "ref_low": 29, "ref_high": 40, "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Hipertensión de reciente diagnóstico con deterioro de función renal en adulto joven",
            "language": "es",
        },
    },
    {
        "case_id": "case_09_aps",
        "citation": "Mantovani Cardoso E, Hundal J, Feterman D, Magaldi J. Concomitant new "
                    "diagnosis of systemic lupus erythematosus and COVID-19 with possible "
                    "antiphospholipid syndrome. Clinical Rheumatology. 2020;39(9):2811-2815. "
                    "doi:10.1007/s10067-020-05310-1. PMCID: PMC7384868.",
        "confirmed_diagnosis": "Lupus eritematoso sistémico de nuevo diagnóstico con posible síndrome antifosfolípido concomitante",
        "request": {
            "patient": {"external_id": "case-09", "age": 18, "sex": "female"},
            "history": {"comorbidities": ["trastorno del espectro autista", "trastorno de pánico"]},
            "physical_findings": {"free_text": "Cuadro multisistémico concomitante con COVID-19"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": ">=1:2560 homogéneo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": 943, "unit": "IU/mL", "ref_high": 4, "interpretation": "high"},
                    {"loinc_code": "22599-7", "test_name": "Anticoagulante lúpico", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 29, "unit": "mg/dL", "ref_low": 83, "ref_high": 193, "interpretation": "low"},
                    {"test_name": "Complemento C4", "value": 9, "unit": "mg/dL", "ref_low": 15, "ref_high": 57, "interpretation": "low"},
                    {"test_name": "Anti-SSA/SSB, Anti-Sm, Factor Reumatoide", "value": "Negativo", "interpretation": "normal"},
                ],
            }],
            "clinical_diagnosis": "Adolescente con cuadro multisistémico e infección concomitante por COVID-19, estudio de enfermedad autoinmune",
            "language": "es",
        },
    },
    # ------------------------------------------------------------ Sjögren
    {
        "case_id": "case_10_sjogren",
        "citation": "Nakamura H, Tsukamoto M, Nagata K, et al. Sjögren's syndrome positive for "
                    "isolated anti-Ro52/SS-A antibody and anti-centromere antibody. J Int Med "
                    "Res. 2024;52(11). doi:10.1177/03000605241293986. PMCID: PMC11539262.",
        "confirmed_diagnosis": "Síndrome de Sjögren primario",
        "request": {
            "patient": {"external_id": "case-10", "age": 83, "sex": "female"},
            "physical_findings": {"free_text": "Xerostomía de un mes de evolución, sin xeroftalmia"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"test_name": "Anti-Ro52 (SSA)", "value": 28.3, "unit": "U/mL", "interpretation": "high"},
                    {"test_name": "Anti-Ro60 (SSA)", "value": "<1.0", "unit": "U/mL", "interpretation": "normal"},
                    {"loinc_code": "24082-2", "test_name": "Anti-SSB (La)", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Anti-centrómero", "value": 905, "unit": "U/mL", "ref_high": 10, "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:1280", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Mujer de edad avanzada con sequedad bucal subaguda, estudio de síndrome seco",
            "language": "es",
        },
    },
    {
        "case_id": "case_11_sjogren",
        "citation": "Laxmidhar RM, Laxmidhar F, Shastri K, Patel S, Patel S. Fulminant "
                    "Neurologic Manifestation of Sjogren's Syndrome: A Case Report. Cureus. "
                    "2023;15(7):e42604. doi:10.7759/cureus.42604. PMCID: PMC10460263.",
        "confirmed_diagnosis": "Síndrome de Sjögren primario con acidosis tubular renal distal e hipopotasemia severa",
        "request": {
            "patient": {"external_id": "case-11", "age": 18, "sex": "female"},
            "physical_findings": {"free_text": "Parálisis flácida aguda, acidosis metabólica"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "24081-4", "test_name": "Anti-SSA (Ro)", "value": 100, "unit": "U/mL", "ref_high": 12, "interpretation": "high"},
                    {"loinc_code": "24082-2", "test_name": "Anti-SSB (La)", "value": 64, "unit": "U/mL", "ref_high": 12, "interpretation": "high"},
                    {"test_name": "Potasio sérico", "value": 1.68, "unit": "mmol/L", "ref_low": 3.5, "ref_high": 5.1, "interpretation": "critical"},
                    {"test_name": "Bicarbonato", "value": 14.2, "unit": "mmol/L", "ref_low": 22, "ref_high": 28, "interpretation": "low"},
                    {"test_name": "pH arterial", "value": 7.14, "ref_low": 7.35, "ref_high": 7.45, "interpretation": "critical"},
                ],
            }],
            "clinical_diagnosis": "Mujer joven con parálisis flácida aguda e hipopotasemia severa de causa no precisada",
            "language": "es",
        },
    },
    {
        "case_id": "case_12_sjogren",
        "citation": "Shah P, Jaiswal P, Adhikari P, Jaiswal SK, Parajuli K. Maternal Primary "
                    "Sjögren's Syndrome Complicated by Irreversible Fetal Third-Degree Congenital "
                    "Heart Block: A Case Report From Nepal. Clin Case Rep. 2025;13(11):e71349. "
                    "doi:10.1002/ccr3.71349. PMCID: PMC12550594.",
        "confirmed_diagnosis": "Síndrome de Sjögren primario materno con bloqueo cardiaco congénito fetal",
        "request": {
            "patient": {"external_id": "case-12", "age": 34, "sex": "female"},
            "history": {"pregnancies": 2, "miscarriages": 1},
            "physical_findings": {"free_text": "Hallazgo de bradicardia fetal en control prenatal"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "24081-4", "test_name": "Anti-Ro/SSA (Ro60)", "value": 118.87, "unit": "U", "interpretation": "high"},
                    {"loinc_code": "24082-2", "test_name": "Anti-La/SSB", "value": 78.25, "unit": "U", "interpretation": "high"},
                    {"test_name": "Anticardiolipina IgG/IgM, Anti-β2GPI", "value": "Negativo", "interpretation": "normal"},
                ],
            }],
            "clinical_diagnosis": "Embarazada con hallazgo de bradicardia fetal, estudio de causa autoinmune materna",
            "language": "es",
        },
    },
    # ------------------------------------------------------------------ RA
    {
        "case_id": "case_13_ra",
        "citation": "Sadeghi N, Haberman B, McDermott J, Matthews N. A Case Report of "
                    "Rheumatoid Arthritis With a Migratory Pattern. Cureus. 2025;17(6):e86677. "
                    "doi:10.7759/cureus.86677. PMCID: PMC12289107.",
        "confirmed_diagnosis": "Artritis reumatoide temprana con patrón migratorio atípico",
        "request": {
            "patient": {"external_id": "case-13", "age": 74, "sex": "female"},
            "history": {"comorbidities": ["hipertensión", "hipotiroidismo", "diabetes tipo 2", "obesidad"]},
            "physical_findings": {"free_text": "Dolor articular y muscular migratorio de inicio agudo"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "34505-9", "test_name": "Anti-CCP IgG", "value": 17, "unit": "U/mL", "ref_high": 16, "interpretation": "high"},
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": "<8.0", "unit": "IU/mL", "ref_high": 8, "interpretation": "normal"},
                    {"test_name": "PCR", "value": 0.9, "unit": "mg/dL", "ref_high": 0.5, "interpretation": "high"},
                    {"test_name": "ANA", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "ANCA (c y p)", "value": "Negativo", "interpretation": "normal"},
                ],
            }],
            "clinical_diagnosis": "Adulta mayor con poliartralgia migratoria de inicio agudo, descartar artritis inflamatoria",
            "language": "es",
        },
    },
    {
        "case_id": "case_14_ra_distractor",
        "citation": "Silvério-António M, Parlato F, Martins P, et al. Gastric Adenocarcinoma "
                    "Presenting as a Rheumatoid Factor and Anti-cyclic Citrullinated Protein "
                    "Antibody-Positive Polyarthritis: A Case Report and Review of Literature. "
                    "Front Med. 2021;8:627004. doi:10.3389/fmed.2021.627004. PMCID: PMC8180584.",
        "confirmed_diagnosis": "Artritis paraneoplásica secundaria a adenocarcinoma gástrico (NO es artritis reumatoide, pese a serología positiva)",
        "request": {
            "patient": {"external_id": "case-14", "age": 64, "sex": "male"},
            "history": {"symptom_duration_days": 180},
            "physical_findings": {"free_text": "Poliartritis simétrica, pérdida de peso de 12kg, astenia"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": 215, "unit": "IU/mL", "ref_high": 14, "interpretation": "high"},
                    {"loinc_code": "34505-9", "test_name": "Anti-CCP (ACPA)", "value": 156.9, "unit": "IU/mL", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "Hemoglobina", "value": 7.9, "unit": "g/dL", "ref_low": 13, "ref_high": 17, "interpretation": "low"},
                    {"test_name": "Plaquetas", "value": 904, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "high"},
                    {"test_name": "PCR", "value": 17.3, "unit": "mg/dL", "ref_high": 0.5, "interpretation": "high"},
                    {"test_name": "VSG", "value": 94, "unit": "mm/h", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "Hierro sérico", "value": 9.6, "unit": "ug/dL", "ref_low": 60, "ref_high": 170, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Poliartritis simétrica seropositiva de 6 meses con pérdida de peso significativa y anemia, estudio reumatológico",
            "language": "es",
        },
    },
    # ---------------------------------------------------------------- MCTD
    {
        "case_id": "case_15_mctd",
        "citation": "Al Lawati T, Hassan B. Mixed Connective Tissue Disease with Severe Axonal "
                    "Polyneuropathy: A Case Report. Oman Med J. 2022;37(3):e376. "
                    "doi:10.5001/omj.2022.08. PMCID: PMC9188733.",
        "confirmed_diagnosis": "Enfermedad mixta del tejido conectivo con polineuropatía axonal severa",
        "request": {
            "patient": {"external_id": "case-15", "age": 36, "sex": "male"},
            "history": {"comorbidities": ["hipertensión de difícil control"]},
            "physical_findings": {"free_text": "Debilidad progresiva de extremidades inferiores, poliartralgia, parestesias"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:640 patrón moteado", "interpretation": "high"},
                    {"test_name": "Anti-U1-RNP", "value": "Fuertemente positivo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Anticuerpos antifosfolípido", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "VSG", "value": 115, "unit": "mm/h", "ref_high": 30, "interpretation": "high"},
                    {"test_name": "Complemento C3", "value": 0.94, "unit": "g/L", "ref_low": 0.90, "ref_high": 1.80, "interpretation": "normal"},
                    {"test_name": "Hemoglobina", "value": 10.5, "unit": "g/dL", "ref_low": 11, "ref_high": 14.5, "interpretation": "low"},
                ],
            }],
            "clinical_diagnosis": "Debilidad progresiva de extremidades y poliartralgia de un año de evolución, estudio neurológico y reumatológico",
            "language": "es",
        },
    },
    {
        "case_id": "case_16_mctd",
        "citation": "Alsulami K, D'Aoust J. Not Just Myocarditis: Mixed Connective Tissue "
                    "Disease (MCTD) and Overlap Myositis With Anti-Ku Positivity in a Young Male "
                    "With Shortness of Breath. Cureus. 2024. doi:10.7759/cureus.72310. "
                    "PMID: 39450217. PMCID: PMC11500815.",
        "confirmed_diagnosis": "Enfermedad mixta del tejido conectivo con miositis de superposición (anti-Ku positivo)",
        "request": {
            "patient": {"external_id": "case-16", "age": 19, "sex": "male"},
            "physical_findings": {"free_text": "Disnea de esfuerzo, debilidad muscular proximal, sinovitis"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:2560 patrón moteado", "interpretation": "high"},
                    {"test_name": "Anti-RNP", "value": ">644", "unit": "CU", "ref_high": 20, "interpretation": "high"},
                    {"test_name": "Anti-Ku", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "Anti-Sm", "value": ">694", "unit": "CU", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "24081-4", "test_name": "Anti-Ro/SSA", "value": 170, "unit": "U/mL", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "<10", "unit": "IU/mL", "ref_high": 30, "interpretation": "normal"},
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": "<10", "unit": "IU/mL", "ref_high": 14, "interpretation": "normal"},
                    {"test_name": "Troponina T", "value": 673, "unit": "ng/L", "ref_high": 15, "interpretation": "critical"},
                    {"test_name": "CK", "value": 24349, "unit": "U/L", "ref_low": 54, "ref_high": 320, "interpretation": "critical"},
                ],
            }],
            "clinical_diagnosis": "Varón joven deportista con disnea aguda, debilidad muscular y elevación de troponina, descartar miocarditis",
            "language": "es",
        },
    },
    {
        "case_id": "case_17_mctd",
        "citation": "Furuya MY, Watanabe H, Sato S, et al. An Autopsy Case of Mixed Connective "
                    "Tissue Disease Complicated by Thrombotic Thrombocytopenic Purpura. Intern "
                    "Med. 2020;59(10):1315-1321. doi:10.2169/internalmedicine.3939-19. "
                    "PMCID: PMC7303452.",
        "confirmed_diagnosis": "Enfermedad mixta del tejido conectivo complicada con púrpura trombocitopénica trombótica",
        "request": {
            "patient": {"external_id": "case-17", "age": 59, "sex": "female"},
            "history": {"comorbidities": ["enfermedad mixta del tejido conectivo (diagnóstico previo, 20+ años)"]},
            "physical_findings": {"free_text": "Anemia severa, trombocitopenia aguda, alteración neurológica"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1:640 patrón moteado", "interpretation": "high"},
                    {"test_name": "Anti-U1-RNP", "value": 141.0, "unit": "U/mL", "interpretation": "high"},
                    {"loinc_code": "24081-4", "test_name": "Anti-SSA/Ro", "value": 137.0, "unit": "U/mL", "interpretation": "high"},
                    {"test_name": "ADAMTS13 actividad", "value": "<0.5", "unit": "%", "interpretation": "critical"},
                    {"test_name": "Hemoglobina", "value": 6.3, "unit": "g/dL", "ref_low": 12, "ref_high": 16, "interpretation": "critical"},
                    {"test_name": "Plaquetas", "value": 6, "unit": "x10^3/uL", "ref_low": 150, "ref_high": 450, "interpretation": "critical"},
                ],
            }],
            "clinical_diagnosis": "Paciente con enfermedad del tejido conectivo conocida, anemia y trombocitopenia agudas de nueva aparición",
            "language": "es",
        },
    },
    # ---------------------------------------------- Rhupus (RA+SLE overlap)
    {
        "case_id": "case_18_rhupus",
        "citation": "Devrimsel G, Serdaroglu Beyazal M. Three Case Reports of Rhupus Syndrome: "
                    "An Overlap Syndrome of Rheumatoid Arthritis and Systemic Lupus "
                    "Erythematosus (Patient 1). Case Rep Rheumatol. 2018;2018:6194738. "
                    "doi:10.1155/2018/6194738. PMCID: PMC5828105.",
        "confirmed_diagnosis": "Síndrome de Rhupus (superposición artritis reumatoide + lupus eritematoso sistémico)",
        "request": {
            "patient": {"external_id": "case-18", "age": 50, "sex": "female"},
            "history": {"symptom_duration_days": 3285},
            "physical_findings": {"free_text": "Poliartritis simétrica crónica, hematuria microscópica"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": 393, "unit": "IU/mL", "ref_high": 14, "interpretation": "high"},
                    {"loinc_code": "34505-9", "test_name": "Anti-CCP", "value": 500, "unit": "U/mL", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1/100 positivo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": 43.2, "interpretation": "high"},
                    {"test_name": "Complemento C4", "value": 13.2, "unit": "mg/dL", "interpretation": "low"},
                    {"test_name": "VSG", "value": 45, "unit": "mm/h", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Poliartritis simétrica crónica de 9 años con hematuria microscópica de nueva aparición",
            "language": "es",
        },
    },
    {
        "case_id": "case_19_rhupus",
        "citation": "Devrimsel G, Serdaroglu Beyazal M. Three Case Reports of Rhupus Syndrome "
                    "(Patient 2). Case Rep Rheumatol. 2018;2018:6194738. "
                    "doi:10.1155/2018/6194738. PMCID: PMC5828105.",
        "confirmed_diagnosis": "Síndrome de Rhupus (superposición artritis reumatoide + lupus eritematoso sistémico)",
        "request": {
            "patient": {"external_id": "case-19", "age": 26, "sex": "female"},
            "history": {"symptom_duration_days": 548},
            "physical_findings": {"free_text": "Poliartritis simétrica, hematuria microscópica"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": 78.2, "unit": "IU/mL", "ref_high": 14, "interpretation": "high"},
                    {"loinc_code": "34505-9", "test_name": "Anti-CCP", "value": 47.9, "unit": "U/mL", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1/100 positivo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "Negativo", "interpretation": "normal"},
                    {"test_name": "Anti-Sm", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "VSG", "value": 54, "unit": "mm/h", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Mujer joven con poliartritis simétrica de 18 meses y hematuria microscópica",
            "language": "es",
        },
    },
    {
        "case_id": "case_20_rhupus",
        "citation": "Devrimsel G, Serdaroglu Beyazal M. Three Case Reports of Rhupus Syndrome "
                    "(Patient 3). Case Rep Rheumatol. 2018;2018:6194738. "
                    "doi:10.1155/2018/6194738. PMCID: PMC5828105.",
        "confirmed_diagnosis": "Síndrome de Rhupus (superposición artritis reumatoide + lupus eritematoso sistémico)",
        "request": {
            "patient": {"external_id": "case-20", "age": 40, "sex": "female"},
            "history": {"symptom_duration_days": 2190},
            "physical_findings": {"free_text": "Poliartritis simétrica, hematuria microscópica"},
            "lab_series": [{
                "report_date": "2024-01-01",
                "results": [
                    {"loinc_code": "11572-5", "test_name": "Factor Reumatoide", "value": 84.1, "unit": "IU/mL", "ref_high": 14, "interpretation": "high"},
                    {"loinc_code": "34505-9", "test_name": "Anti-CCP", "value": 63.2, "unit": "U/mL", "ref_high": 20, "interpretation": "high"},
                    {"loinc_code": "5048-4", "test_name": "ANA", "value": "1/100 positivo", "interpretation": "high"},
                    {"loinc_code": "14169-3", "test_name": "Anti-dsDNA", "value": "Positivo", "interpretation": "high"},
                    {"loinc_code": "24081-4", "test_name": "Anti-SSA", "value": "Positivo", "interpretation": "high"},
                    {"test_name": "VSG", "value": 56, "unit": "mm/h", "interpretation": "high"},
                ],
            }],
            "clinical_diagnosis": "Mujer con poliartritis simétrica de 6 años y hematuria microscópica de nueva aparición",
            "language": "es",
        },
    },
]

if __name__ == "__main__":
    print(f"{len(CASES)} casos cargados")
    for c in CASES:
        print(" -", c["case_id"], "->", c["confirmed_diagnosis"])
