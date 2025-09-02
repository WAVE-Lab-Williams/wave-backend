"""Centralized database configuration module.

This module provides a single source of truth for all database configuration,
eliminating inconsistencies between different parts of the application.
"""

import os


class DatabaseConfig:
    """Centralized database configuration class."""

    def __init__(self):
        """Initialize database configuration from environment variables."""
        # Base PostgreSQL configuration
        self.host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.user: str = os.getenv("POSTGRES_USER", "wave_user")
        self.password: str = os.getenv("POSTGRES_PASSWORD", "wave_password")

        # Development database configuration
        self.dev_port: str = os.getenv("POSTGRES_PORT", "5432")
        self.dev_db: str = os.getenv("POSTGRES_DB", "wave_dev")

        # Test database configuration
        self.test_port: str = os.getenv("POSTGRES_TEST_PORT", "5433")
        self.test_db: str = os.getenv("POSTGRES_TEST_DB", "wave_test")

        # SQLAlchemy configuration
        self.echo: bool = os.getenv("SQLALCHEMY_ECHO", "false").lower() in ("true", "1", "yes")

    def get_database_url(self, test: bool = False) -> str:
        """Get the complete database URL.

        Args:
            test: If True, return test database URL, otherwise development URL

        Returns:
            Complete PostgreSQL async URL
        """
        port = self.test_port if test else self.dev_port
        db_name = self.test_db if test else self.dev_db

        # Check for explicit DATABASE_URL override first
        if test:
            explicit_url = os.getenv("DATABASE_URL_TEST")
            if explicit_url:
                return explicit_url
        else:
            explicit_url = os.getenv("DATABASE_URL")
            if explicit_url:
                # Convert sync PostgreSQL URL to async if needed
                if explicit_url.startswith("postgresql://"):
                    return explicit_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                return explicit_url

        # Build URL from components
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{port}/{db_name}"

    def get_sync_database_url(self, test: bool = False) -> str:
        """Get synchronous database URL (for migrations, etc.).

        Args:
            test: If True, return test database URL, otherwise development URL

        Returns:
            Complete PostgreSQL sync URL
        """
        async_url = self.get_database_url(test=test)
        return async_url.replace("postgresql+asyncpg://", "postgresql://")

    def get_connection_params(self, test: bool = False) -> dict:
        """Get database connection parameters as a dictionary.

        Args:
            test: If True, return test database params, otherwise development params

        Returns:
            Dictionary with connection parameters
        """
        return {
            "host": self.host,
            "port": int(self.test_port if test else self.dev_port),
            "user": self.user,
            "password": self.password,
            "database": self.test_db if test else self.dev_db,
        }


# Global configuration instance
db_config = DatabaseConfig()
