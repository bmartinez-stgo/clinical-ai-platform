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
    render_dpi: int = int(os.getenv("RENDER_DPI", "180"))
    vision_inference_url: str = os.getenv(
        "VISION_INFERENCE_URL",
        "http://vision-inference.cap-prod-vision-inference.svc.cluster.local:8090/extract/lab-report",
    )
    vision_inference_timeout_seconds: int = int(os.getenv("VISION_INFERENCE_TIMEOUT_SECONDS", "120"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
