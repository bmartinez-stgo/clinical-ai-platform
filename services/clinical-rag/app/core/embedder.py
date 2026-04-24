from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.schema import LabResult

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    model_name = get_settings().embedding_model
    logger.info("loading embedding model: %s", model_name)
    return SentenceTransformer(model_name)


def embed(text: str) -> list[float]:
    return _model().encode(text, normalize_embeddings=True).tolist()


def case_text(age: int, sex: str, results: list[LabResult], notes: str = "") -> str:
    abnormal = [r for r in results if r.interpretation in ("high", "low", "critical")]
    normal_names = [r.test_name for r in results if r.interpretation == "normal"]

    parts = [f"Patient {sex} {age}y"]
    if notes:
        parts.append(f"history: {notes}")
    if abnormal:
        ab = ", ".join(
            f"{r.test_name} {r.interpretation} {r.value}{r.unit or ''}"
            for r in abnormal
        )
        parts.append(f"abnormal: {ab}")
    if normal_names:
        parts.append(f"normal: {', '.join(normal_names[:6])}")

    return ". ".join(parts)
