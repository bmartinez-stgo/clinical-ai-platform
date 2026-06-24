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

    tracing_enabled: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "clinical-rag")
    otel_service_namespace: str = os.getenv("OTEL_SERVICE_NAMESPACE", "cap-prod-clinical-rag")
    otel_exporter_otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability.svc.cluster.local:4318/v1/traces")


@lru_cache
def get_settings() -> Settings:
    return Settings()
