"""API key validation decorator for FastAPI routes."""

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyClient, get_unkey_client
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)

# FastAPI security scheme for API keys
security = HTTPBearer()


async def validate_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    unkey_client: UnkeyClient = Depends(get_unkey_client),
) -> tuple[str, Optional[Role]]:
    """
    FastAPI dependency to validate API key and extract user role.

    Args:
        credentials: HTTP Bearer token from request
        unkey_client: UnkeyClient singleton instance

    Returns:
        Tuple of (key_id, role) for the validated key

    Raises:
        HTTPException: If key is invalid or validation fails
    """
    if not credentials or not credentials.credentials:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await unkey_client.validate_key(credentials.credentials)

    if not result.valid:
        logger.warning(f"Invalid API key: {result.error}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid API key: {result.error}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Valid API key - Key ID: {result.key_id}, Role: {result.role}")
    return result.key_id, result.role


def require_role(minimum_role: Role):
    """
    Decorator factory to require a minimum role for route access.

    Args:
        minimum_role: Minimum role required to access the route

    Returns:
        FastAPI dependency that validates role authorization
    """

    async def check_role_authorization(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        unkey_client: UnkeyClient = Depends(get_unkey_client),
    ) -> tuple[str, Role]:
        """
        FastAPI dependency to validate API key with role requirement.

        Args:
            credentials: HTTP Bearer token from request
            unkey_client: UnkeyClient singleton instance

        Returns:
            Tuple of (key_id, role) for the validated key

        Raises:
            HTTPException: If key is invalid, validation fails, or insufficient role
        """
        if not credentials or not credentials.credentials:
            logger.warning("Missing API key in request")
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate key with required role check
        result = await unkey_client.validate_key(credentials.credentials, minimum_role)

        if not result.valid:
            logger.warning(f"API key validation failed: {result.error}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid API key: {result.error}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not result.role:
            logger.warning(f"No role found for key {result.key_id}")
            raise HTTPException(status_code=403, detail="No role assigned to API key")

        # Check if user's role meets minimum requirement
        if not result.role.can_access(minimum_role):
            logger.warning(f"Insufficient permissions: {result.role} < {minimum_role}")
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {minimum_role}, Found: {result.role}",
            )

        logger.info(f"Authorized access - Key ID: {result.key_id}, Role: {result.role}")
        return result.key_id, result.role

    return check_role_authorization
