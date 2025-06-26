"""Single database test to debug issues."""

import pytest
from httpx import ASGITransport, AsyncClient

from wave_backend.api.main import app


@pytest.mark.anyio
async def test_create_single_tag():
    """Test creating a single tag via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tag_data = {"name": "debug-tag", "description": "Tag for debugging"}
        response = await client.post("/api/v1/tags/", json=tag_data)

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "debug-tag"
            assert data["description"] == "Tag for debugging"
            assert "id" in data
            assert "created_at" in data
