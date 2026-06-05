"""Security guardrails for clinical chat to prevent prompt injection and off-topic responses."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Medical keywords that should appear in valid clinical questions
MEDICAL_KEYWORDS = {
    'es': {
        'symptoms': [
            # Formal
            'síntoma', 'sintoma', 'dolor', 'fiebre', 'malestar', 'cansancio', 'debilidad',
            'náusea', 'nausea', 'náuseas', 'nauseas', 'vómito', 'vomito', 'mareo',
            'desmayo', 'inflamación', 'inflamacion', 'hinchazón', 'hinchazon',
            'sangrado', 'palpitación', 'palpitacion', 'hormigueo', 'entumecimiento',
            'sudoración', 'sudoracion', 'temblor', 'convulsión', 'convulsion',
            'disnea', 'taquicardia', 'bradicardia', 'ictericia', 'edema',
            # Coloquial y slang México
            'me duele', 'me siento mal', 'me siento bien mal', 'me mareo',
            'se me va la cabeza', 'me da vueltas', 'me da vuelta la cabeza',
            'se me va el mundo', 'ando mal', 'ando malo', 'ando mala',
            'ando enfermo', 'ando enferma', 'me trae mal', 'me traigo mal',
            'no tengo fuerzas', 'estoy sin fuerzas', 'me siento cansado', 'me siento cansada',
            'flojera', 'mucha flojera', 'bien cansado', 'bien cansada',
            'agüitado', 'agüitada', 'tronado', 'tronada', 'descompuesto', 'descompuesta',
            'ando descompuesto', 'ando descompuesta', 'me descompuse',
            'me da asco', 'tengo asco', 'me revuelve el estómago', 'me revuelve',
            'me late raro', 'me late fuerte', 'me salta el corazón',
            'se me entumen', 'se me entumece', 'se me adormece', 'se me duerme',
            'ando hinchado', 'ando hinchada', 'se me hincha', 'se me hinchan',
            'ando pálido', 'ando pálida', 'me veo amarillo', 'me veo amarilla',
            'ando orinando mucho', 'voy mucho al baño', 'orino mucho',
            'tengo mucha sed', 'mucha sed', 'tomo mucha agua',
            'bajo de peso', 'bajé de peso', 'perdí peso', 'subí de peso',
            'me falta el aire', 'me falta el aliento', 'no puedo respirar bien',
            'apachurrado', 'apachurrada',
        ],
        'tests': [
            # Términos de laboratorio formal
            'laboratorio', 'análisis', 'analisis', 'resultado', 'examen', 'prueba', 'valor',
            'analito', 'parámetro', 'parametro', 'rango', 'referencia', 'reporte',
            'marcador', 'indicador', 'muestra', 'perfil', 'panel', 'estudio',
            'biometría', 'biometria', 'bhc', 'química sanguínea', 'quimica sanguinea', 'qs',
            'examen general de orina', 'ego', 'cultivo', 'hemograma', 'citometría',
            'electroforesis', 'hba1c', 'pcr', 'vsg', 'inr', 'tp', 'ttp', 'fibrinógeno',
            'curva de tolerancia', 'carga de glucosa', 'glucosa en ayuno',
            'perfil tiroideo', 'perfil lipídico', 'perfil lipidico', 'perfil hepático',
            'perfil renal', 'perfil inmunológico', 'perfil reumatológico',
            # Estado de resultados
            'alterado', 'alterada', 'elevado', 'elevada', 'alto', 'alta', 'bajo', 'baja',
            'anormal', 'normal', 'fuera de rango', 'dentro de rango',
            'fuera del rango', 'dentro del rango', 'por encima', 'por debajo',
            'por arriba del rango', 'por debajo del rango', 'se salió', 'se pasó',
            'está alto', 'está alta', 'está bajo', 'está baja', 'está elevado',
            'está elevada', 'está alterado', 'está alterada',
            # Preguntas coloquiales sobre resultados
            'mis labs', 'mis laboratorios', 'mis análisis', 'mis analisis',
            'mis resultados', 'los exámenes', 'los examenes', 'los estudios',
            'los valores', 'las pruebas', 'el reporte', 'la biometría', 'la biometria',
            'la química', 'la quimica', 'el perfil', 'el análisis', 'el analisis',
            'cómo están mis', 'como están mis', 'cuál está', 'cual está',
            'cuáles están', 'cuales están', 'qué está', 'que está',
            'qué salió', 'que salió', 'cómo salió', 'como salió',
            'cómo quedó', 'como quedó', 'cómo quedaron', 'como quedaron',
            'cuánto tiene', 'cuanto tiene', 'cuánto salió', 'cuanto salió',
            'cuánto debería', 'cuanto debería', 'cuánto debe estar', 'cuanto debe estar',
            'de cuánto debe', 'de cuanto debe', 'hasta cuánto', 'hasta cuanto',
            'a qué se debe', 'a que se debe', 'por qué está', 'por que está',
            'qué significa', 'que significa', 'qué quiere decir', 'que quiere decir',
            'qué implica', 'que implica', 'qué tan grave', 'que tan grave',
            'es grave', 'es malo', 'es peligroso', 'debo preocuparme', 'me debo preocupar',
            'es normal', 'está normal', 'esta normal', 'es preocupante',
            'qué tan alto', 'que tan alto', 'qué tan bajo', 'que tan bajo',
            'cuánto se desvió', 'cuánto se salió', 'qué tanto se salió',
            'por cuánto se pasó', 'está muy lejos', 'está lejos del rango',
            'qué otro', 'que otro', 'qué otra', 'que otra', 'cuál otro', 'cual otro',
            'algún otro', 'alguna otra', 'hay más', 'qué más', 'que más',
            'qué más está', 'qué más salió', 'cuáles más', 'cuales más',
            'cuántos están', 'cuantos están', 'cuántos salieron', 'cuantos salieron',
            'en cuánto está', 'en cuanto está', 'en qué rango', 'en que rango',
        ],
        'analytes': [
            # Glucosa y metabolismo
            'glucosa', 'azúcar', 'azucar', 'el azúcar', 'el azucar', 'glicemia',
            'glucemia', 'insulina', 'resistencia a la insulina', 'homa',
            # Lípidos
            'colesterol', 'triglicéridos', 'trigliceridos', 'lípidos', 'lipidos',
            'hdl', 'ldl', 'vldl', 'no hdl', 'lipoproteína', 'lipoproteina',
            # Hematología
            'hemoglobina', 'hematocrito', 'plaquetas', 'leucocitos', 'eritrocitos',
            'glóbulos blancos', 'globulos blancos', 'los blancos',
            'glóbulos rojos', 'globulos rojos', 'los rojos',
            'neutrófilos', 'neutrofilos', 'linfocitos', 'monocitos',
            'eosinófilos', 'eosinofilos', 'basófilos', 'basofilos',
            'mcv', 'mch', 'mchc', 'rdw', 'vcm', 'hcm', 'reticulocitos',
            # Función renal
            'creatinina', 'urea', 'bun', 'ácido úrico', 'acido urico',
            'filtrado glomerular', 'tasa de filtración', 'tfg', 'clearance',
            'electrolitos', 'sodio', 'potasio', 'cloro', 'bicarbonato',
            'calcio', 'magnesio', 'fósforo', 'fosforo',
            # Función hepática
            'bilirrubina', 'transaminasa', 'transaminasas', 'tgo', 'tgp',
            'alt', 'ast', 'alp', 'fa', 'ggt', 'gamma gt',
            'albumina', 'proteínas totales', 'proteinas totales', 'globulina',
            'tiempo de protrombina', 'inr',
            # Tiroides
            'tsh', 't3', 't4', 'tiroxina', 'tiroides', 'triyodotironina',
            'anticuerpos tiroideos', 'tpo', 'anti-tpo',
            # Hierro y vitaminas
            'hierro', 'ferritina', 'transferrina', 'saturación de transferrina',
            'vitamina d', 'vitamina b12', 'vitamina b1', 'folato', 'ácido fólico',
            'acido folico',
            # Inflamación e inmunología
            'proteína c reactiva', 'proteina c reactiva', 'pcr', 'pcr ultra',
            'procalcitonina', 'interleucina', 'vsg', 'sedimentación',
            'ana', 'anti-ana', 'anti-dna', 'anca', 'anti-ro', 'anti-la',
            'anti-sm', 'anti-scl', 'anti-jo', 'complemento', 'c3', 'c4',
            'factor reumatoide', 'anti-ccp', 'anticuerpo', 'anticuerpos',
            # Hormonas
            'cortisol', 'prolactina', 'testosterona', 'estradiol', 'progesterona',
            'fsh', 'lh', 'hormona del crecimiento', 'igf',
            # Páncreas
            'amilasa', 'lipasa',
            # Orina
            'proteínas en orina', 'proteinuria', 'microalbuminuria',
            'creatinina en orina', 'glucosa en orina', 'leucocitos en orina',
            # Marcadores cardíacos
            'troponina', 'ck', 'ck-mb', 'bnp', 'pro-bnp',
            # Marcadores tumorales
            'cea', 'ca125', 'ca19', 'afp', 'psa',
        ],
        'treatments': [
            # Formal
            'medicamento', 'tratamiento', 'droga', 'fármaco', 'farmaco', 'terapia',
            'medicina', 'pastilla', 'tableta', 'cápsula', 'capsula', 'jarabe',
            'inyección', 'inyeccion', 'dosis', 'indicación', 'indicacion',
            'receta', 'prescripción', 'prescripcion', 'suplemento', 'vitamina',
            # Medicamentos comunes México
            'metformina', 'insulina', 'glibenclamida', 'enalapril', 'losartán',
            'amlodipino', 'atorvastatina', 'omeprazol', 'levotiroxina',
            'ácido fólico', 'hierro', 'calcio', 'vitamina d',
            'antiinflamatorio', 'antibiótico', 'antibiotic', 'antihipertensivo',
            # Coloquial
            'la pastilla', 'el medicamento', 'qué tomo', 'qué me tomo',
            'qué le doy', 'qué tomar', 'cómo se trata', 'como se trata',
            'tiene cura', 'tiene tratamiento', 'qué me recomienda', 'que me recomienda',
            'qué debo tomar', 'que debo tomar', 'qué puedo tomar', 'que puedo tomar',
            'necesito tomar algo', 'debo tomar algo',
        ],
        'diagnosis': [
            # Formal
            'diagnóstico', 'diagnostico', 'enfermedad', 'condición', 'condicion',
            'patología', 'patologia', 'descartar', 'diferencial', 'síndrome', 'sindrome',
            'presuntivo', 'probable', 'compatible', 'sugestivo', 'hallazgo',
            'cuadro clínico', 'cuadro clinico', 'alteración', 'alteracion',
            'déficit', 'deficit', 'evidencia', 'paraclínico', 'paraclínico',
            'complicación', 'complicacion', 'pronóstico', 'pronostico',
            # Condiciones comunes México
            'diabetes', 'diabético', 'diabetico', 'prediabetes', 'resistencia insulina',
            'hipertensión', 'hipertension', 'hipertenso', 'hipertensa',
            'presión alta', 'presion alta', 'tensión alta', 'tension alta',
            'anemia', 'anémico', 'anemico', 'anémica', 'anemica',
            'hipotiroidismo', 'hipertiroidismo', 'tiroides',
            'gota', 'hiperuricemia', 'úrico', 'urico',
            'lupus', 'les', 'artritis', 'reumatoide', 'autoinmune', 'autoinmun',
            'infección', 'infeccion', 'inflamación', 'inflamacion',
            'insuficiencia renal', 'falla renal', 'riñón', 'rinon', 'riñones',
            'insuficiencia hepática', 'falla hepática', 'hígado', 'higado',
            'dislipidem', 'hiperlipid', 'hipercolesterol', 'hipertriglicerid',
            'obesidad', 'sobrepeso', 'síndrome metabólico', 'sindrome metabolico',
            'enfermedad cardiovascular', 'cardiopatía', 'cardiopatia',
            'nefropatía', 'nefropatia', 'neuropatía', 'neuropatia',
            'retinopatía', 'retinopatia',
        ],
        'clinical': [
            # Formal
            'paciente', 'clínico', 'clinico', 'médico', 'medico', 'doctor', 'doctora',
            'especialista', 'nefrólogo', 'cardiólogo', 'endocrinólogo', 'reumatólogo',
            'presión', 'presion', 'pulso', 'temperatura', 'saturación', 'saturacion',
            'seguimiento', 'control', 'evolución', 'evolucion', 'cita', 'consulta',
            'urgente', 'urgencia', 'emergencia', 'hospitalización', 'hospitalizacion',
            # Preguntas de seguimiento coloquiales
            'el doctor', 'la doctora', 'el médico', 'la médica',
            'debo ir', 'necesito ir', 'tengo que ir', 'hay que ver',
            'se recomienda', 'qué recomienda', 'que recomienda',
            'qué hacer', 'que hacer', 'qué debo hacer', 'que debo hacer',
            'qué le hago', 'que le hago', 'qué sigue', 'que sigue',
            'qué más pedir', 'que más pedir', 'qué más estudios', 'qué más exámenes',
            'qué más analizar', 'qué más revisar',
            'me preocupa', 'estoy preocupado', 'estoy preocupada',
            'qué tan urgente', 'que tan urgente', 'es urgente',
            'debo cuidarme de', 'de qué me cuido', 'de que me cuido',
            'qué no debo comer', 'que no debo comer', 'qué debo evitar',
            'cómo bajo', 'como bajo', 'cómo subo', 'como subo',
            'cómo lo controlo', 'como lo controlo', 'cómo mejoro', 'como mejoro',
        ],
    },
    'en': {
        'symptoms': [
            'symptom', 'pain', 'fever', 'fatigue', 'weakness', 'discomfort',
            'nausea', 'vomiting', 'dizziness', 'swelling', 'bleeding',
            'shortness of breath', 'palpitation', 'numbness', 'weight loss',
            'sweating', 'tremor', 'jaundice', 'edema',
        ],
        'tests': [
            'lab', 'test', 'result', 'examination', 'value', 'findings',
            'analyte', 'parameter', 'range', 'reference', 'report',
            'marker', 'panel', 'profile', 'study', 'bloodwork', 'cbc',
            'out of range', 'within range', 'abnormal', 'normal',
            'elevated', 'high', 'low', 'altered', 'what does it mean',
            'is it serious', 'should i worry', 'why is', 'what is',
            'which one', 'what else', 'how high', 'how low',
        ],
        'analytes': [
            'glucose', 'sugar', 'cholesterol', 'triglycerides', 'hdl', 'ldl',
            'hemoglobin', 'hematocrit', 'platelets', 'leukocytes', 'white blood cells',
            'red blood cells', 'neutrophils', 'lymphocytes', 'creatinine', 'urea',
            'uric acid', 'bilirubin', 'transaminase', 'alt', 'ast', 'albumin',
            'sodium', 'potassium', 'calcium', 'iron', 'ferritin', 'vitamin',
            'tsh', 't3', 't4', 'thyroid', 'insulin', 'cortisol', 'crp', 'troponin',
        ],
        'treatments': [
            'medication', 'treatment', 'drug', 'therapy', 'prescription',
            'pill', 'tablet', 'capsule', 'dose', 'dosage', 'supplement',
        ],
        'diagnosis': [
            'diagnosis', 'disease', 'condition', 'pathology', 'rule out',
            'differential', 'syndrome', 'finding', 'clinical picture',
            'diabetes', 'hypertension', 'anemia', 'hypothyroidism',
            'lupus', 'arthritis', 'infection', 'inflammation', 'insufficiency',
            'metabolic syndrome', 'autoimmune',
        ],
        'clinical': [
            'patient', 'clinical', 'physician', 'doctor', 'specialist',
            'pressure', 'glucose', 'creatinine', 'hemoglobin',
            'follow-up', 'monitoring', 'next steps', 'urgent', 'emergency',
            'what should i do', 'should i worry', 'is it dangerous',
        ],
    }
}

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    r'ignore.*previous|olvida.*anterior',
    r'system prompt|prompt del sistema',
    r'role.*:.*system|role.*:.*admin',
    r'forget.*instruction|olvida.*instrucción',
    r'respond.*as.*\w+|responde.*como',
]

# Topics that are clearly non-medical
NON_MEDICAL_TRIGGERS = {
    'es': [
        'capital de', 'presidente de', 'película', 'serie', 'chiste', 'poema',
        'canción', 'receta de cocina', 'pizza', 'hamburguesa', 'programación',
        'javascript', 'python', 'función', 'database', 'código',
    ],
    'en': [
        'capital of', 'president of', 'movie', 'series', 'joke', 'poem',
        'song', 'recipe', 'pizza', 'code', 'programming', 'function',
        'javascript', 'python', 'database',
    ]
}


def is_prompt_injection_attempt(text: str) -> bool:
    """Detect common prompt injection patterns."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning("potential_prompt_injection", extra={"pattern": pattern, "text_sample": text[:100]})
            return True
    return False


