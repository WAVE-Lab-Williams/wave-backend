"""Tests for search service functionality."""

from datetime import datetime, timedelta

import pytest

from wave_backend.schemas.schemas import (
    ExperimentCreate,
    ExperimentTypeCreate,
    TagCreate,
)
from wave_backend.services.experiment_data import ExperimentDataService
from wave_backend.services.experiment_types import ExperimentTypeService
from wave_backend.services.experiments import ExperimentService
from wave_backend.services.search import SearchService
from wave_backend.services.tags import TagService


@pytest.fixture
async def search_test_setup(db_session):
    """Create test data for search tests."""
    # Create tags
    tag1 = await TagService.create_tag(
        db_session, TagCreate(name="neural", description="Neural studies")
    )
    tag2 = await TagService.create_tag(
        db_session, TagCreate(name="cognitive", description="Cognitive research")
    )
    tag3 = await TagService.create_tag(
        db_session, TagCreate(name="behavioral", description="Behavioral analysis")
    )

    # Create experiment types
    exp_type1 = await ExperimentTypeService.create_experiment_type(
        db_session,
        ExperimentTypeCreate(
            name="reaction_time_test",
            description="Test for measuring reaction times in cognitive tasks",
            table_name="reaction_time_test_table",
            schema_definition={
                "reaction_time": "FLOAT",
                "accuracy": "FLOAT",
                "stimulus_type": "STRING",
            },
        ),
    )

    exp_type2 = await ExperimentTypeService.create_experiment_type(
        db_session,
        ExperimentTypeCreate(
            name="memory_test",
            description="Memory retention and recall experiments",
            table_name="memory_test_table",
            schema_definition={
                "recall_score": "FLOAT",
                "retention_time": "INTEGER",
                "word_count": "INTEGER",
            },
        ),
    )

    # Create experiments
    exp1 = await ExperimentService.create_experiment(
        db_session,
        ExperimentCreate(
            experiment_type_id=exp_type1.id,
            description="Reaction time study with visual stimuli",
            tags=["neural", "cognitive"],
        ),
    )

    exp2 = await ExperimentService.create_experiment(
        db_session,
        ExperimentCreate(
            experiment_type_id=exp_type1.id,
            description="Reaction time study with auditory stimuli",
            tags=["neural"],
        ),
    )

    exp3 = await ExperimentService.create_experiment(
        db_session,
        ExperimentCreate(
            experiment_type_id=exp_type2.id,
            description="Memory recall with word lists",
            tags=["cognitive", "behavioral"],
        ),
    )

    # Add some experiment data
    await ExperimentDataService.insert_data_row(
        exp_type1.table_name,
        str(exp1.uuid),
        "PARTICIPANT_001",
        {"reaction_time": 1.23, "accuracy": 0.85, "stimulus_type": "visual"},
        db_session,
    )

    await ExperimentDataService.insert_data_row(
        exp_type1.table_name,
        str(exp2.uuid),
        "PARTICIPANT_002",
        {"reaction_time": 0.98, "accuracy": 0.92, "stimulus_type": "audio"},
        db_session,
    )

    await ExperimentDataService.insert_data_row(
        exp_type2.table_name,
        str(exp3.uuid),
        "PARTICIPANT_003",
        {"recall_score": 0.78, "retention_time": 300, "word_count": 20},
        db_session,
    )

    return {
        "tags": [tag1, tag2, tag3],
        "experiment_types": [exp_type1, exp_type2],
        "experiments": [exp1, exp2, exp3],
    }


@pytest.mark.anyio
async def test_search_experiments_by_tags(db_session, search_test_setup):
    """Test searching experiments by tags."""
    # Test single tag search
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], match_all=True
    )
    assert len(results) == 2
    experiment_descriptions = [exp.description for exp in results]
    assert "Reaction time study with visual stimuli" in experiment_descriptions
    assert "Reaction time study with auditory stimuli" in experiment_descriptions

    # Test multiple tag search with match_all=True
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural", "cognitive"], match_all=True
    )
    assert len(results) == 1
    assert results[0].description == "Reaction time study with visual stimuli"

    # Test multiple tag search with match_all=False
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural", "behavioral"], match_all=False
    )
    assert len(results) == 3  # All experiments match at least one tag

    # Test tag that doesn't exist
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["nonexistent"], match_all=True
    )
    assert len(results) == 0


@pytest.mark.anyio
async def test_search_experiment_types_by_description(db_session, search_test_setup):
    """Test searching experiment types by description text."""
    # Test search by description
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="reaction"
    )
    assert len(results) == 1
    assert results[0].name == "reaction_time_test"

    # Test search by name
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="memory"
    )
    assert len(results) == 1
    assert results[0].name == "memory_test"

    # Test case-insensitive search
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="COGNITIVE"
    )
    assert len(results) == 1
    assert results[0].name == "reaction_time_test"

    # Test search that matches nothing
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="nonexistent"
    )
    assert len(results) == 0


@pytest.mark.anyio
async def test_search_tags_by_name(db_session, search_test_setup):
    """Test searching tags by name."""
    # Test search by name
    results = await SearchService.search_tags_by_name(db_session, search_text="neural")
    assert len(results) == 1
    assert results[0].name == "neural"

    # Test search by description
    results = await SearchService.search_tags_by_name(db_session, search_text="studies")
    assert len(results) == 1
    assert results[0].name == "neural"

    # Test partial match
    results = await SearchService.search_tags_by_name(db_session, search_text="cogn")
    assert len(results) == 1
    assert results[0].name == "cognitive"

    # Test case-insensitive search
    results = await SearchService.search_tags_by_name(db_session, search_text="BEHAVIORAL")
    assert len(results) == 1
    assert results[0].name == "behavioral"


