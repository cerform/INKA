"""
Tests for libs/observability.

These tests validate the observability stack without needing
Docker or GCP credentials — everything runs with in-process mocks.
"""
from __future__ import annotations

import logging
import json
import io
import sys


def test_setup_logging_json_output():
    """In non-development mode, logs should be valid JSON with required fields."""
    from libs.observability.src.logging_config import setup_logging

    # Capture stdout
    captured = io.StringIO()
    handler = logging.StreamHandler(captured)

    setup_logging(log_level="INFO", environment="production", service_name="test-svc")

    # Replace handler to capture output
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)

    logger = logging.getLogger("test.json")
    logger.info("hello world")

    output = captured.getvalue().strip()
    assert output, "Expected log output but got nothing"

    parsed = json.loads(output)
    assert parsed["event"] == "hello world"
    assert parsed["service"] == "test-svc"
    assert parsed["env"] == "production"


def test_setup_logging_dev_mode():
    """In development mode, logging should not raise and should use console renderer."""
    from libs.observability.src.logging_config import setup_logging

    # Should not raise
    setup_logging(log_level="DEBUG", environment="development", service_name="dev-svc")


def test_setup_sentry_noop_without_dsn():
    """setup_sentry with no DSN should be a complete no-op."""
    from libs.observability.src.sentry_config import setup_sentry

    # Should not raise or import sentry at all
    setup_sentry(dsn=None, environment="test")
    setup_sentry(dsn="", environment="test")


def test_get_current_trace_id_without_span():
    """Without an active span, get_current_trace_id should return None or a zero trace."""
    from libs.observability.src.tracing import get_current_trace_id

    result = get_current_trace_id()
    # Without a provider/span, this should be None or the invalid trace id
    assert result is None or result == "0" * 32


def test_trace_context_middleware_sets_headers():
    """TraceContextMiddleware should add X-Trace-ID and X-Request-ID to responses."""
    import asyncio
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from libs.observability.src.middleware import TraceContextMiddleware

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(TraceContextMiddleware)

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "x-trace-id" in response.headers
    assert "x-request-id" in response.headers
    # Should be a valid UUID or trace id
    assert len(response.headers["x-request-id"]) >= 32


def test_trace_context_middleware_preserves_request_id():
    """If X-Request-ID is sent, the middleware should echo it back."""
    import asyncio
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from libs.observability.src.middleware import TraceContextMiddleware

    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(TraceContextMiddleware)

    client = TestClient(app)
    custom_id = "my-custom-request-id-12345"
    response = client.get("/", headers={"x-request-id": custom_id})

    assert response.headers["x-request-id"] == custom_id
