"""Unit tests for UnkeyClient caching functionality."""

import time
from unittest.mock import AsyncMock, patch

import pytest

from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import (
    CachedValidationResult,
    UnkeyClient,
    UnkeyValidationResult,
)


class TestCachedValidationResult:
    """Test the caching wrapper class."""

    def test_cached_result_not_expired(self):
        """Test that non-expired cached results are valid."""
        result = UnkeyValidationResult(valid=True, key_id="test_key", role=Role.RESEARCHER)
        cached = CachedValidationResult(result, ttl_seconds=300)

        assert not cached.is_expired()
        assert cached.result == result

    def test_cached_result_expired(self):
        """Test that expired cached results are detected."""
        result = UnkeyValidationResult(valid=True, key_id="test_key", role=Role.RESEARCHER)
        cached = CachedValidationResult(result, ttl_seconds=0)

        # Sleep briefly to ensure expiration
        time.sleep(0.01)
        assert cached.is_expired()


class TestUnkeyClientCaching:
    """Test UnkeyClient caching functionality."""

    def test_cache_key_generation(self):
        """Test cache key generation with different parameters."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        key = "sk_abcdefghijklmnopqrstuvwxyz123456789"

        # Test without required role
        cache_key1 = client._get_cache_key(key)
        assert cache_key1 == "sk_abcde...23456789:none"

        # Test with required role
        cache_key2 = client._get_cache_key(key, Role.RESEARCHER)
        assert cache_key2 == "sk_abcde...23456789:researcher"

    def test_cache_result_successful(self):
        """Test caching of successful validation results."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        result = UnkeyValidationResult(valid=True, key_id="test_key", role=Role.RESEARCHER)
        cache_key = "test_cache_key"

        # Cache the result
        client._cache_result(cache_key, result)

        # Verify it's cached
        cached_result = client._get_cached_result(cache_key)
        assert cached_result is not None
        assert cached_result.valid is True
        assert cached_result.key_id == "test_key"
        assert cached_result.role == Role.RESEARCHER

    def test_cache_result_unsuccessful_not_cached(self):
        """Test that unsuccessful validation results are not cached."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        result = UnkeyValidationResult(valid=False, error="Invalid key")
        cache_key = "test_cache_key"

        # Try to cache the unsuccessful result
        client._cache_result(cache_key, result)

        # Verify it's not cached
        cached_result = client._get_cached_result(cache_key)
        assert cached_result is None

    def test_cache_expiration(self):
        """Test that expired cache entries are removed."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=0)

        result = UnkeyValidationResult(valid=True, key_id="test_key", role=Role.RESEARCHER)
        cache_key = "test_cache_key"

        # Cache the result with 0 TTL (immediate expiration)
        client._cache_result(cache_key, result)

        # Sleep briefly to ensure expiration
        time.sleep(0.01)

        # Try to get cached result - should be None and entry should be removed
        cached_result = client._get_cached_result(cache_key)
        assert cached_result is None
        assert cache_key not in client._validation_cache

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        result = UnkeyValidationResult(valid=True, key_id="test_key", role=Role.RESEARCHER)

        # Add multiple cache entries
        client._cache_result("key1", result)
        client._cache_result("key2", result)

        assert len(client._validation_cache) == 2

        # Clear cache
        client.clear_cache()

        assert len(client._validation_cache) == 0

    @pytest.mark.asyncio
    async def test_validate_key_uses_cache(self):
        """Test that validate_key uses cached results when available."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        # First call - should make API request and cache result
        with patch.object(client, "_make_verify_request") as mock_request:
            mock_response = AsyncMock()
            mock_response.data = AsyncMock()
            mock_response.data.valid = True
            mock_response.data.key_id = "test_key"
            mock_response.data.roles = ["researcher"]
            mock_response.data.permissions = None
            mock_response.data.meta = None
            mock_response.data.identity = None
            mock_request.return_value = mock_response

            result1 = await client.validate_key("test_key")
            assert result1.valid is True
            assert mock_request.call_count == 1

        # Second call - should use cache, not make API request
        with patch.object(client, "_make_verify_request") as mock_request2:
            result2 = await client.validate_key("test_key")
            assert result2.valid is True
            assert result2.key_id == "test_key"
            assert mock_request2.call_count == 0  # No API call made

    @pytest.mark.asyncio
    async def test_validate_key_different_roles_cached_separately(self):
        """Test that different required roles are cached separately."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        with patch.object(client, "_make_verify_request") as mock_request:
            mock_response = AsyncMock()
            mock_response.data = AsyncMock()
            mock_response.data.valid = True
            mock_response.data.key_id = "test_key"
            mock_response.data.roles = ["researcher"]
            mock_response.data.permissions = None
            mock_response.data.meta = None
            mock_response.data.identity = None
            mock_request.return_value = mock_response

            # Call with different required roles
            await client.validate_key("test_key", Role.RESEARCHER)
            await client.validate_key("test_key", Role.ADMIN)
            await client.validate_key("test_key")  # No required role

            # Should make 3 separate API calls (different cache keys)
            assert mock_request.call_count == 3

            # Verify separate cache entries
            assert len(client._validation_cache) == 3

    @pytest.mark.asyncio
    async def test_validate_key_error_not_cached(self):
        """Test that validation errors are not cached."""
        client = UnkeyClient("test_api_key", cache_ttl_seconds=300)

        with patch.object(client, "_make_verify_request") as mock_request:
            mock_request.side_effect = Exception("API Error")

            # First call - should fail
            result1 = await client.validate_key("test_key")
            assert result1.valid is False

            # Second call - should make API request again (error not cached)
            result2 = await client.validate_key("test_key")
            assert result2.valid is False

            # Should have made 2 API calls
            assert mock_request.call_count == 2

            # Should have no cache entries
            assert len(client._validation_cache) == 0
