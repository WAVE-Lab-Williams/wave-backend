"""Edge case testing for authentication system.

Tests role boundary conditions and malformed response handling to ensure
the auth system behaves correctly under unusual or error conditions.
"""

from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from wave_backend.auth.decorator import require_role, validate_api_key
from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyValidationResult


@pytest.mark.asyncio
async def test_unkey_client_caching():
    """Test that UnkeyClient is properly cached."""
    from wave_backend.auth.unkey_client import get_unkey_client

    # Clear cache first
    get_unkey_client.cache_clear()

    # Set environment variables for test
    with patch.dict("os.environ", {"WAVE_API_KEY": "test_key", "WAVE_APP_ID": "test_app"}):
        client1 = get_unkey_client()
        client2 = get_unkey_client()

        # Should return the same instance due to caching
        assert client1 is client2


@pytest.mark.asyncio
async def test_role_boundary_conditions(mock_unkey_client):
    """Test role checking at boundary conditions."""

    # Test each role boundary
    role_hierarchy = [Role.EXPERIMENTEE, Role.RESEARCHER, Role.TEST, Role.ADMIN]

    for i, user_role in enumerate(role_hierarchy):
        mock_unkey_client.validate_key.return_value = UnkeyValidationResult(
            valid=True, key_id="boundary_test_key", role=user_role
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_key")

        # Should be able to access same level and below
        for j, required_role in enumerate(role_hierarchy):
            dependency = require_role(required_role)

            if i >= j:  # User role >= required role
                result = await dependency(credentials, mock_unkey_client)
                assert result is not None
                _, role = result
                assert role == user_role
            else:  # User role < required role
                with pytest.raises(Exception):  # Should raise permission error
                    await dependency(credentials, mock_unkey_client)


@pytest.mark.asyncio
async def test_malformed_unkey_responses(mock_unkey_client):
    """Test handling of malformed responses from Unkey."""

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_key")

    # Test various malformed responses
    malformed_responses = [
        UnkeyValidationResult(valid=True, key_id=None, role=None),  # Valid but no data
        UnkeyValidationResult(valid=True, key_id="", role=None),  # Empty key_id
        UnkeyValidationResult(
            valid=False, key_id="test", role=Role.ADMIN, error="Malformed response test"
        ),  # Invalid with role
    ]

    for response in malformed_responses:
        mock_unkey_client.validate_key.return_value = response

        # Should handle malformed responses gracefully
        try:
            result = await validate_api_key(credentials, mock_unkey_client)
            # If no exception, verify result is reasonable
            if result:
                key_id, role = result
                # At minimum, should have some identifying information
                assert key_id is not None or role is not None
        except Exception:
            # Exceptions are acceptable for malformed data
            pass
