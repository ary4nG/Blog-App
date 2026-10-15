"""
Application configuration management system.

Settings are managed using Pydantic's BaseSettings with a multi-level configuration approach:
1. Environment variables (highest priority)
2. .env file in the project root
3. Default values defined in the Settings class
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings class that manages environment-based configuration.

    Attributes:
        APP_NAME: Application name identifier
        APP_ENV: Environment name (dev/test/acc/prod/)
        APP_VERSION: Application version
        JWT_AUDIENCE: JWT token audience value
        JWKS_URL: URL endpoint for JSON Web Key Set to verify token signatures
        SAMPLE_API_ROLE: Role required for sample API access
        LOG_LEVEL_APP: Application logging level, defaults to "INFO"
        ELASTICSEARCH_URL: Connection URL for Elasticsearch telemetry data storage
        ELASTICSEARCH_USERNAME: Authentication username for Elasticsearch access
        ELASTICSEARCH_PASSWORD: Authentication password for Elasticsearch access
        SEND_TELEMETRY_DATA: Flag to enable/disable sending telemetry data to Elasticsearch
    """

    APP_NAME: str = "activity-service"
    JWT_AUDIENCE: str = "**Fill your JWT audience value here**"
    JWKS_URL: str = (
        "https://login.microsoftonline.com/1a407a2d-7675-4d17-8692-b3ac285306e4/discovery/v2.0/keys"
    )
    SAMPLE_API_ROLE: str = "api.status"
    LOG_LEVEL_APP: str = "INFO"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    APP_ENV: str = ""
    AUTH_DISABLED: bool = False
    APP_VERSION: str = ""
    ELASTICSEARCH_URL: str = ""
    ELASTICSEARCH_USERNAME: str = ""
    ELASTICSEARCH_PASSWORD: str = ""
    SEND_TELEMETRY_DATA: str = "false"
    ELASTIC_INDEX_PREFIX: str = "activity-service"

    class Config:
        """Configuration class for Pydantic BaseSettings behavior."""

        env_file = ".env"
        extra = "allow"  # Allow extra fields not defined in the class

    @classmethod
    def get_unit_test_settings(cls):
        """Creates settings for unit testing with mocked external services.
        
        Inherits default values from environment but overrides external service 
        connections with dummy values to prevent actual API calls during unit tests."""

        settings = cls()
        settings.APP_ENV = "build"
        settings.APP_VERSION = "1.0.0-unit-test"

        settings.ELASTICSEARCH_URL = "dummy_url"
        settings.ELASTICSEARCH_USERNAME = "dummy_username"
        settings.ELASTICSEARCH_PASSWORD = "dummy_password"

        return settings
        
    @classmethod
    def get_integration_test_settings(cls):
        """
        Creates settings for integration testing with real external services.
        
        Inherits values from environment variables including real credentials for
        external services. Only overrides application metadata for test identification.
        This allows integration tests to verify actual connections to external systems.
        """

        settings = cls()
        
        settings.APP_ENV = "build"
        settings.APP_VERSION = "1.0.0-integration-test"
        
        return settings

@lru_cache
def get_settings() -> Settings:
    """
    Get application settings, either from environment variables or test settings.
    
    - For unit tests (UNIT_TESTING_MODE=true): Use mocked services
    - For integration tests (INTEGRATION_TESTING_MODE=true): Use real services
    - For normal operation: Use standard settings

    Returns:
        Settings: The configuration settings for the application.
    """
    if os.environ.get("UNIT_TESTING_MODE", "").lower() == "true":
        return Settings.get_unit_test_settings()
    
    if os.environ.get("INTEGRATION_TESTING_MODE", "").lower() == "true":
        return Settings.get_integration_test_settings()

    return Settings()


# Initialize settings using the factory function
settings = get_settings()