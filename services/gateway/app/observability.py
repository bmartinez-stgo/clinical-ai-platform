import platform
import sys
import time

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.config import settings

SERVICE_START_TIME = time.time()

PLATFORM_HTTP_REQUESTS_TOTAL = Counter(
    "platform_http_requests_total",
    "Total HTTP requests",
    ["namespace", "app", "service_version", "environment", "http_method", "http_route", "http_status_code"],
)

PLATFORM_HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "platform_http_request_duration_seconds",
    "HTTP request duration seconds",
    ["namespace", "app", "service_version", "environment", "http_method", "http_route"],
)

PLATFORM_HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "platform_http_requests_in_progress",
    "In progress HTTP requests",
    ["namespace", "app", "service_version", "environment"],
)

PLATFORM_HTTP_REQUEST_ERRORS_TOTAL = Counter(
    "platform_http_request_errors_total",
    "Total HTTP request errors",
    ["namespace", "app", "service_version", "environment", "http_method", "http_route", "error_type"],
)

PLATFORM_SERVICE_INFO = Gauge(
    "platform_service_info",
    "Service information",
    ["namespace", "app", "service_version", "environment", "runtime", "runtime_version"],
)

PLATFORM_SERVICE_UPTIME_SECONDS = Gauge(
    "platform_service_uptime_seconds",
    "Service uptime in seconds",
    ["namespace", "app", "service_version", "environment"],
)


def initialize_service_metrics() -> None:
    PLATFORM_SERVICE_INFO.labels(
        namespace=settings.app_namespace,
        app=settings.app_name,
        service_version=settings.service_version,
        environment=settings.app_env,
        runtime=platform.python_implementation().lower(),
        runtime_version=sys.version.split(" ")[0],
    ).set(1)


def update_uptime() -> None:
    PLATFORM_SERVICE_UPTIME_SECONDS.labels(
        namespace=settings.app_namespace,
        app=settings.app_name,
        service_version=settings.service_version,
        environment=settings.app_env,
    ).set(time.time() - SERVICE_START_TIME)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
