"""Tests for experiment discovery and tag-based lookup operations."""

import pytest

from tests.medium.e2e.conftest import assert_tag_lookup_contains_experiment


@pytest.mark.asyncio
async def test_lookup_experiments_by_single_tag(async_client, experiment_setup):
    """Test looking up experiments by a single tag."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get("/api/v1/experiments/?tags=crud-test", headers=headers)

    assert response.status_code == 200
    tag_experiments = response.json()
    assert len(tag_experiments) >= 1
    assert_tag_lookup_contains_experiment(tag_experiments, experiment_uuid)


@pytest.mark.asyncio
async def test_lookup_experiments_by_multiple_tags(async_client, experiment_setup):
    """Test looking up experiments by multiple tags."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(
        "/api/v1/experiments/?tags=crud-test&tags=data-test", headers=headers
    )

    assert response.status_code == 200
    multi_tag_experiments = response.json()
    assert len(multi_tag_experiments) >= 1
    assert_tag_lookup_contains_experiment(multi_tag_experiments, experiment_uuid)


@pytest.mark.asyncio
async def test_lookup_experiments_by_non_existent_tag(async_client):
    """Test looking up experiments by non-existent tag returns empty results."""
    headers = {"Authorization": "Bearer test_token"}
    response = await async_client.get("/api/v1/experiments/?tags=nonexistent-tag", headers=headers)

    assert response.status_code == 200
    empty_experiments = response.json()
    assert len(empty_experiments) == 0


@pytest.mark.asyncio
async def test_tag_filtering_specificity(
    async_client, experiment_setup, created_tags, created_experiment_type, timestamp
):
    """Test that tag filtering is specific and doesn't return unrelated experiments."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    headers = {"Authorization": "Bearer test_token"}
    # Create another experiment with different tags
    other_tag_data = {"name": f"other-tag-{timestamp}", "description": "Other tag for testing"}
    tag_response = await async_client.post("/api/v1/tags/", json=other_tag_data, headers=headers)
    assert tag_response.status_code == 200

    other_experiment_data = {
        "experiment_type_id": created_experiment_type["id"],
        "description": "Other experiment with different tags",
        "tags": [f"other-tag-{timestamp}"],
    }
    other_exp_response = await async_client.post(
        "/api/v1/experiments/", json=other_experiment_data, headers=headers
    )
    assert other_exp_response.status_code == 200
    other_exp_uuid = other_exp_response.json()["uuid"]

    # Search for original experiment tags - should not include the other experiment
    response = await async_client.get("/api/v1/experiments/?tags=crud-test", headers=headers)
    tag_experiments = response.json()

    # Should contain original experiment
    assert_tag_lookup_contains_experiment(tag_experiments, experiment_uuid)

    # Should NOT contain the other experiment
    other_exp_found = any(exp["uuid"] == other_exp_uuid for exp in tag_experiments)
    assert not other_exp_found


@pytest.mark.asyncio
async def test_experiment_discovery_with_experiment_type_filter(async_client, experiment_setup):
    """Test combining tag search with experiment type filtering."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]
    experiment_type_id = experiment_setup["experiment_type"]["id"]

    response = await async_client.get(
        f"/api/v1/experiments/?tags=crud-test&experiment_type_id={experiment_type_id}",
        headers=headers,
    )

    assert response.status_code == 200
    filtered_experiments = response.json()
    assert len(filtered_experiments) >= 1
    assert_tag_lookup_contains_experiment(filtered_experiments, experiment_uuid)

    # Verify all returned experiments have the correct experiment type
    for exp in filtered_experiments:
        assert exp["experiment_type_id"] == experiment_type_id


