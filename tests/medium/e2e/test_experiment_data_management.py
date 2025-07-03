"""Tests for bulk data management operations."""

import pytest

from tests.medium.e2e.conftest import assert_experiment_list_response


@pytest.mark.anyio
async def test_create_multiple_data_rows(
    async_client, experiment_setup, additional_experiment_data
):
    """Test creating multiple experiment data rows."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    created_ids = []

    for data in additional_experiment_data:
        response = await async_client.post(
            f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data
        )
        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    assert len(created_ids) == len(additional_experiment_data)
    assert len(set(created_ids)) == len(created_ids)  # All IDs are unique


@pytest.mark.anyio
async def test_list_all_experiment_data(async_client, populated_experiment):
    """Test retrieving all experiment data."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    participant_id = populated_experiment["participant_id"]
    expected_count = len(populated_experiment["data_rows"])

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/")

    assert response.status_code == 200
    all_data = response.json()
    assert_experiment_list_response(all_data, expected_count, participant_id)


@pytest.mark.anyio
async def test_data_count_operations(async_client, populated_experiment):
    """Test data count endpoint."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    expected_count = len(populated_experiment["data_rows"])

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/count")

    assert response.status_code == 200
    count_data = response.json()
    assert count_data["count"] == expected_count


@pytest.mark.anyio
async def test_count_after_deletion(async_client, populated_experiment):
    """Test that count updates correctly after deletion."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    initial_count = len(populated_experiment["data_rows"])
    row_id_to_delete = populated_experiment["primary_row_id"]

    # Delete one row
    delete_response = await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id_to_delete}"
    )
    assert delete_response.status_code == 200

    # Verify count decreased
    count_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/count")
    assert count_response.status_code == 200
    final_count = count_response.json()["count"]
    assert final_count == initial_count - 1


@pytest.mark.anyio
async def test_empty_experiment_data_list(async_client, experiment_setup):
    """Test listing data for experiment with no data."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.anyio
async def test_empty_experiment_data_count(async_client, experiment_setup):
    """Test count for experiment with no data."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/count")

    assert response.status_code == 200
    count_data = response.json()
    assert count_data["count"] == 0


@pytest.mark.anyio
async def test_bulk_operations_workflow(async_client, experiment_setup, additional_experiment_data):
    """Test complete bulk operations workflow."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    # Initial state - empty
    initial_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/count"
    )
    assert initial_response.json()["count"] == 0

    # Create multiple rows
    for data in additional_experiment_data:
        response = await async_client.post(
            f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data
        )
        assert response.status_code == 201

    # Verify count increased
    count_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/count")
    assert count_response.json()["count"] == len(additional_experiment_data)

    # Verify list contains all rows
    list_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/")
    assert_experiment_list_response(
        list_response.json(), len(additional_experiment_data), participant_id
    )
