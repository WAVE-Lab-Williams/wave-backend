"""
Test module for FastAPI endpoints.
"""

from fastapi.testclient import TestClient


def test_api_root(test_client: TestClient):
    """Test the API root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the WAVE Backend API", "version": "0.1.0"}


def test_health_check(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "wave-backend"
