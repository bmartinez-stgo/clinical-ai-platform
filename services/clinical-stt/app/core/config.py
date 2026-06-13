import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "clinical-stt")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-clinical-stt")
    app_port: int = int(os.getenv("APP_PORT", "8087"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    whisper_model: str = os.getenv("WHISPER_MODEL", "large-v3-turbo")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    hf_home: str = os.getenv("HF_HOME", "/var/cache/huggingface")

    vllm_reasoning_url: str = os.getenv(
        "VLLM_REASONING_URL",
        "http://vllm-reasoning.cap-prod-vllm-reasoning.svc.cluster.local:8000",
    )
    vllm_reasoning_model: str = os.getenv(
        "VLLM_REASONING_MODEL",
        "Qwen/Qwen2.5-32B-Instruct-AWQ",
    )
    vllm_timeout_seconds: int = int(os.getenv("VLLM_TIMEOUT_SECONDS", "120"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1500"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))

    max_audio_size_bytes: int = int(os.getenv("MAX_AUDIO_SIZE_BYTES", str(50 * 1024 * 1024)))
    job_ttl_seconds: int = int(os.getenv("JOB_TTL_SECONDS", "3600"))
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
