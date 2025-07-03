"""Medium-sized CRUD tests for experiment data operations."""

import time

import pytest


@pytest.mark.anyio
async def test_experiment_data_full_crud_workflow(async_client):
    """Test complete CRUD workflow for experiment data."""
    # Setup: Create simple experiment type without custom schema to avoid DB conflicts
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"test-experiment-type-{timestamp}",
        "description": "Test experiment type for CRUD testing",
        "table_name": f"test_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post("/api/v1/experiment-types/", json=exp_type_data)
    assert exp_type_response.status_code == 200
    exp_type_id = exp_type_response.json()["id"]

    # Setup: Create experiment
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "participant_id": f"test-participant-{timestamp}",
        "description": "Test experiment for data CRUD",
        "tags": ["crud-test", "data-test"],
    }
    experiment_response = await async_client.post("/api/v1/experiments/", json=experiment_data)
    assert experiment_response.status_code == 200
    experiment_uuid = experiment_response.json()["uuid"]

    # Test 1: Create experiment data with simple data (no custom schema)
    create_data = {
        "participant_id": f"test-participant-{timestamp}",
        "data": {
            "test_value": "some test data",
            "number": 42,
        },
    }
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/", json=create_data
    )
    assert create_response.status_code == 200
    created_data = create_response.json()
    assert created_data["participant_id"] == f"test-participant-{timestamp}"
    assert created_data["test_value"] == "some test data"
    assert created_data["number"] == 42
    assert "id" in created_data
    assert "created_at" in created_data
    row_id = created_data["id"]

    # Test 2: Get specific experiment data row
    get_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/{row_id}"
    )
    assert get_response.status_code == 200
    retrieved_data = get_response.json()
    assert retrieved_data["id"] == row_id
    assert retrieved_data["participant_id"] == f"test-participant-{timestamp}"
    assert retrieved_data["test_value"] == "some test data"
    assert retrieved_data["number"] == 42

    # Test 3: Update experiment data
    update_data = {
        "participant_id": f"test-participant-{timestamp}",
        "data": {
            "test_value": "updated test data",
            "number": 99,
        },
    }
    update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_uuid}/data/{row_id}", json=update_data
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["id"] == row_id
    assert updated_data["test_value"] == "updated test data"
    assert updated_data["number"] == 99

    # Test 4: Create additional data rows for list testing
    additional_data = [
        {
            "participant_id": f"test-participant-{timestamp}",
            "data": {"value": "data1", "count": 10},
        },
        {
            "participant_id": f"test-participant-{timestamp}",
            "data": {"value": "data2", "count": 20},
        },
    ]
    additional_ids = []
    for data in additional_data:
        response = await async_client.post(
            f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data
        )
        assert response.status_code == 200
        additional_ids.append(response.json()["id"])

    # Test 5: Get all experiment data
    list_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/")
    assert list_response.status_code == 200
    all_data = list_response.json()
    assert len(all_data) == 3
    assert all(row["participant_id"] == f"test-participant-{timestamp}" for row in all_data)

    # Test 6: Get experiment data with pagination
    paginated_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?limit=2&offset=1"
    )
    assert paginated_response.status_code == 200
    paginated_data = paginated_response.json()
    assert len(paginated_data) == 2

    # Test 7: Get experiment data with participant filter
    filtered_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}"
        f"/data/?participant_id=test-participant-{timestamp}"
    )
    assert filtered_response.status_code == 200
    filtered_data = filtered_response.json()
    assert len(filtered_data) == 3

    # Test 8: Get data count
    count_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/count")
    assert count_response.status_code == 200
    count_data = count_response.json()
    assert count_data["count"] == 3

    # Test 9: Get column information
    columns_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/columns"
    )
    assert columns_response.status_code == 200
    columns_data = columns_response.json()
    column_names = [col["column_name"] for col in columns_data]
    assert "id" in column_names
    assert "participant_id" in column_names
    assert "created_at" in column_names

    # Test 10: Query experiment data with custom filters
    query_data = {
        "participant_id": f"test-participant-{timestamp}",
        "filters": {"number": 99},
        "limit": 10,
        "offset": 0,
    }
    query_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/query", json=query_data
    )
    assert query_response.status_code == 200
    query_results = query_response.json()
    assert len(query_results) == 1
    assert query_results[0]["number"] == 99

    # Test 11: Delete experiment data
    delete_response = await async_client.delete(
        f"/api/v1/experiment-data/{experiment_uuid}/data/{row_id}"
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Experiment data row deleted successfully"

    # Test 12: Verify deletion
    get_deleted_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/{row_id}"
    )
    assert get_deleted_response.status_code == 404

    # Test 13: Verify count after deletion
    final_count_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/count"
    )
    assert final_count_response.status_code == 200
    final_count = final_count_response.json()
    assert final_count["count"] == 2


@pytest.mark.anyio
async def test_experiment_data_error_cases(async_client):
    """Test error cases for experiment data operations."""
    # Test with non-existent experiment ID
    fake_uuid = "00000000-0000-4000-8000-000000000000"

    # Test creating data for non-existent experiment
    create_data = {
        "participant_id": "test-participant",
        "data": {"score": 95},
    }
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=create_data
    )
    assert create_response.status_code == 404
    assert "Experiment not found" in create_response.json()["detail"]

    # Test getting data for non-existent experiment
    get_response = await async_client.get(f"/api/v1/experiment-data/{fake_uuid}/data/")
    assert get_response.status_code == 404
    assert "Experiment not found" in get_response.json()["detail"]

    # Test invalid UUID format
    invalid_uuid = "not-a-uuid"
    invalid_response = await async_client.get(f"/api/v1/experiment-data/{invalid_uuid}/data/")
    assert invalid_response.status_code == 422  # Validation error


@pytest.mark.anyio
async def test_experiment_data_validation(async_client):
    """Test validation of experiment data requests."""
    # Use the error case test's fake UUID to avoid creating experiment types
    fake_uuid = "00000000-0000-4000-8000-000000000000"

    # Test missing participant_id
    invalid_data = {"data": {"score": 95}}
    response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=invalid_data
    )
    assert response.status_code == 422

    # Test missing data
    invalid_data = {"participant_id": "test-participant"}
    response = await async_client.post(
        f"/api/v1/experiment-data/{fake_uuid}/data/", json=invalid_data
    )
    assert response.status_code == 422
