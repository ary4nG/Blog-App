"""
Steps for authentication and token management in integration tests.
"""

import requests
from behave import given, then  # pylint: disable=no-name-in-module
from tests.integration.test_config import TestConfig


@given("I have acquired a valid token with required role")
def step_acquire_valid_token(context):
    """Obtain a valid JWT token from Azure AD"""
    client_id = TestConfig.TOKEN_CLIENT_ID
    client_secret = TestConfig.TOKEN_CLIENT_SECRET
    scope = TestConfig.TOKEN_SCOPE

    if not client_id or not client_secret:
        raise ValueError(
            "Missing credentials for token acquisition. "
            "Please set TOKEN_CLIENT_ID, TOKENCLIENT_SECRET, TOKEN_SCOPE in your .env file."
        )

    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }

    try:
        response = requests.post(
            TestConfig.TOKEN_ENDPOINT, data=token_data, timeout=10.0
        )
        assert response.status_code == 200, f"Failed to obtain token: {response.text}"

        token_json = response.json()
        access_token = token_json.get("access_token")
        assert access_token, "No access token returned"

        context.token = access_token
        context.headers["Authorization"] = f"Bearer {access_token}"
    except requests.RequestException as e:
        raise AssertionError(f"Failed to connect to token endpoint: {str(e)}") from e


@given("I have no authorization header")
def step_remove_auth_header(context):
    """Remove the authorization header for testing authentication failures."""
    if "Authorization" in context.headers:
        del context.headers["Authorization"]


@then("the response indicates an authentication error")
def step_verify_auth_error(context):
    """Verify that the response indicates an authentication error."""
    assert context.response.status_code == 401
    error_data = context.response.json()
    assert "error_code" in error_data
    assert "error_desc" in error_data
    assert "correlation_id" in error_data
    assert error_data["error_code"] == 401
