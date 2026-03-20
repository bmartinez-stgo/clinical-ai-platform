import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "vision-inference")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-document-reader")
    app_port: int = int(os.getenv("APP_PORT", "8090"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")
    engine_backend: str = os.getenv("ENGINE_BACKEND", "transformers")
    engine_id: str = os.getenv("ENGINE_ID", "Qwen/Qwen2.5-VL-3B-Instruct")
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "4096"))
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    device_preference: str = os.getenv("DEVICE_PREFERENCE", "cuda")


@lru_cache
def get_settings() -> Settings:
    return Settings()
