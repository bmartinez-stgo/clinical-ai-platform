import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "auth")
    app_namespace: str = os.getenv("APP_NAMESPACE", "cap-prod-auth")
    app_port: int = int(os.getenv("APP_PORT", "8081"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    service_version: str = os.getenv("SERVICE_VERSION", "0.1.0")
    environment: str = os.getenv("ENVIRONMENT", "prod")

    auth_token_secret: str = os.getenv("AUTH_TOKEN_SECRET", "changeme")
    token_expiration_seconds: int = int(os.getenv("TOKEN_EXPIRATION_SECONDS", "3600"))
    jwt_issuer: str = os.getenv("JWT_ISSUER", "clinical-ai-platform-auth")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "clinical-ai-platform")

    otel_enabled: bool = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "auth")
    otel_exporter_otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    auth_users_json: str = os.getenv(
        "AUTH_USERS_JSON",
        '[{"username":"admin","password":"changeme","roles":["admin"]}]',
    )
    auth_users: List[dict] = field(default_factory=list)

    def __post_init__(self):
        self.auth_users = json.loads(self.auth_users_json)


@lru_cache
def get_settings() -> Settings:
    return Settings()
