import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "document-reader")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-document-reader")
    app_port: int = int(os.getenv("APP_PORT", "8082"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")
    max_upload_size_bytes: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "20971520"))
    render_dpi: int = int(os.getenv("RENDER_DPI", "120"))
    ai_engine_url: str = os.getenv(
        "AI_ENGINE_URL",
        "http://ai-engine.cap-prod-ai-engine.svc.cluster.local:8090/extract/lab-report",
    )
    ai_engine_timeout_seconds: int = int(os.getenv("AI_ENGINE_TIMEOUT_SECONDS", "120"))
    ai_engine_page_batch_size: int = int(os.getenv("AI_ENGINE_PAGE_BATCH_SIZE", "1"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
