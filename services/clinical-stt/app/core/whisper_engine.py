from __future__ import annotations

import logging
import os
import tempfile

logger = logging.getLogger(__name__)

_model = None


def get_model(model_name: str, device: str, compute_type: str):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(
            "loading whisper model",
            extra={"model": model_name, "device": device, "compute_type": compute_type},
        )
        _model = WhisperModel(model_name, device=device, compute_type=compute_type)
        logger.info("whisper model loaded")
    return _model


def transcribe(
    audio_bytes: bytes,
    model_name: str,
    device: str,
    compute_type: str,
    language: str = "es",
    max_duration_seconds: int = 1800,
) -> tuple[str, float]:
    model = get_model(model_name, device, compute_type)

    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language=language if language != "auto" else None,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        # info.duration is available immediately (reads file header, before GPU work)
        if info.duration > max_duration_seconds:
            limit_min = max_duration_seconds // 60
            raise ValueError(
                f"audio duration {info.duration / 60:.1f} min exceeds the {limit_min}-minute limit"
            )
        transcript = " ".join(seg.text.strip() for seg in segments)
        return transcript.strip(), info.duration
    finally:
        os.unlink(tmp_path)
