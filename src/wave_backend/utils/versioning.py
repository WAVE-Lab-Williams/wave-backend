"""
Versioning utilities for client-server compatibility.

This module provides lightweight version compatibility checking between WAVE client
libraries (Python & JavaScript) and the backend API. It uses HTTP headers to
communicate version information and provides non-blocking compatibility warnings.

## How Version Compatibility Works

1. **Client Headers**: Clients send X-WAVE-Client-Version header with requests
2. **Server Response**: Server adds X-WAVE-API-Version header to all responses
3. **Compatibility Check**: Server logs warnings for incompatible combinations
4. **Non-blocking**: Incompatible versions get warnings, not errors

## Semantic Versioning Compatibility Rules

This system uses standard semantic versioning (semver) compatibility rules:

- **Same major version = Compatible**: 1.0.0 ↔ 1.5.0 ✅
- **Different major version = Incompatible**: 1.0.0 ↔ 2.0.0 ❌
- **Backward compatibility**: Newer minor/patch versions work with older ones
- **Forward compatibility**: Older clients work with newer API minor/patch versions

### Examples:
- Client 1.0.0 + API 1.0.1 = ✅ Compatible (patch update)
- Client 1.2.0 + API 1.5.0 = ✅ Compatible (minor updates, same major)
- Client 1.0.0 + API 2.0.0 = ❌ Incompatible (major version change)
- Client 2.1.0 + API 1.9.0 = ❌ Incompatible (different majors)

### Warning System
- `get_compatibility_warning()`: Returns warning text for incompatible versions
- `log_version_info()`: Logs compatibility status for monitoring
- Warnings are logged but don't block requests (graceful degradation)

## Version Update Strategy
1. **Patch updates** (1.0.0 → 1.0.1): Bug fixes, always compatible
2. **Minor updates** (1.0.0 → 1.1.0): New features, backward compatible
3. **Major updates** (1.0.0 → 2.0.0): Breaking changes, update both client and API
"""

import re
from typing import Optional

from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Current API version - update this when making changes
API_VERSION = "1.0.0"


def parse_version(version: str) -> tuple[int, int, int]:
    """
    Parse semantic version string into tuple.

    Args:
        version: Version string like "1.2.3"

    Returns:
        Tuple of (major, minor, patch)

    Raises:
        ValueError: If version format is invalid
    """
    if not version:
        raise ValueError("Version cannot be empty")

    # Remove 'v' prefix if present
    clean_version = version.lstrip("v")

    # Match semantic version pattern
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$"
    match = re.match(pattern, clean_version)

    if not match:
        raise ValueError(f"Invalid semantic version format: {version}")

    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def is_compatible_version(client_version: str, api_version: str) -> bool:
    """
    Check if client and API versions are compatible using semantic versioning.

    Compatibility Rules:
    - Same major version = compatible (1.x.x works with 1.y.z)
    - Different major version = incompatible (1.x.x vs 2.y.z)

    Args:
        client_version: Client version string
        api_version: API version string

    Returns:
        True if versions are compatible, False otherwise

    Examples:
        >>> is_compatible_version("1.0.0", "1.5.0")
        True
        >>> is_compatible_version("1.0.0", "2.0.0")
        False
    """
    try:
        # Parse both versions
        client_major, client_minor, client_patch = parse_version(client_version)
        api_major, api_minor, api_patch = parse_version(api_version)

        # Same major version = compatible (following semantic versioning)
        return client_major == api_major

    except ValueError as e:
        logger.warning(f"Version parsing error: {e}")
        return False


def get_compatibility_warning(client_version: str, api_version: str) -> Optional[str]:
    """
    Generate compatibility warning message if versions are incompatible.

    This function creates user-friendly warning messages when client and API
    versions are not compatible. It provides specific guidance based on the
    type of incompatibility detected.

    Warning Types:
    1. Major version mismatch: Suggests client upgrade (breaking changes)
    2. Unknown combination: Minor incompatibility (untested combination)
    3. Invalid format: Malformed version strings

    Args:
        client_version: Client version string (from X-WAVE-Client-Version header)
        api_version: API version string (current server version)

    Returns:
        Warning message string if incompatible, None if compatible

    Examples:
        >>> get_compatibility_warning("1.0.0", "1.0.1")
        None  # Compatible versions

        >>> get_compatibility_warning("1.0.0", "2.0.0")
        "Major version mismatch: Client v1.0.0 may not be compatible with API v2.0.0..."

        >>> get_compatibility_warning("1.5.0", "1.0.0")
        "Version compatibility unknown: Client v1.5.0 with API v1.0.0..."
    """
    if is_compatible_version(client_version, api_version):
        return None

    try:
        client_major, _, _ = parse_version(client_version)
        api_major, _, _ = parse_version(api_version)

        if client_major != api_major:
            return (
                f"Major version mismatch: Client v{client_version} may not be compatible "
                f"with API v{api_version}. Consider upgrading your client library."
            )
        else:
            return (
                f"Version compatibility unknown: Client v{client_version} with API v{api_version}. "
                f"This combination has not been tested."
            )
    except ValueError:
        return (
            f"Invalid version format detected: Client v{client_version}, API v{api_version}. "
            f"Please check your client library version."
        )


def log_version_info(client_version: str, user_agent: Optional[str] = None):
    """
    Log version information for debugging and monitoring.

    This function is called by the versioning middleware to log compatibility
    status when a client version header is present. It helps with debugging
    client issues and monitoring version adoption across your user base.

    Note: This function should only be called when client_version is provided.
    If no client version header is present, no compatibility checking occurs.

    Logging Behavior:
    1. Compatible versions: INFO level log with version numbers
    2. Incompatible versions: WARNING level log with compatibility message
    3. User agent: DEBUG level log for additional client identification

    Args:
        client_version: Client version from X-WAVE-Client-Version header (required)
        user_agent: User agent string from User-Agent header (optional)

    Examples of log output:
        INFO: "Compatible versions: Client v1.0.0, API v1.0.1"
        WARNING: "Version compatibility: Major version mismatch: Client v1.0.0..."
        DEBUG: "User agent: wave-python-client/1.0.0"
    """
    # Check compatibility and log appropriate message
    warning = get_compatibility_warning(client_version, API_VERSION)
    if warning:
        logger.warning(f"Version compatibility: {warning}")
    else:
        logger.info(f"Compatible versions: Client v{client_version}, API v{API_VERSION}")

    # Log user agent for additional context
    if user_agent:
        logger.debug(f"User agent: {user_agent}")
