"""
TraceContextMiddleware — injects trace_id and request_id into every request.

- Reads X-Request-ID header (or generates UUID)
- Extracts trace_id from the active OpenTelemetry span
- Binds both to structlog context vars
- Sets X-Trace-ID and X-Request-ID response headers
"""
from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Binds tracing context for every HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Request ID (from header or auto-generated)
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # 2. Trace ID from OTEL span (if available)
        trace_id: str | None = None
        try:
            from opentelemetry import trace as otel_trace

            span = otel_trace.get_current_span()
            ctx = span.get_span_context()
            if ctx and ctx.trace_id:
                trace_id = format(ctx.trace_id, "032x")
        except Exception:
            pass

        trace_id = trace_id or request_id

        # 3. Bind to structlog context vars
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
        )

        # 4. Store on request.state for downstream handlers
        request.state.trace_id = trace_id
        request.state.request_id = request_id

        response: Response = await call_next(request)

        # 5. Echo IDs in response headers
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Request-ID"] = request_id

        # 6. Clear context vars
        structlog.contextvars.clear_contextvars()

        return response
