from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "clinical-rag")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-clinical-rag")
    app_port: int = int(os.getenv("APP_PORT", "8085"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")

    chromadb_host: str = os.getenv("CHROMADB_HOST", "chromadb")
    chromadb_port: int = int(os.getenv("CHROMADB_PORT", "8000"))

    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
    )

    otel_enabled: bool = os.getenv("OTEL_ENABLED", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
