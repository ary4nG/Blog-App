"""This module provides request context-aware logging using LoggerAdapter."""

from logging import LoggerAdapter
from fastapi import Request
from itaap_python_utils.logging.manager import LogManager


def get_logger(request: Request) -> LoggerAdapter:
    """
    Returns a LoggerAdapter configured with request context (correlation_id,
    trace_id, client_id) from request.state. This will be added as a dependency in each endpoint.

    Args:
        request (Request): FastAPI request object with populated state

    Returns:
        LoggerAdapter: Context-aware logger for the request
    """
    logger = LogManager.get_logger(
        request.state.correlation_id, request.state.trace_id, request.state.client_id
    )
    return logger
