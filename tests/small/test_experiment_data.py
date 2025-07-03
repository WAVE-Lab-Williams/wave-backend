"""Unit tests for experiment data operations."""

from datetime import UTC, datetime

import pytest

from wave_backend.services.experiment_data import ExperimentDataService


class TestExperimentDataService:
    """Test cases for ExperimentDataService."""

    @pytest.mark.asyncio
    async def test_create_experiment_table(self, mocker):
        """Test creating an experiment table."""
        table_name = "test_experiment_data"
        schema_definition = {
            "reaction_time": "FLOAT",
            "accuracy": "FLOAT",
            "difficulty_level": "INTEGER",
        }

        mock_create = mocker.patch.object(ExperimentDataService, "create_experiment_table")
        mock_create.return_value = True

        result = await ExperimentDataService.create_experiment_table(table_name, schema_definition)

        assert result is True
        mock_create.assert_called_once_with(table_name, schema_definition)

    @pytest.mark.asyncio
    async def test_drop_experiment_table(self, mocker):
        """Test dropping an experiment table."""
        table_name = "test_experiment_data"

        mock_drop = mocker.patch.object(ExperimentDataService, "drop_experiment_table")
        mock_drop.return_value = True

        result = await ExperimentDataService.drop_experiment_table(table_name)

        assert result is True
        mock_drop.assert_called_once_with(table_name)

    @pytest.mark.asyncio
    async def test_insert_data_row(self, mocker):
        """Test inserting a data row."""
        table_name = "test_experiment_data"
        participant_id = "PART-001"
        data = {"reaction_time": 1.23, "accuracy": 0.85, "difficulty_level": 2}

        mock_insert = mocker.patch.object(ExperimentDataService, "insert_data_row")
        mock_insert.return_value = 1

        result = await ExperimentDataService.insert_data_row(table_name, participant_id, data)

        assert result == 1
        mock_insert.assert_called_once_with(table_name, participant_id, data)

    @pytest.mark.asyncio
    async def test_get_data_rows(self, mocker):
        """Test retrieving data rows."""
        table_name = "test_experiment_data"
        participant_id = "PART-001"

        expected_rows = [
            {
                "id": 1,
                "participant_id": "PART-001",
                "reaction_time": 1.23,
                "accuracy": 0.85,
                "difficulty_level": 2,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        ]

        mock_get = mocker.patch.object(ExperimentDataService, "get_data_rows")
        mock_get.return_value = expected_rows

        result = await ExperimentDataService.get_data_rows(table_name, participant_id)

        assert result == expected_rows
        mock_get.assert_called_once_with(table_name, participant_id)

    @pytest.mark.asyncio
    async def test_get_data_row_by_id(self, mocker):
        """Test retrieving a specific data row by ID."""
        table_name = "test_experiment_data"
        row_id = 1

        expected_row = {
            "id": 1,
            "participant_id": "PART-001",
            "reaction_time": 1.23,
            "accuracy": 0.85,
            "difficulty_level": 2,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        mock_get = mocker.patch.object(ExperimentDataService, "get_data_row_by_id")
        mock_get.return_value = expected_row

        result = await ExperimentDataService.get_data_row_by_id(table_name, row_id)

        assert result == expected_row
        mock_get.assert_called_once_with(table_name, row_id)

    @pytest.mark.asyncio
    async def test_update_data_row(self, mocker):
        """Test updating a data row."""
        table_name = "test_experiment_data"
        row_id = 1
        data = {"reaction_time": 1.45, "accuracy": 0.90}

        mock_update = mocker.patch.object(ExperimentDataService, "update_data_row")
        mock_update.return_value = True

        result = await ExperimentDataService.update_data_row(table_name, row_id, data)

        assert result is True
        mock_update.assert_called_once_with(table_name, row_id, data)

    @pytest.mark.asyncio
    async def test_delete_data_row(self, mocker):
        """Test deleting a data row."""
        table_name = "test_experiment_data"
        row_id = 1

        mock_delete = mocker.patch.object(ExperimentDataService, "delete_data_row")
        mock_delete.return_value = True

        result = await ExperimentDataService.delete_data_row(table_name, row_id)

        assert result is True
        mock_delete.assert_called_once_with(table_name, row_id)

    @pytest.mark.asyncio
    async def test_get_table_columns(self, mocker):
        """Test retrieving table column information."""
        table_name = "test_experiment_data"

        expected_columns = [
            {
                "column_name": "id",
                "column_type": "INTEGER",
                "is_nullable": False,
                "default_value": None,
            },
            {
                "column_name": "participant_id",
                "column_type": "VARCHAR",
                "is_nullable": False,
                "default_value": None,
            },
            {
                "column_name": "reaction_time",
                "column_type": "FLOAT",
                "is_nullable": True,
                "default_value": None,
            },
        ]

        mock_get_columns = mocker.patch.object(ExperimentDataService, "get_table_columns")
        mock_get_columns.return_value = expected_columns

        result = await ExperimentDataService.get_table_columns(table_name)

        assert result == expected_columns
        mock_get_columns.assert_called_once_with(table_name)

    @pytest.mark.asyncio
    async def test_count_data_rows(self, mocker):
        """Test counting data rows."""
        table_name = "test_experiment_data"
        participant_id = "PART-001"

        mock_count = mocker.patch.object(ExperimentDataService, "count_data_rows")
        mock_count.return_value = 5

        result = await ExperimentDataService.count_data_rows(table_name, participant_id)

        assert result == 5
        mock_count.assert_called_once_with(table_name, participant_id)

    @pytest.mark.asyncio
    async def test_get_data_rows_with_date_filters(self, mocker):
        """Test retrieving data rows with date filters."""
        table_name = "test_experiment_data"
        created_after = datetime(2024, 1, 1)
        created_before = datetime(2024, 12, 31)

        mock_get = mocker.patch.object(ExperimentDataService, "get_data_rows")
        mock_get.return_value = []

        await ExperimentDataService.get_data_rows(
            table_name, created_after=created_after, created_before=created_before
        )

        mock_get.assert_called_once_with(
            table_name, created_after=created_after, created_before=created_before
        )

    @pytest.mark.asyncio
    async def test_get_data_rows_with_custom_filters(self, mocker):
        """Test retrieving data rows with custom filters."""
        table_name = "test_experiment_data"
        filters = {"difficulty_level": 2, "accuracy": 0.85}

        mock_get = mocker.patch.object(ExperimentDataService, "get_data_rows")
        mock_get.return_value = []

        await ExperimentDataService.get_data_rows(table_name, filters=filters)

        mock_get.assert_called_once_with(table_name, filters=filters)

    @pytest.mark.asyncio
    async def test_get_data_rows_with_pagination(self, mocker):
        """Test retrieving data rows with pagination."""
        table_name = "test_experiment_data"
        limit = 50
        offset = 10

        mock_get = mocker.patch.object(ExperimentDataService, "get_data_rows")
        mock_get.return_value = []

        await ExperimentDataService.get_data_rows(table_name, limit=limit, offset=offset)

        mock_get.assert_called_once_with(table_name, limit=limit, offset=offset)
