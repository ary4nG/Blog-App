"""Service exception configuration and initialization."""

from itaap_python_utils.exceptions.factory import ServiceErrorsFactory
from app.exceptions.service_errors import ServiceErrors


def setup_error_factory() -> ServiceErrorsFactory:
    """Initialize and configure error factory with predefined exceptions."""
    factory = ServiceErrorsFactory()

    # Register all errors from enum
    for error in ServiceErrors:
        factory.register_error(
            error.value.name,
            error_code=error.value.error_code,
            error_desc_template=error.value.template,
            status_code=error.value.status_code,
        )

    return factory


# Create singleton instance
service_error_factory = setup_error_factory()
