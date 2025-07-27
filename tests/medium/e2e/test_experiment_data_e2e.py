"""Simplified E2E tests for experiment data operations."""

import time

import pytest

from tests.medium.e2e.conftest import (
    assert_experiment_data_response,
    assert_tag_lookup_contains_experiment,
)


@pytest.mark.asyncio
async def test_complete_experiment_workflow_e2e(
    async_client, experiment_setup, sample_experiment_data
):
    """Simplified end-to-end test covering the complete experiment workflow.

    This test verifies the happy path integration of all major components:
    - Experiment creation with tags
    - Basic data operations (create, read, update, delete)
    - Data management (count, list)
    - Tag-based discovery

    For comprehensive testing of individual features, see the modular test files:
    - test_experiment_data_basic_crud.py
    - test_experiment_data_management.py
    - test_experiment_data_queries.py
    - test_experiment_data_schema.py
    - test_experiment_discovery.py
    """
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    # 1. Create experiment data
    headers = {"Authorization": "Bearer test_token"}
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    assert_experiment_data_response(created_data, participant_id)
    row_id = created_data["id"]

    # 2. Read the data back
    read_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert read_response.status_code == 200
    assert read_response.json()["id"] == row_id

    # 3. Update the data
    update_data = {
        "participant_id": participant_id,
        "data": {"test_value": "updated data", "number": 100},
    }
    update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}",
        json=update_data,
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["test_value"] == "updated data"

    # 4. Verify data management operations work
    count_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/count", headers=headers
    )
    assert count_response.status_code == 200
    assert count_response.json()["count"] == 1

    list_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/", headers=headers
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    # 5. Verify experiment discovery works
    tag_response = await async_client.get("/api/v1/experiments/?tags=crud-test", headers=headers)
    assert tag_response.status_code == 200
    assert_tag_lookup_contains_experiment(tag_response.json(), experiment_uuid)

    # 6. Delete the data
    delete_response = await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert delete_response.status_code == 200

    # 7. Verify deletion
    verify_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/row/{row_id}", headers=headers
    )
    assert verify_response.status_code == 404


@pytest.mark.asyncio
async def test_experiment_data_error_cases(async_client):
    """Test error cases for experiment data operations."""
    # Test with non-existent experiment ID
    fake_uuid = "00000000-0000-4000-8000-000000000000"

    # Test creating data for non-existent experiment
    create_data = {
        "participant_id": "test-participant",
        "data": {"score": 95},
    }
    headers = {"Authorization": "Bearer test_token"}
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=create_data, headers=headers
    )
    assert create_response.status_code == 404
    assert "Experiment not found" in create_response.json()["detail"]

    # Test getting data for non-existent experiment
    get_response = await async_client.get(
        f"/api/v1/experiment-data/{fake_uuid}/data/", headers=headers
    )
    assert get_response.status_code == 404
    assert "Experiment not found" in get_response.json()["detail"]

    # Test invalid UUID format
    invalid_uuid = "not-a-uuid"
    invalid_response = await async_client.get(
        f"/api/v1/experiment-data/{invalid_uuid}/data/", headers=headers
    )
    assert invalid_response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_experiment_data_validation(async_client):
    """Test validation of experiment data requests."""
    # Use the error case test's fake UUID to avoid creating experiment types
    fake_uuid = "00000000-0000-4000-8000-000000000000"

    # Test missing participant_id
    headers = {"Authorization": "Bearer test_token"}
    invalid_data = {"data": {"score": 95}}
    response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=invalid_data, headers=headers
    )
    assert response.status_code == 422

    # Test missing data
    invalid_data = {"participant_id": "test-participant"}
    response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=invalid_data, headers=headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_experiment_tag_validation(async_client):
    """Test tag validation for experiment creation."""
    # Setup: Create experiment type
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"test-tag-validation-{timestamp}",
        "description": "Test experiment type for tag validation",
        "table_name": f"test_tag_validation_{timestamp}",
        "schema_definition": {"test_field": "STRING"},
    }
    headers = {"Authorization": "Bearer test_token"}
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    assert exp_type_response.status_code == 200
    exp_type_id = exp_type_response.json()["id"]

    # Test: Create experiment with non-existent tags (should fail with proper validation)
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Test experiment with invalid tags",
        "tags": ["nonexistent-tag", "another-invalid-tag"],
    }
    experiment_response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )
    assert experiment_response.status_code == 400
    assert "does not exist" in experiment_response.json()["detail"]

    # Test: Create valid tag and then create experiment
    tag_data = {"name": "valid-tag", "description": "A valid tag for testing"}
    tag_response = await async_client.post("/api/v1/tags/", json=tag_data, headers=headers)
    assert tag_response.status_code == 200

    valid_experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Test experiment with valid tags",
        "tags": ["valid-tag"],
    }
    valid_experiment_response = await async_client.post(
        "/api/v1/experiments/", json=valid_experiment_data, headers=headers
    )
    assert valid_experiment_response.status_code == 200
