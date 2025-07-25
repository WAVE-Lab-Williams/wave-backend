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

    if not result.role:
        logger.warning(f"No role found for key {result.key_id}")
        raise HTTPException(status_code=403, detail="No role assigned to API key")

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