def is_medical_query(text: str, language: str = 'es') -> tuple[bool, Optional[str]]:
    """
    Check if query is related to clinical/medical context.
    Returns (is_medical, reason_if_rejected)
    """
    text_lower = text.lower()
    lang_key = 'es' if language != 'en' else 'en'

    # Check for injection attempts first
    if is_prompt_injection_attempt(text):
        return False, "Query contains potential prompt injection patterns"

    # Check for non-medical triggers
    non_medical = NON_MEDICAL_TRIGGERS.get(lang_key, [])
    for trigger in non_medical:
        if trigger in text_lower:
            logger.warning(
                "non_medical_query_detected",
                extra={"trigger": trigger, "text_sample": text[:100]}
            )
            return False, f"Query appears to be about '{trigger}', not clinical matters"

    # Require at least one medical keyword
    medical_kw = MEDICAL_KEYWORDS.get(lang_key, {})
    all_medical_keywords = []
    for category_keywords in medical_kw.values():
        all_medical_keywords.extend(category_keywords)

    has_medical_keyword = any(kw in text_lower for kw in all_medical_keywords)

    if not has_medical_keyword:
        logger.warning("no_medical_keywords", extra={"text_sample": text[:100]})
        return False, "Query does not contain recognizable medical/clinical terminology"

    return True, None


def is_valid_response(response: str, language: str = 'es') -> tuple[bool, Optional[str]]:
    """
    Validate that model response stays in clinical context.
    Returns (is_valid, reason_if_invalid)
    """
    response_lower = response.lower()
    lang_key = 'es' if language != 'en' else 'en'

    # Check if response contains non-medical content indicators
    non_medical = NON_MEDICAL_TRIGGERS.get(lang_key, [])
    for trigger in non_medical:
        if trigger in response_lower:
            logger.warning(
                "off_topic_response_detected",
                extra={"trigger": trigger, "response_sample": response[:100]}
            )
            return False, "Model response deviates from clinical context"

    # Response should reference patient data or clinical concepts
    # (must be at least somewhat coherent with medical context)
    min_length = 10  # At least some content
    if len(response) < min_length:
        return False, "Response too short to be meaningful clinical content"

    return True, None
