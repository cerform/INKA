"""
OpenTelemetry distributed tracing setup.

- Cloud Trace exporter in production
- ConsoleSpanExporter for local development
- Auto-instruments FastAPI, SQLAlchemy, Redis
"""
from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "inka-api", environment: str = "development") -> None:
    """
    Initialise the OpenTelemetry TracerProvider and auto-instrumentors.

    In production: exports spans to Google Cloud Trace.
    In development: prints spans to stdout via ConsoleSpanExporter.
    """
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": environment,
        }
    )

    provider = TracerProvider(resource=resource)

    if environment == "development":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            exporter = CloudTraceSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("Cloud Trace exporter initialised")
        except Exception:
            logger.warning(
                "Cloud Trace exporter unavailable, falling back to console",
                exc_info=True,
            )
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    # Auto-instrument libraries (best-effort, skip if not installed)
    _instrument_fastapi()
    _instrument_sqlalchemy()
    _instrument_redis()

    logger.info("OpenTelemetry tracing initialised for %s (%s)", service_name, environment)


def _instrument_fastapi() -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument()
    except ImportError:
        pass


def _instrument_sqlalchemy() -> None:
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_redis() -> None:
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except ImportError:
        pass


def get_current_trace_id() -> str | None:
    """Return the current trace ID as a hex string, or None."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return format(ctx.trace_id, "032x")
    return None
