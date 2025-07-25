"""Configuration for large-scale tests."""

import os
from typing import Dict, Generator, Optional
from unittest.mock import AsyncMock, patch

import pytest
from dotenv import load_dotenv

from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyClient, UnkeyValidationResult

# Load environment variables from .env file
load_dotenv()


async def mock_validate(key: str, required_role: Optional[Role] = None):
    # Simulate different responses based on key pattern for testing
    user_role = None
    key_id = None

    if "admin" in key or key.endswith("_admin"):
        user_role = Role.ADMIN
        key_id = "mock_admin_key_id"
    elif "researcher" in key or key.endswith("_researcher"):
        user_role = Role.RESEARCHER
        key_id = "mock_researcher_key_id"
    elif "experimentee" in key or key.endswith("_experimentee"):
        user_role = Role.EXPERIMENTEE
        key_id = "mock_experimentee_key_id"
    elif "test" in key or key == os.getenv("WAVE_API_KEY"):
        # Use test role for real key and test-pattern keys
        user_role = Role.TEST
        key_id = "test_key_id"
    elif "invalid" in key:
        return UnkeyValidationResult(valid=False, error="Invalid API key")
    else:
        # Default to experimentee for other mock scenarios
        user_role = Role.EXPERIMENTEE
        key_id = "mock_experimentee_key_id"

    # Note: We don't check required_role here - that's handled by the decorator
    # The mock just validates the key exists and returns the user's role

    # Return successful validation
    return UnkeyValidationResult(
        valid=True,
        key_id=key_id,
        role=user_role,
        permissions=[str(user_role).lower()],
        roles=[str(user_role).lower()],
    )


@pytest.fixture
def unkey_api_key() -> str:
    """Get Unkey API key from environment."""
    api_key = os.getenv("WAVE_API_KEY")
    if not api_key:
        pytest.skip("WAVE_API_KEY not set - skipping real Unkey integration tests")
    return api_key


@pytest.fixture
def unkey_app_id() -> str:
    """Get Unkey App ID from environment."""
    app_id = os.getenv("WAVE_APP_ID")
    if not app_id:
        pytest.skip("WAVE_APP_ID not set - skipping real Unkey integration tests")
    return app_id


@pytest.fixture
def real_unkey_client(unkey_api_key: str, unkey_app_id: str) -> UnkeyClient:
    """Create UnkeyClient with real credentials for integration testing."""
    return UnkeyClient(unkey_api_key, unkey_app_id)


@pytest.fixture
def test_role_key() -> str:
    """Get the real test role API key from environment.

    This fixture provides the actual API key that should have 'test' role
    in the Unkey system.
    """
    api_key = os.getenv("WAVE_API_KEY")
    if not api_key:
        pytest.skip("WAVE_API_KEY not set - skipping real integration tests")
    return api_key


@pytest.fixture
def test_keys() -> Dict[str, Optional[str]]:
    """Test API keys - expecting only test role credentials from environment
    Other roles will be simulated via mocking for comprehensive testing"""
    return {
        "test": os.getenv("WAVE_API_KEY"),  # Main test key with "test" role
        "test_app_id": os.getenv("WAVE_APP_ID"),  # App ID for test environment
        "invalid": "sk_invalid_key_12345",  # Always invalid key for negative testing
        "malformed": "invalid_format",  # Malformed key for edge case testing
    }


@pytest.fixture
def mock_unkey_client() -> Generator[AsyncMock, None, None]:
    """Mock UnkeyClient for testing without real API calls."""
    # Clear the LRU cache to avoid using cached real client
    from wave_backend.auth.unkey_client import get_unkey_client

    get_unkey_client.cache_clear()

    # Patch the UnkeyClient.validate_key method directly
    with patch.object(UnkeyClient, "validate_key") as mock_validate_method:
        mock_validate_method.side_effect = mock_validate
        yield mock_validate_method

    # Clear cache after test to ensure clean state
    get_unkey_client.cache_clear()


@pytest.fixture
def mock_network_failure(mock_unkey_client: AsyncMock) -> AsyncMock:
    """Configure mock client to simulate network failures."""
    from wave_backend.auth.unkey_client import UnkeyValidationResult

    # Clear any existing side_effect and set return_value
    mock_unkey_client.side_effect = None
    mock_unkey_client.return_value = UnkeyValidationResult(
        valid=False, error="Timeout connecting to Unkey API"
    )
    return mock_unkey_client


@pytest.fixture
def mock_auth_success(mock_unkey_client: AsyncMock) -> AsyncMock:
    """Configure mock client for successful authentication.

    This fixture simulates different role responses since we only have
    test role credentials in the real environment.
    """
    mock_unkey_client.validate_key.side_effect = mock_validate
    return mock_unkey_client


@pytest.fixture
def mock_insufficient_permissions(mock_unkey_client: AsyncMock) -> AsyncMock:
    """Configure mock client for insufficient permissions scenario."""
    from wave_backend.auth.unkey_client import UnkeyValidationResult

    mock_unkey_client.return_value = UnkeyValidationResult(
        valid=True,
        key_id="test_experimentee_key_id",
        role=Role.EXPERIMENTEE,
        permissions=[],
        roles=["experimentee"],
    )
    return mock_unkey_client
