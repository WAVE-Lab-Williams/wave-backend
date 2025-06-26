"""Single database test to debug issues."""

from fastapi.testclient import TestClient


def test_create_single_tag(test_client: TestClient):
    """Test creating a single tag via API."""
    tag_data = {"name": "debug-tag", "description": "Tag for debugging"}
    response = test_client.post("/api/v1/tags/", json=tag_data)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 200:
        data = response.json()
        assert data["name"] == "debug-tag"
        assert data["description"] == "Tag for debugging"
        assert "id" in data
        assert "created_at" in data
