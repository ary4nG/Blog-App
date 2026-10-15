"""Test suite for sample.py.
Verifies authentication, authorization formats, and env settings."""

import pytest


class TestSampleEndpoint:
    """Test cases for the /sample endpoint"""

    def test_successful_request(self, client):
        """Test successful API call with valid token and role"""
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_missing_authorization(self, client):
        """Test API call without authorization header"""
        response = client.get("/PROJECT_NAME_PLACEHOLDER/sample")
        assert response.status_code == 401
        assert (
            response.json()["error_desc"]
            == "Authentication failed: Authorization header missing"
        )

    def test_invalid_token_format(self, client):
        """Test API call with incorrectly formatted token"""
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "InvalidToken"},
        )
        assert response.status_code == 401
        assert (
            response.json()["error_desc"]
            == "Authentication failed: Invalid authorization format"
        )

    def test_invalid_bearer_format(self, client):
        """Test API call with invalid bearer format"""
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401
        assert (
            response.json()["error_desc"] == "Authentication failed: Invalid auth type"
        )

    def test_settings_values(self, settings):
        """Verify that mocked settings have correct test values"""
        assert settings.APP_ENV == "build"