@pytest.mark.asyncio
async def test_experiment_discovery_pagination(
    async_client, experiment_setup, created_experiment_type, timestamp
):
    """Test pagination with tag-based experiment discovery."""
    headers = {"Authorization": "Bearer test_token"}
    # Create multiple experiments with the same tag
    for i in range(3):
        exp_data = {
            "experiment_type_id": created_experiment_type["id"],
            "description": f"Test experiment {i} for pagination",
            "tags": ["crud-test"],
        }
        response = await async_client.post("/api/v1/experiments/", json=exp_data, headers=headers)
        assert response.status_code == 200

    # Test pagination
    response = await async_client.get(
        "/api/v1/experiments/?tags=crud-test&limit=2&skip=0", headers=headers
    )

    assert response.status_code == 200
    page1_experiments = response.json()
    assert len(page1_experiments) == 2

    # Get second page
    response = await async_client.get(
        "/api/v1/experiments/?tags=crud-test&limit=2&skip=2", headers=headers
    )

    assert response.status_code == 200
    page2_experiments = response.json()
    assert len(page2_experiments) >= 1  # At least our original experiment


@pytest.mark.asyncio
async def test_case_sensitive_tag_search(async_client, experiment_setup):
    """Test that tag search is case sensitive."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]

    # Search with correct case
    correct_response = await async_client.get(
        "/api/v1/experiments/?tags=crud-test", headers=headers
    )
    assert correct_response.status_code == 200
    correct_results = correct_response.json()
    assert_tag_lookup_contains_experiment(correct_results, experiment_uuid)

    # Search with different case - should return no results
    wrong_case_response = await async_client.get(
        "/api/v1/experiments/?tags=CRUD-TEST", headers=headers
    )
    assert wrong_case_response.status_code == 200
    wrong_case_results = wrong_case_response.json()
    # Should not find the experiment due to case mismatch
    wrong_case_found = any(exp["uuid"] == experiment_uuid for exp in wrong_case_results)
    assert not wrong_case_found


@pytest.mark.asyncio
async def test_experiment_tag_inclusion_in_response(async_client, experiment_setup):
    """Test that experiment responses include tag information."""
    headers = {"Authorization": "Bearer test_token"}
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get("/api/v1/experiments/?tags=crud-test", headers=headers)

    assert response.status_code == 200
    tag_experiments = response.json()

    # Find our experiment
    our_experiment = None
    for exp in tag_experiments:
        if exp["uuid"] == experiment_uuid:
            our_experiment = exp
            break

    assert our_experiment is not None
    assert "tags" in our_experiment
    assert isinstance(our_experiment["tags"], list)
    assert "crud-test" in our_experiment["tags"]
    assert "data-test" in our_experiment["tags"]


@pytest.mark.asyncio
async def test_comprehensive_experiment_discovery_workflow(
    async_client, experiment_setup, created_experiment_type, timestamp
):
    """Test comprehensive experiment discovery workflow."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    headers = {"Authorization": "Bearer test_token"}
    # Test 1: Basic tag search
    basic_response = await async_client.get("/api/v1/experiments/?tags=crud-test", headers=headers)
    assert basic_response.status_code == 200
    assert_tag_lookup_contains_experiment(basic_response.json(), experiment_uuid)

    # Test 2: Multi-tag search
    multi_response = await async_client.get(
        "/api/v1/experiments/?tags=crud-test&tags=data-test", headers=headers
    )
    assert multi_response.status_code == 200
    assert_tag_lookup_contains_experiment(multi_response.json(), experiment_uuid)

    # Test 3: Combined with type filter
    type_response = await async_client.get(
        f"/api/v1/experiments/?tags=crud-test&experiment_type_id={created_experiment_type['id']}",
        headers=headers,
    )
    assert type_response.status_code == 200
    assert_tag_lookup_contains_experiment(type_response.json(), experiment_uuid)

    # Test 4: Non-existent tag
    empty_response = await async_client.get(
        "/api/v1/experiments/?tags=non-existent", headers=headers
    )
    assert empty_response.status_code == 200
    assert len(empty_response.json()) == 0

    # Test 5: All experiments (no filters)
    all_response = await async_client.get("/api/v1/experiments/", headers=headers)
    assert all_response.status_code == 200
    assert_tag_lookup_contains_experiment(all_response.json(), experiment_uuid)
