"""
Sample FastAPI routers demonstrating best practices and common patterns.

This module serves as a template for implementing API endpoints in a FastAPI application.
It showcases:
- Role-based authorization using RoleChecker
- Structured logging with LoggerAdapter
- FastAPI dependency injection pattern
- Global exception handling
"""

from typing import Annotated
from logging import LoggerAdapter


from fastapi import APIRouter, Depends

from app.dependencies.jwt_auth import RoleChecker
from app.dependencies.logger import get_logger
from app.config.settings import settings
from app.exceptions.error_factory import service_error_factory
from app.exceptions.service_errors import ServiceErrors


user_detail_error = ServiceErrors.USERDETAIL.value
error_factory = service_error_factory


router = APIRouter()


@router.get("/sample")
async def root(
    role_check: Annotated[RoleChecker, Depends(RoleChecker(settings.SAMPLE_API_ROLE))],
    logger: Annotated[LoggerAdapter, Depends(get_logger)],
):
    """
    Sample API to demo authentication, authorization, & logging feature .

    Dependencies:
        - role_check: Ensures user has the required role access
        - logger: Provides structured logging capability

    Returns:
        dict: A simple response demonstrating successful API access
    """
    logger.info("Root endpoint accessed")
    logger.debug("Testing env variable LOG_LEVEL_APP")

    return {"message": "Hello World"}
