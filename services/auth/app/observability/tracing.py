from app.core.logging import get_logger

logger = get_logger(__name__)



def setup_tracing(settings) -> None:
    if not settings.otel_enabled:
        logger.info(
            "otel disabled",
            extra={
                "request_id": None,
                "http_method": None,
                "http_route": None,
                "http_status_code": None,
                "duration_ms": None,
                "error_type": None,
            },
        )
        return

    logger.info(
        "otel placeholder initialized",
        extra={
            "request_id": None,
            "http_method": None,
            "http_route": None,
            "http_status_code": None,
            "duration_ms": None,
            "error_type": None,
        },
    )
