from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def setup_tracing(app, settings) -> None:
    if not settings.tracing_enabled:
        logger.info("tracing disabled")
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.namespace": settings.otel_service_namespace,
        "deployment.environment": "production",
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,ready,metrics")

    logger.info(
        "tracing enabled",
        extra={"endpoint": settings.otel_exporter_otlp_endpoint, "service": settings.otel_service_name},
    )

