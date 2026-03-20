import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import Settings, get_settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        settings = get_settings()

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": settings.app_name,
            "service_namespace": settings.app_namespace,
            "service_version": settings.service_version,
            "environment": settings.environment,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "http_method": getattr(record, "http_method", None),
            "http_route": getattr(record, "http_route", None),
            "http_status_code": getattr(record, "http_status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "error_type": getattr(record, "error_type", None),
            "logger": record.name,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)



def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(settings.log_level.upper())
    root_logger.addHandler(handler)

    for noisy_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(noisy_logger)
        logger.handlers = []
        logger.propagate = True



def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
