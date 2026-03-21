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
    ai_engine_url: str = os.getenv(
        "AI_ENGINE_URL",
        "http://ai-engine.cap-prod-ai-engine.svc.cluster.local:8090/infer/clinical",
    )
    ai_engine_timeout_seconds: int = int(os.getenv("AI_ENGINE_TIMEOUT_SECONDS", "120"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
