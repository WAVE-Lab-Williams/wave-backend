"""Tests for experiment data isolation between different experiments."""

import pytest


@pytest.mark.asyncio
async def test_data_isolation_between_experiments_same_type(
    async_client, created_experiment_type, created_tags, timestamp
):
    """Test that data from different experiments using the same type is properly isolated."""
    experiment_type_id = created_experiment_type["id"]

    # Create two different experiments using the same experiment type
    experiment_a_data = {
        "experiment_type_id": experiment_type_id,
        "description": f"Experiment A - {timestamp}",
        "tags": ["crud-test"],
        "additional_data": {"session": "morning", "group": "A"},
    }

    experiment_b_data = {
        "experiment_type_id": experiment_type_id,
        "description": f"Experiment B - {timestamp}",
        "tags": ["data-test"],
        "additional_data": {"session": "afternoon", "group": "B"},
    }

    # Create experiment A
    exp_a_response = await async_client.post("/api/v1/experiments/", json=experiment_a_data)
    assert exp_a_response.status_code == 200
    experiment_a = exp_a_response.json()
    experiment_a_uuid = experiment_a["uuid"]

    # Create experiment B
    exp_b_response = await async_client.post("/api/v1/experiments/", json=experiment_b_data)
    assert exp_b_response.status_code == 200
    experiment_b = exp_b_response.json()
    experiment_b_uuid = experiment_b["uuid"]

    # Verify we have different experiments
    assert experiment_a_uuid != experiment_b_uuid

    # Create data for experiment A
    exp_a_data_1 = {
        "participant_id": "PARTICIPANT_A_001",
        "data": {
            "test_value": "experiment_a_data_1",
            "number": 100,
            "value": "group_a_value_1",
            "count": 10,
        },
    }

    exp_a_data_2 = {
        "participant_id": "PARTICIPANT_A_002",
        "data": {
            "test_value": "experiment_a_data_2",
            "number": 200,
            "value": "group_a_value_2",
            "count": 20,
        },
    }

    # Create data for experiment B
    exp_b_data_1 = {
        "participant_id": "PARTICIPANT_B_001",
        "data": {
            "test_value": "experiment_b_data_1",
            "number": 300,
            "value": "group_b_value_1",
            "count": 30,
        },
    }

    exp_b_data_2 = {
        "participant_id": "PARTICIPANT_B_002",
        "data": {
            "test_value": "experiment_b_data_2",
            "number": 400,
            "value": "group_b_value_2",
            "count": 40,
        },
    }

    # Add data to experiment A
    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/", json=exp_a_data_1
    )
    assert response.status_code == 201
    exp_a_row_1 = response.json()

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/", json=exp_a_data_2
    )
    assert response.status_code == 201
    exp_a_row_2 = response.json()

    # Add data to experiment B
    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/", json=exp_b_data_1
    )
    assert response.status_code == 201
    exp_b_row_1 = response.json()

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/", json=exp_b_data_2
    )
    assert response.status_code == 201
    exp_b_row_2 = response.json()

    # Verify all data was created with correct experiment_uuid
    assert exp_a_row_1["experiment_uuid"] == experiment_a_uuid
    assert exp_a_row_2["experiment_uuid"] == experiment_a_uuid
    assert exp_b_row_1["experiment_uuid"] == experiment_b_uuid
    assert exp_b_row_2["experiment_uuid"] == experiment_b_uuid

    # Test: Query experiment A data - should only return experiment A data
    exp_a_data_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/"
    )
    assert exp_a_data_response.status_code == 200
    exp_a_retrieved_data = exp_a_data_response.json()

    # Should have exactly 2 rows for experiment A
    assert len(exp_a_retrieved_data) == 2

    # Verify all returned data belongs to experiment A
    for row in exp_a_retrieved_data:
        assert row["experiment_uuid"] == experiment_a_uuid
        assert row["participant_id"] in ["PARTICIPANT_A_001", "PARTICIPANT_A_002"]
        assert row["test_value"] in ["experiment_a_data_1", "experiment_a_data_2"]
        assert row["number"] in [100, 200]

    # Test: Query experiment B data - should only return experiment B data
    exp_b_data_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/"
    )
    assert exp_b_data_response.status_code == 200
    exp_b_retrieved_data = exp_b_data_response.json()

    # Should have exactly 2 rows for experiment B
    assert len(exp_b_retrieved_data) == 2

    # Verify all returned data belongs to experiment B
    for row in exp_b_retrieved_data:
        assert row["experiment_uuid"] == experiment_b_uuid
        assert row["participant_id"] in ["PARTICIPANT_B_001", "PARTICIPANT_B_002"]
        assert row["test_value"] in ["experiment_b_data_1", "experiment_b_data_2"]
        assert row["number"] in [300, 400]

    # Critical test: Verify no cross-contamination
    exp_a_participant_ids = {row["participant_id"] for row in exp_a_retrieved_data}
    exp_b_participant_ids = {row["participant_id"] for row in exp_b_retrieved_data}

    # No participant IDs should overlap
    assert exp_a_participant_ids.isdisjoint(exp_b_participant_ids)

    # No experiment A data should appear in experiment B results
    exp_a_test_values = {row["test_value"] for row in exp_a_retrieved_data}
    exp_b_test_values = {row["test_value"] for row in exp_b_retrieved_data}
    assert exp_a_test_values.isdisjoint(exp_b_test_values)


