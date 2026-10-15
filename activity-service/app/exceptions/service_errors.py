"""Configuration for service-level errors."""

from enum import Enum
from itaap_python_utils.exceptions.factory import ErrorConfig


class ServiceErrors(Enum):
    """Enumeration of all service-level errors."""

    AUTHENTICATION = ErrorConfig(
        "AuthenticationError", 401, "Authentication failed: {reason}", 401
    )
    USERDETAIL = ErrorConfig("UserDetailNotFound", 4041, "User detail not found", 404)

    # Add your service exceptions below
    # Follow the format:
    # ERROR_NAME = ErrorConfig(
    #     "ErrorClassName",
    #     error_code,
    #     "Error message with optional {placeholder}",
    #     appropriate_http_status_code
    # )
