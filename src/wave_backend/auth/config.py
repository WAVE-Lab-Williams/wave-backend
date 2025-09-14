"""Authentication configuration management."""

import os
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator


class AuthConfig(BaseModel):
    """Authentication configuration with validation."""

    api_key: str = Field(..., min_length=1, description="Unkey root API key for validation")
    cache_ttl_seconds: int = Field(
        default=60, description="Authentication cache TTL in seconds", gt=0, le=3600
    )
    base_url: str = Field(default="https://api.unkey.com/v2", description="Unkey API base URL")
    timeout_seconds: float = Field(
        default=10.0, description="HTTP request timeout in seconds", gt=0, le=60.0
    )

    @field_validator("base_url")
    @classmethod
    def remove_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from base URL for proper concatenation."""
        return v.rstrip("/")


@lru_cache(maxsize=1)
def get_auth_config() -> AuthConfig:
    """
    Get authentication configuration from environment variables.
    Uses LRU cache to ensure configuration is loaded only once.

    Returns:
        AuthConfig instance with validated configuration

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    # Check for required environment variable first
    root_key = os.getenv("ROOT_VALIDATOR_KEY", "")
    if not root_key:
        raise ValueError(
            "MISSING ROOT_VALIDATOR_KEY: The ROOT_VALIDATOR_KEY environment variable must be set. "
            "This should be your Unkey root API key with 'api.*.verify_key' permission."
        )

    try:
        config_data = {
            "api_key": root_key,
        }

        # Only set optional fields if environment variable exists
        if cache_ttl := os.getenv("WAVE_AUTH_CACHE_TTL"):
            config_data["cache_ttl_seconds"] = int(cache_ttl)
        if base_url := os.getenv("WAVE_AUTH_BASE_URL"):
            config_data["base_url"] = base_url
        if timeout := os.getenv("WAVE_AUTH_TIMEOUT"):
            config_data["timeout_seconds"] = float(timeout)

        return AuthConfig(**config_data)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid authentication configuration: {e}")
