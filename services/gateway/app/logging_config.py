import json
import logging
import sys
from datetime import datetime, timezone

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": getattr(record, "service_name", settings.app_name),
            "service_namespace": getattr(record, "service_namespace", settings.app_namespace),
            "service_version": getattr(record, "service_version", settings.service_version),
            "environment": getattr(record, "environment", settings.app_env),
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "trace_id": getattr(record, "trace_id", None),
            "span_id": getattr(record, "span_id", None),
            "http_method": getattr(record, "http_method", None),
            "http_route": getattr(record, "http_route", None),
            "http_status_code": getattr(record, "http_status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "error_type": getattr(record, "error_type", None),
            "error_code": getattr(record, "error_code", None),
        }
        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
