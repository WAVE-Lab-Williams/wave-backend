"""Simple tests for experiment operations."""

import time

import pytest


@pytest.mark.asyncio
async def test_create_experiment_api(async_client):
    """Test creating an experiment via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-experiment-type-{timestamp}",
        "description": "Test experiment type",
        "table_name": f"simple_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create tags first (proper workflow)
    tag_data_1 = {"name": "simple-tag1", "description": "Simple tag 1 for testing"}
    tag_data_2 = {"name": "simple-tag2", "description": "Simple tag 2 for testing"}
    await async_client.post("/api/v1/tags/", json=tag_data_1, headers=headers)
    await async_client.post("/api/v1/tags/", json=tag_data_2, headers=headers)

    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Simple test experiment",
        "tags": ["simple-tag1", "simple-tag2"],
        "additional_data": {"test": True},
    }
    response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Simple test experiment"
    assert data["tags"] == ["simple-tag1", "simple-tag2"]
    assert "uuid" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_experiments_api(async_client):
    """Test getting experiments via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-list-experiment-type-{timestamp}",
        "description": "Test experiment type for listing",
        "table_name": f"simple_list_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create an experiment
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Experiment for listing",
    }
    await async_client.post("/api/v1/experiments/", json=experiment_data, headers=headers)

    response = await async_client.get("/api/v1/experiments/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_experiment_columns_api(async_client):
    """Test getting experiment columns via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-columns-experiment-type-{timestamp}",
        "description": "Test experiment type for columns",
        "table_name": f"simple_columns_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create an experiment
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Experiment for column testing",
    }
    create_response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )
    experiment_uuid = create_response.json()["uuid"]

    # Get columns for the experiment
    response = await async_client.get(
        f"/api/v1/experiments/{experiment_uuid}/columns", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert data["experiment_uuid"] == experiment_uuid
    assert len(data["columns"]) > 0
