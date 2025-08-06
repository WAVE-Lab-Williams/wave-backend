"""API key validation decorator for FastAPI routes.

Example usage:
    from wave_backend.auth.decorator import auth
    from wave_backend.auth.roles import Role

    @router.post("/experiments")
    @auth.role(Role.RESEARCHER)
    async def create_experiment(
        experiment: ExperimentCreate,
        db: AsyncSession = Depends(get_db),
        auth: tuple[str, Role]  # Injected by decorator
    ):
        key_id, role = auth
        # ...your code...

    @router.get("/public-data")
    @auth.any
    async def get_public_data(
        auth: tuple[str, Optional[Role]]  # Injected by decorator
    ):
        key_id, role = auth
        # ...your code...
"""

import inspect
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wave_backend.auth.errors import (
    raise_insufficient_permissions_error,
    raise_invalid_api_key_error,
    raise_missing_api_key_error,
    raise_missing_role_error,
)
from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyClient, get_unkey_client
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)

# FastAPI security scheme for API keys
security = HTTPBearer()


async def _validate_credentials_and_key(
    credentials: HTTPAuthorizationCredentials,
    unkey_client: UnkeyClient,
    required_role: Optional[Role] = None,
) -> tuple[str, Role]:
    """
    Common validation logic for API key credentials.

    Args:
        credentials: HTTP Bearer token from request
        unkey_client: UnkeyClient singleton instance
        required_role: Optional role requirement for validation

    Returns:
        Tuple of (key_id, role) for the validated key

    Raises:
        HTTPException: If key is invalid, validation fails, or missing role
    """
    if not credentials or not credentials.credentials:
        raise_missing_api_key_error()

    result = await unkey_client.validate_key(credentials.credentials, required_role)

    if not result.valid:
        raise_invalid_api_key_error(result.error or "Unknown validation error")

    if not result.role:
        raise_missing_role_error(result.key_id or "unknown")

    return result.key_id, result.role


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
    key_id, role = await _validate_credentials_and_key(credentials, unkey_client)
    logger.info(f"Valid API key - Key ID: {key_id}, Role: {role}")
    return key_id, role


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
        key_id, role = await _validate_credentials_and_key(credentials, unkey_client, minimum_role)

        # Check if user's role meets minimum requirement
        if not role.can_access(minimum_role):
            raise_insufficient_permissions_error(role, minimum_role)

        logger.debug(f"Authorized access - Key ID: {key_id}, Role: {role}")
        return key_id, role

    return check_role_authorization


class Auth:
    """Auth decorator class for clean route decoration."""

    @staticmethod
    def any(func: Callable) -> Callable:
        """Decorator requiring any valid API key."""
        sig = inspect.signature(func)

        # Check if function already has auth parameter
        if "auth" in sig.parameters:
            # Replace the existing auth parameter with dependency injection
            new_params = []
            for param in sig.parameters.values():
                if param.name == "auth":
                    auth_param = inspect.Parameter(
                        "auth",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default=Depends(validate_api_key),
                        annotation="tuple[str, Optional[Role]]",
                    )
                    new_params.append(auth_param)
                else:
                    new_params.append(param)
        else:
            # Add auth parameter if it doesn't exist
            new_params = list(sig.parameters.values())
            auth_param = inspect.Parameter(
                "auth",
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(validate_api_key),
                annotation="tuple[str, Optional[Role]]",
            )
            new_params.append(auth_param)

        # Create new signature with parameters as a list
        new_sig = sig.replace(parameters=new_params)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper.__signature__ = new_sig
        return wrapper

    @staticmethod
    def role(minimum_role: Role):
        """Decorator factory requiring specific role."""

        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)

            # Check if function already has auth parameter
            if "auth" in sig.parameters:
                # Replace the existing auth parameter with dependency injection
                new_params = []
                for param in sig.parameters.values():
                    if param.name == "auth":
                        auth_param = inspect.Parameter(
                            "auth",
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            default=Depends(require_role(minimum_role)),
                            annotation="tuple[str, Role]",
                        )
                        new_params.append(auth_param)
                    else:
                        new_params.append(param)
            else:
                # Add auth parameter if it doesn't exist
                new_params = list(sig.parameters.values())
                auth_param = inspect.Parameter(
                    "auth",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=Depends(require_role(minimum_role)),
                    annotation="tuple[str, Role]",
                )
                new_params.append(auth_param)

            # Create new signature with parameters as a list
            new_sig = sig.replace(parameters=new_params)

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper.__signature__ = new_sig
            return wrapper

        return decorator


# Create lowercase instance for convenient usage
auth = Auth()