@pytest.mark.anyio
async def test_search_experiments_by_description_and_type(db_session, search_test_setup):
    """Test searching experiment descriptions within a specific type."""
    experiment_types = search_test_setup["experiment_types"]
    reaction_time_type = experiment_types[0]

    # Test search within specific type
    results = await SearchService.search_experiments_by_description_and_type(
        db_session, experiment_type_id=reaction_time_type.id, search_text="visual"
    )
    assert len(results) == 1
    assert results[0].description == "Reaction time study with visual stimuli"

    # Test search within specific type with no matches
    results = await SearchService.search_experiments_by_description_and_type(
        db_session, experiment_type_id=reaction_time_type.id, search_text="memory"
    )
    assert len(results) == 0

    # Test search with nonexistent type
    results = await SearchService.search_experiments_by_description_and_type(
        db_session, experiment_type_id=999, search_text="visual"
    )
    assert len(results) == 0


@pytest.mark.anyio
async def test_advanced_experiment_search(db_session, search_test_setup):
    """Test advanced search combining multiple criteria."""
    experiment_types = search_test_setup["experiment_types"]
    reaction_time_type = experiment_types[0]

    # Test search with text and tags
    results = await SearchService.advanced_experiment_search(
        db_session,
        search_text="visual",
        tags=["neural"],
        match_all_tags=True,
    )
    assert len(results) == 1
    assert results[0].description == "Reaction time study with visual stimuli"

    # Test search with type filter
    results = await SearchService.advanced_experiment_search(
        db_session,
        experiment_type_id=reaction_time_type.id,
        tags=["neural"],
        match_all_tags=True,
    )
    assert len(results) == 2

    # Test search with conflicting criteria
    results = await SearchService.advanced_experiment_search(
        db_session,
        search_text="visual",
        tags=["behavioral"],
        match_all_tags=True,
    )
    assert len(results) == 0

    # Test search with multiple tags (match any)
    results = await SearchService.advanced_experiment_search(
        db_session,
        tags=["neural", "behavioral"],
        match_all_tags=False,
    )
    assert len(results) == 3


@pytest.mark.anyio
async def test_date_range_filtering(db_session, search_test_setup):
    """Test date range filtering across all search methods."""
    # Create a future date
    future_date = datetime.now() + timedelta(days=1)

    # Test experiments search with future date (should return no results)
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], created_after=future_date
    )
    assert len(results) == 0

    # Test with past date (should return results)
    past_date = datetime.now() - timedelta(days=1)
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], created_after=past_date
    )
    assert len(results) == 2

    # Test experiment types search with date filter
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="reaction", created_after=past_date
    )
    assert len(results) == 1

    # Test tags search with date filter
    results = await SearchService.search_tags_by_name(
        db_session, search_text="neural", created_after=past_date
    )
    assert len(results) == 1


@pytest.mark.anyio
async def test_pagination(db_session, search_test_setup):
    """Test pagination across search methods."""
    # Test experiments pagination
    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], limit=1, skip=0
    )
    assert len(results) == 1

    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], limit=1, skip=1
    )
    assert len(results) == 1

    results = await SearchService.search_experiments_by_tags(
        db_session, tags=["neural"], limit=1, skip=2
    )
    assert len(results) == 0


@pytest.mark.anyio
async def test_get_experiment_data_by_tags(db_session, search_test_setup):
    """Test getting experiment data by tags."""
    result = await SearchService.get_experiment_data_by_tags(
        db_session, tags=["neural"], match_all=False
    )

    assert "data" in result
    assert "total_rows" in result
    assert "total_experiments" in result
    assert "experiment_info" in result

    # Should have data from both neural experiments
    assert result["total_experiments"] == 2
    assert result["total_rows"] == 2
    assert len(result["data"]) == 2

    # Verify experiment metadata is included
    for row in result["data"]:
        assert "experiment_metadata" in row
        assert "experiment_uuid" in row["experiment_metadata"]
        assert "experiment_type_name" in row["experiment_metadata"]
        assert "experiment_tags" in row["experiment_metadata"]

    # Test with specific tag that has only one experiment
    result = await SearchService.get_experiment_data_by_tags(
        db_session, tags=["behavioral"], match_all=True
    )

    assert result["total_experiments"] == 1
    assert result["total_rows"] == 1
    assert len(result["data"]) == 1

    # Verify the data is from the correct experiment
    assert result["data"][0]["experiment_metadata"]["experiment_tags"] == [
        "cognitive",
        "behavioral",
    ]


@pytest.mark.anyio
async def test_search_with_empty_results(db_session, search_test_setup):
    """Test search methods with queries that return no results."""
    # Test with nonexistent tag
    results = await SearchService.search_experiments_by_tags(db_session, tags=["nonexistent"])
    assert len(results) == 0

    # Test with nonexistent text
    results = await SearchService.search_experiment_types_by_description(
        db_session, search_text="nonexistent"
    )
    assert len(results) == 0

    # Test with nonexistent tag name
    results = await SearchService.search_tags_by_name(db_session, search_text="nonexistent")
    assert len(results) == 0

    # Test data by tags with no matches
    result = await SearchService.get_experiment_data_by_tags(db_session, tags=["nonexistent"])
    assert result["total_experiments"] == 0
    assert result["total_rows"] == 0
    assert len(result["data"]) == 0
