"""Standardized authentication and authorization error responses."""

from fastapi import HTTPException

from wave_backend.auth.roles import Role
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


def raise_missing_api_key_error() -> None:
    """Raise standardized error for missing API key."""
    logger.warning("Missing API key in request")
    raise HTTPException(
        status_code=401,
        detail="Authentication required: API key missing",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_invalid_api_key_error(error_detail: str) -> None:
    """Raise standardized error for invalid API key."""
    logger.warning(f"API key validation failed: {error_detail}")
    raise HTTPException(
        status_code=401,
        detail=f"Authentication failed: {error_detail}",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_missing_role_error(key_id: str) -> None:
    """Raise standardized error for missing role assignment."""
    logger.warning(f"No role found for key {key_id}")
    raise HTTPException(status_code=403, detail="Authorization failed: No role assigned to API key")


def raise_insufficient_permissions_error(user_role: Role, required_role: Role) -> None:
    """Raise standardized error for insufficient permissions."""
    logger.warning(f"Insufficient permissions: {user_role} < {required_role}")
    raise HTTPException(
        status_code=403,
        detail=(
            "Authorization failed: Insufficient permissions. "
            f"Required: {required_role}, Found: {user_role}"
        ),
    )
