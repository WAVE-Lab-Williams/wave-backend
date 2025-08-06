"""Authentication configuration management."""

import os
from functools import lru_cache

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration with validation."""

    api_key: str = Field(..., min_length=1, description="Unkey root API key for validation")
    app_id: str = Field(..., min_length=1, description="Unkey application ID")
    cache_ttl_seconds: int = Field(
        default=300, description="Authentication cache TTL in seconds", gt=0, le=3600
    )
    base_url: str = Field(default="https://api.unkey.com", description="Unkey API base URL")
    timeout_seconds: float = Field(
        default=10.0, description="HTTP request timeout in seconds", gt=0, le=60.0
    )


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
    try:
        return AuthConfig(
            api_key=os.getenv("WAVE_API_KEY", ""),
            app_id=os.getenv("WAVE_APP_ID", ""),
            cache_ttl_seconds=int(os.getenv("WAVE_AUTH_CACHE_TTL", "300")),
            base_url=os.getenv("WAVE_AUTH_BASE_URL", "https://api.unkey.com"),
            timeout_seconds=float(os.getenv("WAVE_AUTH_TIMEOUT", "10.0")),
        )
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid authentication configuration: {e}")
