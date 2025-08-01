"""
Test module for FastAPI endpoints.
"""

from fastapi.testclient import TestClient


def test_api_root(test_client: TestClient):
    """Test the API root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "wave-backend"
