"""Simple tests for tag operations."""

from fastapi.testclient import TestClient


class TestTagAPI:
    """Test tag API endpoints."""

    def test_create_tag_api(self, test_client: TestClient):
        """Test creating a tag via API."""
        tag_data = {"name": "simple-api-tag", "description": "Tag created via API"}
        response = test_client.post("/api/v1/tags/", json=tag_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "simple-api-tag"
        assert data["description"] == "Tag created via API"
        assert "id" in data
        assert "created_at" in data

    def test_get_tags_api(self, test_client: TestClient):
        """Test getting tags via API."""
        # Create a tag first
        tag_data = {"name": "simple-list-tag", "description": "Tag for listing"}
        test_client.post("/api/v1/tags/", json=tag_data)

        response = test_client.get("/api/v1/tags/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_duplicate_tag_api(self, test_client: TestClient):
        """Test creating a duplicate tag via API."""
        tag_data = {"name": "simple-duplicate-tag", "description": "First tag"}
        test_client.post("/api/v1/tags/", json=tag_data)

        # Try to create duplicate
        response = test_client.post("/api/v1/tags/", json=tag_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