@pytest.mark.asyncio
async def test_participant_filtering_isolated_by_experiment(
    async_client, created_experiment_type, created_tags, timestamp
):
    """Test that participant filtering is properly isolated between experiments."""
    experiment_type_id = created_experiment_type["id"]

    # Create two experiments with the same experiment type
    exp_a_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Participant Filter Test A - {timestamp}",
            "tags": ["crud-test"],
        },
    )
    assert exp_a_response.status_code == 200
    experiment_a_uuid = exp_a_response.json()["uuid"]

    exp_b_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Participant Filter Test B - {timestamp}",
            "tags": ["data-test"],
        },
    )
    assert exp_b_response.status_code == 200
    experiment_b_uuid = exp_b_response.json()["uuid"]

    # Use the same participant ID in both experiments (this should be allowed)
    same_participant_id = "SHARED_PARTICIPANT_001"

    # Add data for same participant in experiment A
    exp_a_data = {
        "participant_id": same_participant_id,
        "data": {
            "test_value": "from_experiment_a",
            "number": 111,
            "value": "experiment_a_value",
            "count": 1,
        },
    }

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/", json=exp_a_data
    )
    assert response.status_code == 201

    # Add data for same participant in experiment B
    exp_b_data = {
        "participant_id": same_participant_id,
        "data": {
            "test_value": "from_experiment_b",
            "number": 222,
            "value": "experiment_b_value",
            "count": 2,
        },
    }

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/", json=exp_b_data
    )
    assert response.status_code == 201

    # Query experiment A with participant filter
    exp_a_filtered_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/?participant_id={same_participant_id}"
    )
    assert exp_a_filtered_response.status_code == 200
    exp_a_filtered_data = exp_a_filtered_response.json()

    # Should return only experiment A data for this participant
    assert len(exp_a_filtered_data) == 1
    assert exp_a_filtered_data[0]["experiment_uuid"] == experiment_a_uuid
    assert exp_a_filtered_data[0]["participant_id"] == same_participant_id
    assert exp_a_filtered_data[0]["test_value"] == "from_experiment_a"
    assert exp_a_filtered_data[0]["number"] == 111

    # Query experiment B with participant filter
    exp_b_filtered_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/?participant_id={same_participant_id}"
    )
    assert exp_b_filtered_response.status_code == 200
    exp_b_filtered_data = exp_b_filtered_response.json()

    # Should return only experiment B data for this participant
    assert len(exp_b_filtered_data) == 1
    assert exp_b_filtered_data[0]["experiment_uuid"] == experiment_b_uuid
    assert exp_b_filtered_data[0]["participant_id"] == same_participant_id
    assert exp_b_filtered_data[0]["test_value"] == "from_experiment_b"
    assert exp_b_filtered_data[0]["number"] == 222


