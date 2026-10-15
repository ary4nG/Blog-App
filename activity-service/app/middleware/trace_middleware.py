"""FastAPI middleware for request tracing and correlation.
Handles correlation ID and trace ID assignment for request tracking."""

import uuid
from typing import Callable
from fastapi import Request
from opentelemetry import trace
from app.config.settings import settings


async def trace_middleware(request: Request, call_next: Callable):
    """FastAPI middleware for tracing and correlation of HTTP requests.

    This middleware performs the following operations:
    - Extracts existing correlation ID from request headers or generates a new one
    - Creates an OpenTelemetry span for the request with relevant attributes
    - Sets correlation ID and trace ID in request state for access by route handlers
    - Adds correlation ID to response headers for end-to-end tracing
    - Conditionally enables/disables telemetry based on application settings"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    if settings.SEND_TELEMETRY_DATA.lower() == "true":
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}"
        ) as span:
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("app_name", settings.APP_NAME)
            span.set_attribute("app_version", settings.APP_VERSION)
            span.set_attribute("environment", settings.APP_ENV)
            span.set_attribute("request_method", request.method)
            span.set_attribute("request_url", request.url.path)

            request.state.trace_id = format(span.get_span_context().trace_id, "032x")

            response = await call_next(request)

            span.set_attribute("http.status_code", response.status_code)
    else:
        request.state.trace_id = ""
        response = await call_next(request)

    response.headers.update({"X-Correlation-ID": correlation_id})

    return response
