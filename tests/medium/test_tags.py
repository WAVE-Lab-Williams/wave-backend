"""Simple tests for tag operations."""

import time

import pytest


@pytest.mark.asyncio
async def test_create_tag_api(async_client):
    """Test creating a tag via API."""
    timestamp = str(int(time.time() * 1000))
    tag_data = {"name": f"simple-api-tag-{timestamp}", "description": "Tag created via API"}
    response = await async_client.post("/api/v1/tags/", json=tag_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == f"simple-api-tag-{timestamp}"
    assert data["description"] == "Tag created via API"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_tags_api(async_client):
    """Test getting tags via API."""
    # Create a tag first
    timestamp = str(int(time.time() * 1000))
    tag_data = {"name": f"simple-list-tag-{timestamp}", "description": "Tag for listing"}
    await async_client.post("/api/v1/tags/", json=tag_data)

    response = await async_client.get("/api/v1/tags/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_duplicate_tag_api(async_client):
    """Test creating a duplicate tag via API."""
    timestamp = str(int(time.time() * 1000))
    tag_data = {"name": f"simple-duplicate-tag-{timestamp}", "description": "First tag"}
    await async_client.post("/api/v1/tags/", json=tag_data)

    # Try to create duplicate
    response = await async_client.post("/api/v1/tags/", json=tag_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
