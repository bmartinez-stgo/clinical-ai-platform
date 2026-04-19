import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "ai-diagnostic")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-ai-diagnostic")
    app_port: int = int(os.getenv("APP_PORT", "8083"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")
    vllm_reasoning_url: str = os.getenv(
        "VLLM_REASONING_URL",
        "http://vllm-reasoning.cap-prod-vllm-reasoning.svc.cluster.local:8000",
    )
    vllm_reasoning_model: str = os.getenv(
        "VLLM_REASONING_MODEL",
        "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
    )
    vllm_timeout_seconds: int = int(os.getenv("VLLM_TIMEOUT_SECONDS", "120"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2048"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
