import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.observability import (
    PLATFORM_HTTP_REQUEST_DURATION_SECONDS,
    PLATFORM_HTTP_REQUEST_ERRORS_TOTAL,
    PLATFORM_HTTP_REQUESTS_IN_PROGRESS,
    PLATFORM_HTTP_REQUESTS_TOTAL,
    update_uptime,
)

logger = logging.getLogger(settings.app_name)


def _get_http_route(request: Request) -> str:
    route = request.scope.get("route")
    if route and hasattr(route, "path"):
        return route.path
    return request.url.path


async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    http_method = request.method

    PLATFORM_HTTP_REQUESTS_IN_PROGRESS.labels(
        namespace=settings.app_namespace,
        app=settings.app_name,
        service_version=settings.service_version,
        environment=settings.app_env,
    ).inc()

    start = time.perf_counter()

    try:
        response = await call_next(request)
        http_status_code = response.status_code
        http_route = _get_http_route(request)

        duration_seconds = time.perf_counter() - start
        duration_ms = round(duration_seconds * 1000, 2)

        PLATFORM_HTTP_REQUESTS_TOTAL.labels(
            namespace=settings.app_namespace,
            app=settings.app_name,
            service_version=settings.service_version,
            environment=settings.app_env,
            http_method=http_method,
            http_route=http_route,
            http_status_code=str(http_status_code),
        ).inc()

        PLATFORM_HTTP_REQUEST_DURATION_SECONDS.labels(
            namespace=settings.app_namespace,
            app=settings.app_name,
            service_version=settings.service_version,
            environment=settings.app_env,
            http_method=http_method,
            http_route=http_route,
        ).observe(duration_seconds)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request completed",
            extra={
                "service_name": settings.app_name,
                "service_namespace": settings.app_namespace,
                "service_version": settings.service_version,
                "environment": settings.app_env,
                "request_id": request_id,
                "trace_id": None,
                "span_id": None,
                "http_method": http_method,
                "http_route": http_route,
                "http_status_code": http_status_code,
                "duration_ms": duration_ms,
                "error_type": None,
                "error_code": None,
            },
        )

        return response

    except Exception as exc:
        http_route = _get_http_route(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        PLATFORM_HTTP_REQUEST_ERRORS_TOTAL.labels(
            namespace=settings.app_namespace,
            app=settings.app_name,
            service_version=settings.service_version,
            environment=settings.app_env,
            http_method=http_method,
            http_route=http_route,
            error_type=exc.__class__.__name__,
        ).inc()

        PLATFORM_HTTP_REQUESTS_TOTAL.labels(
            namespace=settings.app_namespace,
            app=settings.app_name,
            service_version=settings.service_version,
            environment=settings.app_env,
            http_method=http_method,
            http_route=http_route,
            http_status_code="500",
        ).inc()

        logger.exception(
            "request failed",
            extra={
                "service_name": settings.app_name,
                "service_namespace": settings.app_namespace,
                "service_version": settings.service_version,
                "environment": settings.app_env,
                "request_id": request_id,
                "trace_id": None,
                "span_id": None,
                "http_method": http_method,
                "http_route": http_route,
                "http_status_code": 500,
                "duration_ms": duration_ms,
                "error_type": exc.__class__.__name__,
                "error_code": None,
            },
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "internal server error", "request_id": request_id},
        )

    finally:
        PLATFORM_HTTP_REQUESTS_IN_PROGRESS.labels(
            namespace=settings.app_namespace,
            app=settings.app_name,
            service_version=settings.service_version,
            environment=settings.app_env,
        ).dec()
        update_uptime()
