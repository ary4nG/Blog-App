"""Environment configuration for Behave tests."""

from fastapi.testclient import TestClient
from app.main import app


def before_all(context):
    """Initialize test client and shared context before all tests."""
    context.client = TestClient(app)
    context.token = None
    context.response = None

    # Set default headers
    context.headers = {"X-Correlation-ID": "behave-test-correlation-id"}


def before_scenario(context, scenario):
    """Reset scenario-specific state before each scenario."""
    context.response = None
    context.status_code = None
