"""Unkey API client for key validation using REST API with Pydantic models."""

import time
from functools import lru_cache
from typing import Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from wave_backend.auth.config import get_auth_config
from wave_backend.auth.roles import Role
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


class CachedValidationResult:
    """Wrapper for cached validation results with TTL."""

    def __init__(self, result: "UnkeyValidationResult", ttl_seconds: int = 300):
        self.result = result
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if cached result has expired."""
        return time.time() > self.expires_at


class UnkeyAuthorizationRequest(BaseModel):
    """Authorization requirements for Unkey validation."""

    permissions: Optional[Union[str, List[str]]] = None
    roles: Optional[Union[str, List[str]]] = None


class UnkeyVerifyRequest(BaseModel):
    """Request model for Unkey key verification."""

    api_id: str = Field(alias="apiId")
    key: str
    authorization: Optional[UnkeyAuthorizationRequest] = None


class UnkeyVerifyResponse(BaseModel):
    """Response model from Unkey key verification."""

    valid: bool
    key_id: Optional[str] = Field(default=None, alias="keyId")
    permissions: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    meta: Optional[Dict] = None
    identity: Optional[Dict] = None


class UnkeyValidationResult(BaseModel):
    """Result of Unkey API key validation with parsed role."""

    valid: bool
    key_id: Optional[str] = None
    role: Optional[Role] = None
    permissions: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    meta: Optional[Dict] = None
    error: Optional[str] = None


class UnkeyClient:
    """Client for interacting with Unkey API using REST endpoints."""

    def __init__(
        self,
        api_key: str,
        app_id: str,
        cache_ttl_seconds: int = 300,
        base_url: str = "https://api.unkey.dev",
        timeout_seconds: float = 10.0,
    ):
        """Initialize Unkey client with API credentials and configuration."""
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = base_url
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._validation_cache: Dict[str, CachedValidationResult] = {}

    def _build_request(self, key: str, required_role: Optional[Role] = None) -> UnkeyVerifyRequest:
        """Build Unkey verification request."""
        authorization = None
        if required_role:
            authorization = UnkeyAuthorizationRequest(roles=str(required_role))

        return UnkeyVerifyRequest(apiId=self.app_id, key=key, authorization=authorization)

    async def _make_verify_request(self, request_data: UnkeyVerifyRequest) -> UnkeyVerifyResponse:
        """
        Make HTTP request to Unkey API for key verification.

        Args:
            request_data: Pydantic model with request payload

        Returns:
            UnkeyVerifyResponse parsed from API response

        Raises:
            httpx.HTTPStatusError: For non-200 status codes
            httpx.TimeoutException: For request timeouts
            Exception: For other HTTP or parsing errors
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/keys.verifyKey",
                headers={"Content-Type": "application/json"},
                json=request_data.model_dump(by_alias=True, exclude_none=True),
                timeout=self.timeout_seconds,
            )

            if response.status_code != 200:
                logger.error(f"Unkey API error: {response.status_code} - {response.text}")
                raise httpx.HTTPStatusError(
                    f"Unkey API error: {response.status_code}",
                    request=response.request,
                    response=response,
                )

            return UnkeyVerifyResponse.model_validate(response.json())

    def _extract_role(self, unkey_response: UnkeyVerifyResponse) -> Optional[Role]:  # noqa: C901
        """
        Extract role from Unkey response, trying multiple sources.

        Args:
            unkey_response: Response from Unkey API

        Returns:
            Role enum if found and valid, None otherwise
        """
        # Try to find a matching role from Unkey roles array first
        if unkey_response.roles:
            for unkey_role in unkey_response.roles:
                try:
                    return Role.from_string(unkey_role)
                except ValueError:
                    continue

        # Try to extract role from meta as fallback
        if unkey_response.meta and "role" in unkey_response.meta:
            role_str = unkey_response.meta["role"]
            try:
                return Role.from_string(role_str)
            except ValueError as e:
                logger.warning(f"Invalid role from meta: {role_str} - {e}")

        # Try to extract role from identity as final fallback
        if unkey_response.identity and "role" in unkey_response.identity:
            role_str = unkey_response.identity["role"]
            try:
                return Role.from_string(role_str)
            except ValueError as e:
                logger.warning(f"Invalid role from identity: {role_str} - {e}")

        return None

    def _build_result(self, unkey_response: UnkeyVerifyResponse) -> UnkeyValidationResult:
        """
        Build validation result from Unkey response.

        Args:
            unkey_response: Response from Unkey API

        Returns:
            UnkeyValidationResult with extracted information
        """
        if not unkey_response.valid:
            return UnkeyValidationResult(
                valid=False, error="Invalid API key or insufficient permissions"
            )

        role = self._extract_role(unkey_response)

        return UnkeyValidationResult(
            valid=True,
            key_id=unkey_response.key_id,
            role=role,
            permissions=unkey_response.permissions,
            roles=unkey_response.roles,
            meta=unkey_response.meta,
        )

    def _get_cache_key(self, key: str, required_role: Optional[Role] = None) -> str:
        """Generate cache key for validation result."""
        role_str = str(required_role) if required_role else "none"
        return f"{key[:8]}...{key[-8:]}:{role_str}"

    def _get_cached_result(self, cache_key: str) -> Optional[UnkeyValidationResult]:
        """Get cached validation result if not expired."""
        if cache_key in self._validation_cache:
            cached = self._validation_cache[cache_key]
            if not cached.is_expired():
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached.result
            else:
                # Remove expired entry
                del self._validation_cache[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")
        return None

    def _cache_result(self, cache_key: str, result: UnkeyValidationResult) -> None:
        """Cache validation result if it's successful."""
        if result.valid:
            self._validation_cache[cache_key] = CachedValidationResult(
                result, self.cache_ttl_seconds
            )
            logger.debug(f"Cached result for key: {cache_key}")

    def clear_cache(self) -> None:
        """Clear all cached validation results."""
        self._validation_cache.clear()
        logger.info("Validation cache cleared")

    async def validate_key(
        self, key: str, required_role: Optional[Role] = None
    ) -> UnkeyValidationResult:
        """
        Validate an API key with Unkey and extract role information.
        Uses TTL-based caching for successful validations.

        Args:
            key: The API key to validate
            required_role: Optional role to check authorization for

        Returns:
            UnkeyValidationResult with validation status and role info
        """
        # Check cache first
        cache_key = self._get_cache_key(key, required_role)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            request_data = self._build_request(key, required_role)
            unkey_response = await self._make_verify_request(request_data)
            result = self._build_result(unkey_response)

            # Cache successful results
            self._cache_result(cache_key, result)

            return result

        except httpx.TimeoutException:
            logger.error("Timeout connecting to Unkey API")
            return UnkeyValidationResult(valid=False, error="Timeout connecting to Unkey API")
        except httpx.HTTPStatusError as e:
            return UnkeyValidationResult(valid=False, error=str(e))
        except Exception as e:
            logger.error(f"Error validating key with Unkey: {e}")
            return UnkeyValidationResult(valid=False, error=f"Validation error: {str(e)}")


@lru_cache(maxsize=1)
def get_unkey_client() -> UnkeyClient:
    """Get singleton UnkeyClient instance using centralized configuration."""
    config = get_auth_config()
    return UnkeyClient(
        api_key=config.api_key,
        app_id=config.app_id,
        cache_ttl_seconds=config.cache_ttl_seconds,
        base_url=config.base_url,
        timeout_seconds=config.timeout_seconds,
    )
