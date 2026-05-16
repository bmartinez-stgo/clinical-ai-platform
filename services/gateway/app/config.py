from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "gateway"
    app_namespace: str = "cap-prod-gateway"
    app_env: str = "production"
    app_port: int = 8080
    log_level: str = "INFO"
    service_version: str = "0.1.0"

    auth_service_url: str = "http://auth.cap-prod-auth.svc.cluster.local:8081"
    request_timeout_seconds: int = 300
    proxy_config_path: str = "/app/config/routes.yaml"

    metrics_enabled: bool = True
    metrics_path: str = "/metrics"

    token_validation_enabled: bool = True
    readiness_check_auth: bool = False

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_auth_rpm: int = 30          # per-user limit for /auth/* routes
    rate_limit_auth_sensitive_rpm: int = 5  # IP limit for /auth/login and /auth/refresh
    rate_limit_documents_rpm: int = 10
    rate_limit_diagnostics_rpm: int = 20
    rate_limit_clinical_chat_rpm: int = 10
    rate_limit_rag_rpm: int = 30
    rate_limit_portal_rpm: int = 60
    rate_limit_default_rpm: int = 30
    rate_limit_token_rpm: int = 10

    # IP blocking
    ip_block_enabled: bool = True
    ip_blocklist: str = ""  # comma-separated CIDRs for static deny list
    ip_auto_block_threshold: int = 20  # failed auth attempts before auto-block
    ip_auto_block_window_seconds: int = 300  # sliding window for counting failures
    ip_auto_block_duration_seconds: int = 3600  # auto-block duration

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