@pytest.mark.asyncio
async def test_advanced_query_isolation_between_experiments(
    async_client, created_experiment_type, created_tags, timestamp
):
    """Test that advanced query filters are properly isolated between experiments."""
    experiment_type_id = created_experiment_type["id"]

    # Create two experiments
    exp_a_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Advanced Query Test A - {timestamp}",
            "tags": ["crud-test"],
        },
    )
    assert exp_a_response.status_code == 200
    experiment_a_uuid = exp_a_response.json()["uuid"]

    exp_b_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Advanced Query Test B - {timestamp}",
            "tags": ["crud-test"],
        },
    )
    assert exp_b_response.status_code == 200
    experiment_b_uuid = exp_b_response.json()["uuid"]

    # Add data with same filter values to both experiments
    shared_value = "shared_test_value"
    shared_count = 999

    # Experiment A data
    await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/",
        json={
            "participant_id": "QUERY_PARTICIPANT_A",
            "data": {
                "test_value": shared_value,
                "number": 100,
                "value": "from_exp_a",
                "count": shared_count,
            },
        },
    )

    # Experiment B data
    await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/",
        json={
            "participant_id": "QUERY_PARTICIPANT_B",
            "data": {
                "test_value": shared_value,
                "number": 200,
                "value": "from_exp_b",
                "count": shared_count,
            },
        },
    )

    # Query experiment A with filters
    query_a_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/query",
        json={
            "filters": {
                "test_value": shared_value,
                "count": shared_count,
            },
            "limit": 100,
            "offset": 0,
        },
    )
    assert query_a_response.status_code == 200
    query_a_results = query_a_response.json()

    # Should return only experiment A data
    assert len(query_a_results) == 1
    assert query_a_results[0]["experiment_uuid"] == experiment_a_uuid
    assert query_a_results[0]["participant_id"] == "QUERY_PARTICIPANT_A"
    assert query_a_results[0]["value"] == "from_exp_a"
    assert query_a_results[0]["number"] == 100

    # Query experiment B with same filters
    query_b_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/query",
        json={
            "filters": {
                "test_value": shared_value,
                "count": shared_count,
            },
            "limit": 100,
            "offset": 0,
        },
    )
    assert query_b_response.status_code == 200
    query_b_results = query_b_response.json()

    # Should return only experiment B data
    assert len(query_b_results) == 1
    assert query_b_results[0]["experiment_uuid"] == experiment_b_uuid
    assert query_b_results[0]["participant_id"] == "QUERY_PARTICIPANT_B"
    assert query_b_results[0]["value"] == "from_exp_b"
    assert query_b_results[0]["number"] == 200


@pytest.mark.asyncio
async def test_count_isolation_between_experiments(
    async_client, created_experiment_type, created_tags, timestamp
):
    """Test that count operations are properly isolated between experiments."""
    experiment_type_id = created_experiment_type["id"]

    # Create two experiments
    exp_a_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Count Test A - {timestamp}",
            "tags": ["data-test"],
        },
    )
    assert exp_a_response.status_code == 200
    experiment_a_uuid = exp_a_response.json()["uuid"]

    exp_b_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"Count Test B - {timestamp}",
            "tags": ["data-test"],
        },
    )
    assert exp_b_response.status_code == 200
    experiment_b_uuid = exp_b_response.json()["uuid"]

    # Add different amounts of data to each experiment
    # Experiment A: 3 rows
    for i in range(3):
        await async_client.post(
            f"/api/v1/experiment-data/{experiment_a_uuid}/data/",
            json={
                "participant_id": f"COUNT_PARTICIPANT_A_{i}",
                "data": {
                    "test_value": f"exp_a_data_{i}",
                    "number": 100 + i,
                    "value": "experiment_a",
                    "count": i,
                },
            },
        )

    # Experiment B: 5 rows
    for i in range(5):
        await async_client.post(
            f"/api/v1/experiment-data/{experiment_b_uuid}/data/",
            json={
                "participant_id": f"COUNT_PARTICIPANT_B_{i}",
                "data": {
                    "test_value": f"exp_b_data_{i}",
                    "number": 200 + i,
                    "value": "experiment_b",
                    "count": i,
                },
            },
        )

    # Count experiment A data
    count_a_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/count"
    )
    assert count_a_response.status_code == 200
    count_a_data = count_a_response.json()

    assert count_a_data["count"] == 3
    assert count_a_data["experiment_id"] == experiment_a_uuid

    # Count experiment B data
    count_b_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/count"
    )
    assert count_b_response.status_code == 200
    count_b_data = count_b_response.json()

    assert count_b_data["count"] == 5
    assert count_b_data["experiment_id"] == experiment_b_uuid


