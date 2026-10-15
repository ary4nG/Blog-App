"""Test suite for authentication and authorization mechanisms.
Covers token validation, expiry handling, and role-based access control."""

import pytest

from itaap_python_utils.auth.exceptions import (
    TokenExpiredError,
    InvalidRoleError,
    InvalidTokenFormatError,
)


class TestAuthentication:
    """Test cases for authentication functionality"""

    def test_valid_token_validation(self, client, token_checker):
        """Test successful token validation"""
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        token_checker.validate_token.assert_called_once()

    def test_invalid_token(self, client, token_checker):
        """Test invalid token handling"""
        token_checker.validate_token.side_effect = InvalidTokenFormatError(
            "Invalid token"
        )
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert response.json()["error_desc"] == "Authentication failed: Invalid token"

    def test_expired_token(self, client, token_checker):
        """Test expired token handling"""
        token_checker.validate_token.side_effect = TokenExpiredError("Token expired")
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer expired-token"},
        )
        assert response.status_code == 401
        assert response.json()["error_desc"] == "Authentication failed: Token expired"
        assert response.json()["error_code"] == 401

    def test_invalid_role(self, client, token_checker):
        """Test invalid role handling"""
        token_checker.verify_roles.side_effect = InvalidRoleError("Invalid role")
        response = client.get(
            "/PROJECT_NAME_PLACEHOLDER/sample",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 401
        assert response.json()["error_desc"] == "Authentication failed: Invalid role"
