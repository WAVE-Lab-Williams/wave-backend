"""Tests for experiment data querying and filtering operations."""

import pytest


@pytest.mark.asyncio
async def test_pagination_with_limit_and_offset(async_client, populated_experiment):
    """Test pagination using limit and offset parameters."""
    experiment_uuid = populated_experiment["experiment_uuid"]

    response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?limit=2&offset=1"
    )

    assert response.status_code == 200
    paginated_data = response.json()
    assert len(paginated_data) == 2


@pytest.mark.asyncio
async def test_participant_id_filtering(async_client, populated_experiment):
    """Test filtering by participant ID."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    participant_id = populated_experiment["participant_id"]
    expected_count = len(populated_experiment["data_rows"])

    response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?participant_id={participant_id}"
    )

    assert response.status_code == 200
    filtered_data = response.json()
    assert len(filtered_data) == expected_count
    assert all(row["participant_id"] == participant_id for row in filtered_data)


@pytest.mark.asyncio
async def test_custom_query_filters(async_client, experiment_setup, updated_experiment_data):
    """Test custom query filters using POST endpoint."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    # Create data with specific number value to filter on
    create_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/", json=updated_experiment_data
    )
    assert create_response.status_code == 201

    # Query with custom filters
    query_data = {
        "participant_id": participant_id,
        "filters": {"number": 99},  # From updated_experiment_data
        "limit": 10,
        "offset": 0,
    }

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/query", json=query_data
    )

    assert response.status_code == 200
    query_results = response.json()
    assert len(query_results) == 1
    assert query_results[0]["number"] == 99


@pytest.mark.asyncio
async def test_query_with_no_results(async_client, populated_experiment):
    """Test query that returns no results."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    participant_id = populated_experiment["participant_id"]

    query_data = {
        "participant_id": participant_id,
        "filters": {"number": 999999},  # Non-existent value
        "limit": 10,
        "offset": 0,
    }

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/query", json=query_data
    )

    assert response.status_code == 200
    query_results = response.json()
    assert len(query_results) == 0


@pytest.mark.asyncio
async def test_query_with_multiple_filters(
    async_client, experiment_setup, additional_experiment_data
):
    """Test query with multiple filter conditions."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    # Create data with specific values
    for data in additional_experiment_data:
        response = await async_client.post(
            f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data
        )
        assert response.status_code == 201

    # Query with multiple filters
    query_data = {
        "participant_id": participant_id,
        "filters": {"value": "data1", "count": 10},  # From first additional_experiment_data
        "limit": 10,
        "offset": 0,
    }

    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/query", json=query_data
    )

    assert response.status_code == 200
    query_results = response.json()
    assert len(query_results) == 1
    assert query_results[0]["value"] == "data1"
    assert query_results[0]["count"] == 10


@pytest.mark.asyncio
async def test_pagination_edge_cases(async_client, populated_experiment):
    """Test pagination edge cases."""
    experiment_uuid = populated_experiment["experiment_uuid"]
    total_count = len(populated_experiment["data_rows"])

    # Test offset beyond data count
    response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?limit=10&offset=100"
    )
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Test limit larger than available data
    response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?limit=100&offset=0"
    )
    assert response.status_code == 200
    assert len(response.json()) == total_count


@pytest.mark.asyncio
async def test_filter_by_non_existent_participant(async_client, populated_experiment):
    """Test filtering by non-existent participant ID."""
    experiment_uuid = populated_experiment["experiment_uuid"]

    response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?participant_id=non-existent-participant"
    )

    assert response.status_code == 200
    filtered_data = response.json()
    assert len(filtered_data) == 0


@pytest.mark.asyncio
async def test_comprehensive_query_workflow(
    async_client, experiment_setup, sample_experiment_data, additional_experiment_data
):
    """Test comprehensive querying workflow with various filters."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    participant_id = experiment_setup["participant_id"]

    # Create initial data
    await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/", json=sample_experiment_data
    )

    # Create additional data
    for data in additional_experiment_data:
        await async_client.post(f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data)

    # Test 1: Get all data (no filters)
    all_response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/")
    assert len(all_response.json()) == 3

    # Test 2: Paginate results
    page1_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?limit=2&offset=0"
    )
    assert len(page1_response.json()) == 2

    # Test 3: Filter by participant
    participant_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/?participant_id={participant_id}"
    )
    assert len(participant_response.json()) == 3

    # Test 4: Custom query filter
    query_data = {
        "participant_id": participant_id,
        "filters": {"test_value": "some test data"},
        "limit": 10,
        "offset": 0,
    }
    query_response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/query", json=query_data
    )
    assert len(query_response.json()) == 1
