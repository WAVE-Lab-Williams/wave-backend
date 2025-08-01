"""
Middleware for handling client-server version compatibility.
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from wave_backend.utils.logging import get_logger
from wave_backend.utils.versioning import API_VERSION, log_version_info

logger = get_logger(__name__)


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle version compatibility headers.

    Processes:
    - X-WAVE-Client-Version: Version of the client library
    - User-Agent: Browser/client information

    Responds with:
    - X-WAVE-API-Version: Current API version
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add version headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            HTTP response with version headers
        """
        # Extract version information from request headers
        client_version = request.headers.get("X-WAVE-Client-Version")
        user_agent = request.headers.get("User-Agent")

        # Log version information for monitoring/debugging
        # Only check compatibility when client version is explicitly provided
        if client_version:
            log_version_info(client_version, user_agent)
        elif user_agent:
            # Log user agent without version checking if no client version header
            logger.debug(f"No client version header, User agent: {user_agent}")

        # Process the request
        response = await call_next(request)

        # Add API version header to response
        response.headers["X-WAVE-API-Version"] = API_VERSION

        # Add CORS headers for version headers if needed
        if "Access-Control-Expose-Headers" in response.headers:
            exposed_headers = response.headers["Access-Control-Expose-Headers"]
            if "X-WAVE-API-Version" not in exposed_headers:
                response.headers["Access-Control-Expose-Headers"] = (
                    f"{exposed_headers}, X-WAVE-API-Version"
                )
        else:
            response.headers["Access-Control-Expose-Headers"] = "X-WAVE-API-Version"

        return response
