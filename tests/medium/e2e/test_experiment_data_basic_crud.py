"""Tests for basic CRUD operations on experiment data."""

import pytest

from tests.medium.e2e.conftest import (
    assert_experiment_data_matches,
    assert_experiment_data_response,
)


@pytest.mark.asyncio
async def test_create_experiment_data(async_client, experiment_setup, sample_experiment_data):
    """Test creating experiment data."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )

    assert response.status_code == 201
    created_data = response.json()

    assert_experiment_data_response(created_data, participant_id)
    assert_experiment_data_matches(created_data, sample_experiment_data)


@pytest.mark.asyncio
async def test_get_specific_experiment_data_row(
    async_client, experiment_setup, sample_experiment_data
):
    """Test retrieving a specific experiment data row."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    headers = {"Authorization": "Bearer test_token"}
    # Create data first
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    row_id = create_response.json()["id"]

    # Get the specific row
    get_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )

    assert get_response.status_code == 200
    retrieved_data = get_response.json()

    assert retrieved_data["id"] == row_id
    assert_experiment_data_response(retrieved_data, participant_id)
    assert_experiment_data_matches(retrieved_data, sample_experiment_data)


@pytest.mark.asyncio
async def test_update_experiment_data(
    async_client, experiment_setup, sample_experiment_data, updated_experiment_data
):
    """Test updating experiment data."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    headers = {"Authorization": "Bearer test_token"}
    # Create data first
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    row_id = create_response.json()["id"]

    # Update the data
    update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}",
        json=updated_experiment_data,
        headers=headers,
    )

    assert update_response.status_code == 200
    updated_data = update_response.json()

    assert updated_data["id"] == row_id
    assert_experiment_data_matches(updated_data, updated_experiment_data)


@pytest.mark.asyncio
async def test_delete_experiment_data(async_client, experiment_setup, sample_experiment_data):
    """Test deleting experiment data."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    headers = {"Authorization": "Bearer test_token"}
    # Create data first
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    row_id = create_response.json()["id"]

    # Delete the data
    delete_response = await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Experiment data row deleted successfully"


@pytest.mark.asyncio
async def test_verify_deletion(async_client, experiment_setup, sample_experiment_data):
    """Test that deleted data cannot be retrieved."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    headers = {"Authorization": "Bearer test_token"}
    # Create data first
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    row_id = create_response.json()["id"]

    # Delete the data
    await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )

    # Verify deletion - should return 404
    get_deleted_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )

    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_crud_workflow_integration(
    async_client, experiment_setup, sample_experiment_data, updated_experiment_data
):
    """Test complete CRUD workflow in sequence."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    headers = {"Authorization": "Bearer test_token"}
    # Create
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    row_id = create_response.json()["id"]

    # Read
    read_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert read_response.status_code == 200
    assert_experiment_data_response(read_response.json(), participant_id)

    # Update
    update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}",
        json=updated_experiment_data,
        headers=headers,
    )
    assert update_response.status_code == 200
    assert_experiment_data_matches(update_response.json(), updated_experiment_data)

    # Delete
    delete_response = await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert delete_response.status_code == 200

    # Verify deletion
    verify_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert verify_response.status_code == 404
