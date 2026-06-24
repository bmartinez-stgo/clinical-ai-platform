import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "ai-engine-portal")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-ai-engine-portal")
    app_port: int = int(os.getenv("APP_PORT", "8084"))
    tracing_enabled: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "ai-engine-portal")
    otel_service_namespace: str = os.getenv("OTEL_SERVICE_NAMESPACE", "cap-prod-ai-engine-portal")
    otel_exporter_otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability.svc.cluster.local:4318/v1/traces")


@lru_cache
def get_settings() -> Settings:
    return Settings()
