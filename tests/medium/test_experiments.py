"""Simple tests for experiment operations."""

import pytest
from httpx import ASGITransport, AsyncClient

from wave_backend.api.main import app


@pytest.mark.anyio
async def test_create_experiment_api():
    """Test creating an experiment via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create experiment type first
        exp_type_data = {
            "name": "simple-experiment-type",
            "description": "Test experiment type",
            "table_name": "simple_experiment_table",
        }
        exp_type_response = await client.post("/api/v1/experiment-types/", json=exp_type_data)
        exp_type_id = exp_type_response.json()["id"]

        experiment_data = {
            "experiment_type_id": exp_type_id,
            "participant_id": "simple-participant-001",
            "description": "Simple test experiment",
            "tags": ["simple-tag1", "simple-tag2"],
            "additional_data": {"test": True},
        }
        response = await client.post("/api/v1/experiments/", json=experiment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["participant_id"] == "simple-participant-001"
        assert data["description"] == "Simple test experiment"
        assert data["tags"] == ["simple-tag1", "simple-tag2"]
        assert "uuid" in data
        assert "created_at" in data


@pytest.mark.anyio
async def test_get_experiments_api():
    """Test getting experiments via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create experiment type first
        exp_type_data = {
            "name": "simple-list-experiment-type",
            "description": "Test experiment type for listing",
            "table_name": "simple_list_experiment_table",
        }
        exp_type_response = await client.post("/api/v1/experiment-types/", json=exp_type_data)
        exp_type_id = exp_type_response.json()["id"]

        # Create an experiment
        experiment_data = {
            "experiment_type_id": exp_type_id,
            "participant_id": "simple-list-participant",
            "description": "Experiment for listing",
        }
        await client.post("/api/v1/experiments/", json=experiment_data)

        response = await client.get("/api/v1/experiments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


@pytest.mark.anyio
async def test_get_experiment_columns_api():
    """Test getting experiment columns via API."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create experiment type first
        exp_type_data = {
            "name": "simple-columns-experiment-type",
            "description": "Test experiment type for columns",
            "table_name": "simple_columns_experiment_table",
        }
        exp_type_response = await client.post("/api/v1/experiment-types/", json=exp_type_data)
        exp_type_id = exp_type_response.json()["id"]

        # Create an experiment
        experiment_data = {
            "experiment_type_id": exp_type_id,
            "participant_id": "simple-columns-participant",
            "description": "Experiment for column testing",
        }
        create_response = await client.post("/api/v1/experiments/", json=experiment_data)
        experiment_uuid = create_response.json()["uuid"]

        # Get columns for the experiment
        response = await client.get(f"/api/v1/experiments/{experiment_uuid}/columns")
        assert response.status_code == 200
        data = response.json()
        assert "columns" in data
        assert data["experiment_uuid"] == experiment_uuid
        assert len(data["columns"]) > 0
