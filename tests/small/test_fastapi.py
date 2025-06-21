"""
Test module for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_hello_world(test_client: TestClient):
    """Test the hello world endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World from WAVE Backend!"}


def test_health_check(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "wave-backend"


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test application lifespan context manager."""
    # This test ensures the lifespan context manager works correctly
    from wave_backend.api.main import app, lifespan

    # Test that lifespan context manager can be used
    async with lifespan(app):
        # During lifespan, the app should be ready
        pass
    # After lifespan, cleanup should be complete
