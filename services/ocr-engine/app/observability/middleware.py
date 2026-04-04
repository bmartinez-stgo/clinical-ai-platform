import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.observability.metrics import metrics

settings = get_settings()
logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        method = request.method
        route = request.url.path

        in_progress_labels = {
            "service_name": settings.app_name,
            "service_namespace": settings.app_namespace,
            "http_method": method,
            "http_route": route,
            "http_status_code": "in_progress",
        }

        metrics.http_requests_in_progress.labels(**in_progress_labels).inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
            error_type = None
        except Exception as exc:
            status_code = 500
            error_type = exc.__class__.__name__
            logger.exception(
                "unhandled exception",
                extra={
                    "request_id": request_id,
                    "http_method": method,
                    "http_route": route,
                    "http_status_code": status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    "error_type": error_type,
                },
            )
            raise
        finally:
            metrics.http_requests_in_progress.labels(**in_progress_labels).dec()

        duration_seconds = time.perf_counter() - start
        duration_ms = round(duration_seconds * 1000, 2)

        labels = {
            "service_name": settings.app_name,
            "service_namespace": settings.app_namespace,
            "http_method": method,
            "http_route": route,
            "http_status_code": str(status_code),
        }

        metrics.http_requests_total.labels(**labels).inc()
        metrics.http_request_duration_seconds.labels(**labels).observe(duration_seconds)

        if status_code >= 400:
            metrics.http_errors_total.labels(**labels).inc()

        metrics.update_uptime()

        response.headers["x-request-id"] = request_id

        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "http_method": method,
                "http_route": route,
                "http_status_code": status_code,
                "duration_ms": duration_ms,
                "error_type": error_type,
            },
        )

        return response
