"""
JWT token authentication and role-based authorization handlers.

Provides:
- TokenValidator for validating JWT tokens in request headers
- RoleChecker for enforcing role-based access control
"""

from fastapi import Request
from itaap_python_utils.auth.jwt_token_checker import JWTTokenChecker
from itaap_python_utils.auth.exceptions import (
    InvalidTokenFormatError,
    InvalidSignatureError,
    TokenExpiredError,
    InvalidAudienceError,
    InvalidTenantError,
    InvalidRoleError,
)
from app.exceptions.error_factory import service_error_factory
from app.exceptions.service_errors import ServiceErrors
from app.config.settings import settings
import logging
logger = logging.getLogger(__name__)
auth_error = ServiceErrors.AUTHENTICATION.value
error_factory = service_error_factory

token_checker = JWTTokenChecker(
    algorithm="RS256", jwks_url=settings.JWKS_URL, audience=settings.JWT_AUDIENCE
)

def _auth_bypassed()->bool:
    if settings.AUTH_DISABLED and settings.APP_ENV=="local":
        return True
    return False
def get_auth_header(request: Request) -> str:
    """Extract the 'Authorization' header from the request."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        error_factory.raise_exception(auth_error, reason="Authorization header missing")

    try:
        auth_type, token = auth_header.split(" ", 1)
        if auth_type.lower() != "bearer":
            error_factory.raise_exception(auth_error, reason="Invalid auth type")
        return token
    except ValueError:
        error_factory.raise_exception(auth_error, reason="Invalid authorization format")


class TokenValidator:
    """A class to validate the Bearer token from the Authorization header."""
    

    def __call__(self, request: Request) -> bool:
        """Checks the 'Authorization' header for a valid Bearer token."""
        try:
            if _auth_bypassed():
                request.state.client_id = "local_dev"
                logger.warning("AUTH bypassed: local dev")
                return True
            token = get_auth_header(request)
            token_appid = token_checker.validate_token(token)
            request.state.client_id = token_appid
        except (
            InvalidTokenFormatError,
            InvalidSignatureError,
            TokenExpiredError,
            InvalidAudienceError,
            InvalidTenantError,
        ) as e:
            error_factory.raise_exception(auth_error, reason=str(e))
        return True


class RoleChecker:
    """Verifies that a request contains a valid Bearer token and checks for the specified role."""

    def __init__(self, required_role: str = None):
        self.required_role = required_role
    
    async def __call__(self, request: Request) -> bool:
        try:
            if _auth_bypassed():
                return True
            token = get_auth_header(request)
            token_checker.verify_roles(token, self.required_role)
        except (InvalidTokenFormatError, InvalidRoleError, InvalidSignatureError) as e:
            error_factory.raise_exception(auth_error, reason=str(e))
        return True
