"""Basic API tests."""

from fastapi.testclient import TestClient


def test_health_check_basic(test_client: TestClient):
    """Test basic health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_hello_world_basic(test_client: TestClient):
    """Test basic hello world endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Hello World" in response.json()["message"]
