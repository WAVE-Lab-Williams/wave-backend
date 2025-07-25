"""Environment configuration tests for authentication system.

Tests proper handling of environment variables, configuration validation,
and deployment scenarios.
"""

import os
from unittest.mock import patch

import pytest

from wave_backend.auth.unkey_client import get_unkey_client


class TestProductionConfigurationScenarios:
    """Test scenarios relevant to production deployment."""

    def test_configuration_from_env_file_simulation(self, mocker):
        """Simulate loading configuration from .env file."""
        # Simulate typical production environment variables
        prod_env = {
            "WAVE_API_KEY": "sk_prod_1234567890abcdef",
            "WAVE_APP_ID": "app_prod_abcd1234",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/wave_prod",
            "FASTAPI_HOST": "0.0.0.0",
            "FASTAPI_PORT": "8000",
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "production",
        }

        with patch.dict(os.environ, prod_env):
            get_unkey_client.cache_clear()

            client = get_unkey_client()
            assert client.api_key == "sk_prod_1234567890abcdef"
            assert client.app_id == "app_prod_abcd1234"

    @pytest.mark.asyncio
    async def test_configuration_validation_with_real_requests(self, mocker):
        """Test that configuration works with actual API requests."""
        # This test requires valid test credentials
        api_key = os.getenv("WAVE_API_KEY")
        app_id = os.getenv("WAVE_APP_ID")

        if not api_key or not app_id:
            pytest.skip("Real Unkey credentials not available")

        with patch.dict(os.environ, {"WAVE_API_KEY": api_key, "WAVE_APP_ID": app_id}):
            get_unkey_client.cache_clear()

            client = get_unkey_client()

            # Test with an invalid key to verify communication
            result = await client.validate_key("sk_invalid_test_key")
            assert result.valid is False
            assert result.error is not None
