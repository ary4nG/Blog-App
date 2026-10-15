"""
Steps for testing API endpoints in integration tests.
"""

from behave import then, when  # pylint: disable=no-name-in-module
from tests.integration.test_config import TestConfig


@when('I send a GET request to "{endpoint}"')
def step_send_get_request(context, endpoint):
    """Send a GET request to the specified endpoint."""
    url = f"{TestConfig.BASE_URL}{endpoint}"
    context.response = context.client.get(url, headers=context.headers)
    context.status_code = context.response.status_code


@then("the response status code is {status_code:d}")
def step_verify_status_code(context, status_code):
    """Verify that the response has the expected status code."""
    assert context.status_code == status_code


@then("the response body contains a message")
def step_verify_response_message(context):
    """Verify that the response body contains a message field."""
    response_json = context.response.json()
    assert "message" in response_json, "Response does not contain a message field"


@then("the response contains a correlation ID header")
def step_verify_correlation_id(context):
    """Verify that the response contains the X-Correlation-ID header."""
    assert "X-Correlation-ID" in context.response.headers
