import pytest
from fastapi.testclient import TestClient

from wave_backend.api.main import app
from wave_backend.auth.roles import Role


@pytest.fixture
def mock_auth():
    """Mock authentication for tests that need it."""
    from unittest.mock import patch

    from wave_backend.auth.unkey_client import UnkeyClient, UnkeyValidationResult

    async def mock_validate(key: str, required_role=None):
        """Mock validation that always returns TEST role."""
        return UnkeyValidationResult(
            valid=True,
            key_id="test_key_id",
            role=Role.TEST,
            permissions=["test"],
            roles=["test"],
        )

    # Clear the LRU cache to avoid using cached real client
    from wave_backend.auth.unkey_client import get_unkey_client

    get_unkey_client.cache_clear()

    # Patch the UnkeyClient.validate_key method directly
    with patch.object(UnkeyClient, "validate_key") as mock_validate_method:
        mock_validate_method.side_effect = mock_validate
        yield

    # Clear cache after test to ensure clean state
    get_unkey_client.cache_clear()


@pytest.fixture
def test_client() -> TestClient:
    """Test client fixture for unit tests."""
    return TestClient(app)
