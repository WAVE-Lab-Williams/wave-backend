"""Single database test to debug issues."""

import time

import pytest


@pytest.mark.asyncio
async def test_create_single_tag(async_client):
    """Test creating a single tag via API."""
    headers = {"Authorization": "Bearer test_token"}
    timestamp = str(int(time.time() * 1000))
    tag_data = {"name": f"debug-tag-{timestamp}", "description": "Tag for debugging"}
    response = await async_client.post("/api/v1/tags/", json=tag_data, headers=headers)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    if response.status_code == 200:
        data = response.json()
        assert data["name"] == f"debug-tag-{timestamp}"
        assert data["description"] == "Tag for debugging"
        assert "id" in data
        assert "created_at" in data
