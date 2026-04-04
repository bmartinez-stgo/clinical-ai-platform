import time

from prometheus_client import Counter, Gauge, Histogram


class PlatformMetrics:
    def __init__(self):
        self.start_time = time.time()

        self.http_requests_total = Counter(
            "platform_http_requests_total",
            "Total HTTP requests",
            [
                "service_name",
                "service_namespace",
                "http_method",
                "http_route",
                "http_status_code",
            ],
        )

        self.http_request_duration_seconds = Histogram(
            "platform_http_request_duration_seconds",
            "HTTP request duration in seconds",
            [
                "service_name",
                "service_namespace",
                "http_method",
                "http_route",
                "http_status_code",
            ],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
        )

        self.http_requests_in_progress = Gauge(
            "platform_http_requests_in_progress",
            "HTTP requests in progress",
            [
                "service_name",
                "service_namespace",
                "http_method",
                "http_route",
                "http_status_code",
            ],
        )

        self.http_errors_total = Counter(
            "platform_http_errors_total",
            "Total HTTP error responses",
            [
                "service_name",
                "service_namespace",
                "http_method",
                "http_route",
                "http_status_code",
            ],
        )

        self.service_info = Gauge(
            "platform_service_info",
            "Service info",
            [
                "service_name",
                "service_namespace",
                "service_version",
                "environment",
            ],
        )

        self.service_uptime_seconds = Gauge(
            "platform_service_uptime_seconds",
            "Service uptime in seconds",
            [
                "service_name",
                "service_namespace",
            ],
        )

        self._service_name = None
        self._service_namespace = None

    def set_service_info(
        self,
        service_name: str,
        service_namespace: str,
        service_version: str,
        environment: str,
    ) -> None:
        self._service_name = service_name
        self._service_namespace = service_namespace

        self.service_info.labels(
            service_name=service_name,
            service_namespace=service_namespace,
            service_version=service_version,
            environment=environment,
        ).set(1)

        self.update_uptime()

    def update_uptime(self) -> None:
        if not self._service_name or not self._service_namespace:
            return

        self.service_uptime_seconds.labels(
            service_name=self._service_name,
            service_namespace=self._service_namespace,
        ).set(time.time() - self.start_time)


metrics = PlatformMetrics()
