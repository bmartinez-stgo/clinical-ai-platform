"""Security guardrails for clinical chat to prevent prompt injection and off-topic responses."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Medical keywords that should appear in valid clinical questions
MEDICAL_KEYWORDS = {
    'es': {
        'symptoms': ['síntoma', 'dolor', 'fiebre', 'malestar', 'cansancio', 'debilidad'],
        'tests': ['laboratorio', 'análisis', 'resultado', 'examen', 'prueba', 'valor'],
        'treatments': ['medicamento', 'tratamiento', 'droga', 'fármaco', 'terapia'],
        'diagnosis': ['diagnóstico', 'enfermedad', 'condición', 'patología', 'descartar'],
        'clinical': ['paciente', 'clínico', 'médico', 'presión', 'glucosa', 'creatinina', 'hemoglobina'],
    },
    'en': {
        'symptoms': ['symptom', 'pain', 'fever', 'fatigue', 'weakness', 'discomfort'],
        'tests': ['lab', 'test', 'result', 'examination', 'value', 'findings'],
        'treatments': ['medication', 'treatment', 'drug', 'therapy', 'prescription'],
        'diagnosis': ['diagnosis', 'disease', 'condition', 'pathology', 'rule out'],
        'clinical': ['patient', 'clinical', 'physician', 'pressure', 'glucose', 'creatinine', 'hemoglobin'],
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
            logger.warning("potential_prompt_injection", extra={"pattern": pattern, "text": text[:100]})
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
                extra={"trigger": trigger, "text": text[:100]}
            )
            return False, f"Query appears to be about '{trigger}', not clinical matters"

    # Require at least one medical keyword
    medical_kw = MEDICAL_KEYWORDS.get(lang_key, {})
    all_medical_keywords = []
    for category_keywords in medical_kw.values():
        all_medical_keywords.extend(category_keywords)

    has_medical_keyword = any(kw in text_lower for kw in all_medical_keywords)

    if not has_medical_keyword:
        logger.warning("no_medical_keywords", extra={"text": text[:100]})
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
                extra={"trigger": trigger, "response": response[:100]}
            )
            return False, "Model response deviates from clinical context"

    # Response should reference patient data or clinical concepts
    # (must be at least somewhat coherent with medical context)
    min_length = 10  # At least some content
    if len(response) < min_length:
        return False, "Response too short to be meaningful clinical content"

    return True, None
