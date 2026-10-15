"""Configuration settings for Integration testing environment"""

import os
from dotenv import load_dotenv

load_dotenv()


class TestConfig:
    """Test configuration class with constants for test cases."""

    BASE_URL = "/PROJECT_NAME_PLACEHOLDER"
    TOKEN_CLIENT_ID = os.getenv("TOKEN_CLIENT_ID")
    TOKEN_CLIENT_SECRET = os.getenv("TOKEN_CLIENT_SECRET")
    TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT")
    TOKEN_SCOPE = os.getenv("TOKEN_SCOPE")
    REQUIRED_ROLE = os.getenv("SAMPLE_API_ROLE")
