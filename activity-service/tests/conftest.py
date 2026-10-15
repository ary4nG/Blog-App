"""This module contains configs and fixtures for testing with pytest
in a FastAPI application."""

from unittest.mock import Mock, patch
import pytest
from fastapi.testclient import TestClient
from app.config.settings import Settings
from app.main import app


@pytest.fixture(name="settings_instance")
def fixture_settings_instance():
    """Default test settings values"""
    return Settings.get_unit_test_settings()


@pytest.fixture(autouse=True, name="settings")
def fixture_mock_settings(settings_instance):
    """Create a mock settings instance with test values"""
    with patch("app.config.settings.settings", settings_instance):
        yield settings_instance


@pytest.fixture(name="token_checker")
def fixture_mock_token_checker():
    """Mocks the JWT token checker for testing."""
    with patch("app.dependencies.jwt_auth.token_checker") as mock:
        mock.validate_token.return_value = "test-client-id"
        mock.verify_roles.return_value = True
        yield mock


@pytest.fixture(name="logger")
def fixture_mock_logger():
    "Mocks the logger for testing."
    with patch("app.dependencies.logger.LogManager") as mock:
        mock_logger = Mock()
        mock.get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def client(token_checker, logger, settings):
    """Creates a TestClient instance for sending requests to the FastAPI application.

    This fixture initializes a TestClient with the application instance,
    allowing for easy simulation of requests in tests."""
    return TestClient(app)
