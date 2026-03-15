from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gateway"
    app_namespace: str = "cap-prod-gateway"
    app_env: str = "production"
    app_port: int = 8080
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    auth_service_url: str = "http://auth.cap-prod-auth.svc.cluster.local:8081"
    request_timeout_seconds: int = 5

    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    readiness_check_auth: bool = False

    tracing_enabled: bool = False
    otel_service_name: str = "gateway"
    otel_service_namespace: str = "cap-prod-gateway"
    otel_exporter_otlp_endpoint: str = "http://otel-collector.observability:4318/v1/traces"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )


settings = Settings()
