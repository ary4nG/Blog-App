"""Exception handling middleware for FastAPI integration."""

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from itaap_python_utils.exceptions.handler import GlobalExceptionHandler
from itaap_python_utils.exceptions.base import ServiceException
from itaap_python_utils.logging.manager import LogManager
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from app.config.settings import settings

# Initialize the global exception handler
exception_handler = GlobalExceptionHandler()
tracer = trace.get_tracer(__name__)


async def handle_exception(
    request: Request, exc: Exception, is_service_error: bool = False
):
    """Common exception handler for both service and generic exceptions."""
    correlation_id = getattr(request.state, "correlation_id", None)
    trace_id = getattr(request.state, "trace_id", None)
    client_id = getattr(request.state, "client_id", None)

    error_response, status_code = exception_handler.handle_exception(
        exc, correlation_id=correlation_id
    )

    if settings.SEND_TELEMETRY_DATA.lower() == "true" and is_service_error:
        with tracer.start_span("exception_handling") as span:
            # Set error status
            span.set_status(Status(StatusCode.ERROR))

            # Add basic error details
            span.set_attribute("error.type", exc.__class__.__name__)
            span.set_attribute("error.message", str(exc))

            # Record the exception
            span.record_exception(exc)

    logger = LogManager.get_logger(correlation_id, trace_id, client_id)
    error_type = "Service" if is_service_error else "Unhandled"
    logger.error(
        f"{error_type} exception occurred: {str(exc)}\n{traceback.format_exc()}"
    )

    return JSONResponse(status_code=status_code, content=vars(error_response))


async def handle_service_exception(request: Request, exc: ServiceException):
    """Handle ServiceException instances."""
    return await handle_exception(request, exc, is_service_error=True)


async def handle_generic_exception(request: Request, exc: Exception):
    """Handle all other exceptions."""
    return await handle_exception(request, exc)
