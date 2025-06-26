"""Simple tests for tag operations."""

import pytest
from httpx import ASGITransport, AsyncClient

from wave_backend.api.main import app


@pytest.mark.anyio
async def test_create_tag_api():
    """Test creating a tag via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tag_data = {"name": "simple-api-tag", "description": "Tag created via API"}
        response = await client.post("/api/v1/tags/", json=tag_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "simple-api-tag"
        assert data["description"] == "Tag created via API"
        assert "id" in data
        assert "created_at" in data


@pytest.mark.anyio
async def test_get_tags_api():
    """Test getting tags via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a tag first
        tag_data = {"name": "simple-list-tag", "description": "Tag for listing"}
        await client.post("/api/v1/tags/", json=tag_data)

        response = await client.get("/api/v1/tags/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


@pytest.mark.anyio
async def test_create_duplicate_tag_api():
    """Test creating a duplicate tag via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tag_data = {"name": "simple-duplicate-tag", "description": "First tag"}
        await client.post("/api/v1/tags/", json=tag_data)

        # Try to create duplicate
        response = await client.post("/api/v1/tags/", json=tag_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