@pytest.mark.asyncio
async def test_crud_operations_isolated_by_experiment(
    async_client, created_experiment_type, created_tags, timestamp
):
    """Test that CRUD operations (update, delete) are properly isolated between experiments."""
    experiment_type_id = created_experiment_type["id"]

    # Create two experiments
    exp_a_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"CRUD Isolation Test A - {timestamp}",
            "tags": ["crud-test"],
        },
    )
    assert exp_a_response.status_code == 200
    experiment_a_uuid = exp_a_response.json()["uuid"]

    exp_b_response = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": experiment_type_id,
            "description": f"CRUD Isolation Test B - {timestamp}",
            "tags": ["crud-test"],
        },
    )
    assert exp_b_response.status_code == 200
    experiment_b_uuid = exp_b_response.json()["uuid"]

    # Create data in both experiments
    exp_a_data_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/",
        json={
            "participant_id": "CRUD_PARTICIPANT_A",
            "data": {
                "test_value": "original_a_value",
                "number": 100,
                "value": "experiment_a",
                "count": 1,
            },
        },
    )
    assert exp_a_data_response.status_code == 201
    exp_a_row_id = exp_a_data_response.json()["id"]

    exp_b_data_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/",
        json={
            "participant_id": "CRUD_PARTICIPANT_B",
            "data": {
                "test_value": "original_b_value",
                "number": 200,
                "value": "experiment_b",
                "count": 2,
            },
        },
    )
    assert exp_b_data_response.status_code == 201
    exp_b_row_id = exp_b_data_response.json()["id"]

    # Verify both rows exist
    assert exp_a_row_id is not None
    assert exp_b_row_id is not None

    # Test: Update row in experiment A should not affect experiment B
    update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/row/{exp_a_row_id}",
        json={
            "data": {
                "test_value": "updated_a_value",
                "number": 150,
            }
        },
    )
    assert update_response.status_code == 200
    updated_row = update_response.json()
    assert updated_row["test_value"] == "updated_a_value"
    assert updated_row["number"] == 150

    # Verify experiment B data is unchanged
    exp_b_check_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/row/{exp_b_row_id}"
    )
    assert exp_b_check_response.status_code == 200
    exp_b_unchanged = exp_b_check_response.json()
    assert exp_b_unchanged["test_value"] == "original_b_value"
    assert exp_b_unchanged["number"] == 200

    # Test: Try to access experiment A row from experiment B context (should fail)
    cross_access_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/row/{exp_a_row_id}"
    )
    assert cross_access_response.status_code == 404

    # Test: Try to update experiment A row from experiment B context (should fail)
    cross_update_response = await async_client.put(
        f"/api/v1/experiment-data/{experiment_b_uuid}/data/row/{exp_a_row_id}",
        json={
            "data": {
                "test_value": "malicious_update",
            }
        },
    )
    assert cross_update_response.status_code == 404

    # Verify experiment A row is still properly accessible from experiment A
    exp_a_final_check = await async_client.get(
        f"/api/v1/experiment-data/{experiment_a_uuid}/data/row/{exp_a_row_id}"
    )
    assert exp_a_final_check.status_code == 200
    final_row = exp_a_final_check.json()
    assert final_row["test_value"] == "updated_a_value"  # Our legitimate update
    assert final_row["number"] == 150
