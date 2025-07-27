"""Role definitions and hierarchy for WAVE Backend authentication."""

from enum import IntEnum


class Role(IntEnum):
    """
    User roles with hierarchical integer values for permission checking.

    Higher integer values indicate higher permission levels.
    Lower roles can access resources meant for their level and below.

    IMPORTANT: These role names and hierarchy values must exactly match
    the roles configured in your Unkey application. Any changes here
    must be synchronized with Unkey role configuration.

    Hierarchy (ascending permission levels):
    - EXPERIMENTEE (1): Basic user, can participate in experiments
    - RESEARCHER (2): Can create and manage experiments
    - ADMIN (3): Full system access and user management
    - TEST (4): Highest privilege test/staging environment access
    """

    EXPERIMENTEE = 1
    RESEARCHER = 2
    ADMIN = 3
    TEST = 4

    @classmethod
    def from_string(cls, role_str: str) -> "Role":
        """Convert string role name to Role enum."""
        try:
            return cls[role_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid role: {role_str}")

    def can_access(self, required_role: "Role") -> bool:
        """Check if this role can access resources requiring another role."""
        return self.value >= required_role.value

    def __str__(self) -> str:
        """Return lowercase string representation of role."""
        return self.name.lower()
