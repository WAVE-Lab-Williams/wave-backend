"""Comprehensive authentication tests with real Unkey integration.

This module tests the auth system with actual Unkey service calls for test role,
and mocked scenarios for comprehensive coverage of other roles.
"""

from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from wave_backend.auth.decorator import validate_api_key
from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyClient, UnkeyValidationResult


class TestAuthDecorators:
    """Test auth decorator functionality with various scenarios."""

    @pytest.mark.asyncio
    async def test_auth_any_with_valid_test_key(
        self, real_unkey_client: UnkeyClient, test_role_key: str
    ):
        """Test @auth.any decorator with valid test role API key."""
        # Test the underlying validation with real test key
        result = await real_unkey_client.validate_key(test_role_key)
        assert result.valid is True
        assert result.key_id is not None
        assert result.role is not None
        # Should be test role since that's what we expect in environment
        assert result.role == Role.TEST

    @pytest.mark.asyncio
    async def test_auth_any_with_invalid_key(self, real_unkey_client: UnkeyClient):
        """Test @auth.any decorator with invalid API key."""
        result = await real_unkey_client.validate_key("sk_invalid_key_12345")
        assert result.valid is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_auth_role_with_test_role_permissions(
        self, real_unkey_client: UnkeyClient, test_role_key: str
    ):
        """Test @auth.role decorator with test role (real integration)."""
        # Test role should have access to EXPERIMENTEE and RESEARCHER endpoints
        result = await real_unkey_client.validate_key(test_role_key, Role.EXPERIMENTEE)
        assert result.valid is True
        assert result.role is not None
        assert result.role.can_access(Role.EXPERIMENTEE)

        result = await real_unkey_client.validate_key(test_role_key, Role.RESEARCHER)
        assert result.valid is True
        assert result.role.can_access(Role.RESEARCHER)

    @pytest.mark.asyncio
    async def test_auth_role_hierarchy_with_mocks(self, mock_auth_success):
        """Test role hierarchy enforcement using mocked scenarios."""
        # Test each role against its allowed access levels using mocks
        role_tests = [
            ("test_admin", Role.ADMIN, [Role.ADMIN, Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("test_test", Role.TEST, [Role.TEST, Role.ADMIN, Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("test_researcher", Role.RESEARCHER, [Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("test_experimentee", Role.EXPERIMENTEE, [Role.EXPERIMENTEE]),
        ]

        for key_pattern, expected_role, allowed_roles in role_tests:
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=key_pattern)

            result = await validate_api_key(credentials, mock_auth_success)
            assert result is not None
            key_id, role = result
            assert role == expected_role

            # Test that this role can access appropriate levels
            for allowed_role in allowed_roles:
                assert role.can_access(allowed_role), f"{role} should access {allowed_role}"

    @pytest.mark.asyncio
    async def test_auth_role_hierarchy(self, real_unkey_client: UnkeyClient, test_keys: dict):
        """Test role hierarchy enforcement."""
        # Test each role against its allowed access levels
        role_tests = [
            ("admin", Role.ADMIN, [Role.ADMIN, Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("test", Role.TEST, [Role.TEST, Role.ADMIN, Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("researcher", Role.RESEARCHER, [Role.RESEARCHER, Role.EXPERIMENTEE]),
            ("experimentee", Role.EXPERIMENTEE, [Role.EXPERIMENTEE]),
        ]

        for key_name, user_role, allowed_roles in role_tests:
            if not test_keys.get(key_name):
                continue

            result = await real_unkey_client.validate_key(test_keys[key_name])
            if result.valid and result.role:
                for allowed_role in allowed_roles:
                    assert result.role.can_access(
                        allowed_role
                    ), f"{user_role} should access {allowed_role}"


class TestAuthIntegrationScenarios:
    """Test comprehensive auth integration scenarios."""

    @pytest.mark.asyncio
    async def test_missing_environment_variables(self):
        """Test behavior when required environment variables are missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="Invalid authentication configuration"):
                from wave_backend.auth.config import get_auth_config
                from wave_backend.auth.unkey_client import get_unkey_client

                get_unkey_client.cache_clear()  # Clear LRU cache
                get_auth_config.cache_clear()  # Clear config cache
                get_unkey_client()

    @pytest.mark.asyncio
    async def test_multiple_rapid_requests(self, mock_auth_success):
        """Test auth system under rapid concurrent requests."""
        import asyncio

        from fastapi.security import HTTPAuthorizationCredentials

        from wave_backend.auth.decorator import validate_api_key

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="admin_key")

        # Simulate multiple concurrent auth requests
        tasks = []
        for _ in range(10):
            task = validate_api_key(credentials, mock_auth_success)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should succeed without interference
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None

    @pytest.mark.asyncio
    async def test_key_rotation_scenario(self, real_unkey_client: UnkeyClient, test_keys: dict):
        """Test behavior when API keys are rotated/invalidated."""
        # Test with a definitely invalid key
        result = await real_unkey_client.validate_key("sk_definitely_invalid_12345")
        assert result.valid is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_edge_case_keys(self, real_unkey_client: UnkeyClient):
        """Test edge cases with various key formats."""
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "sk_",  # Incomplete key
            "not_a_key_at_all",  # Wrong format
            "sk_" + "a" * 1000,  # Very long key
        ]

        for edge_key in edge_cases:
            result = await real_unkey_client.validate_key(edge_key)
            assert result.valid is False
            assert result.error is not None


class TestRoleExtractionScenarios:
    """Test role extraction from various Unkey response formats."""

    @pytest.mark.asyncio
    async def test_role_from_roles_array(self, mock_unkey_client):
        """Test role extraction from Unkey roles array."""
        mock_unkey_client.validate_key.return_value = UnkeyValidationResult(
            valid=True,
            key_id="test_key",
            role=Role.RESEARCHER,
            roles=["researcher"],
            permissions=["read", "write"],
        )

        from fastapi.security import HTTPAuthorizationCredentials

        from wave_backend.auth.decorator import validate_api_key

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_key")
        result = await validate_api_key(credentials, mock_unkey_client)

        key_id, role = result
        assert role == Role.RESEARCHER

    @pytest.mark.asyncio
    async def test_role_from_meta(self, mock_unkey_client):
        """Test role extraction from meta field."""
        mock_unkey_client.validate_key.return_value = UnkeyValidationResult(
            valid=True,
            key_id="test_key",
            role=Role.ADMIN,
            meta={"role": "admin", "other_data": "value"},
        )

        from fastapi.security import HTTPAuthorizationCredentials

        from wave_backend.auth.decorator import validate_api_key

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_key")
        result = await validate_api_key(credentials, mock_unkey_client)

        key_id, role = result
        assert role == Role.ADMIN

    @pytest.mark.asyncio
    async def test_no_role_found(self, mock_unkey_client):
        """Test behavior when no role is found in response."""
        mock_unkey_client.validate_key.return_value = UnkeyValidationResult(
            valid=True,
            key_id="test_key",
            role=None,  # No role found
            permissions=["some_permission"],
        )

        from fastapi.security import HTTPAuthorizationCredentials

        from wave_backend.auth.decorator import validate_api_key

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_key")

        with pytest.raises(Exception):  # Should raise exception for missing role
            await validate_api_key(credentials, mock_unkey_client)
