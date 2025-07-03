"""Service for managing experiment data with dynamic tables."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import delete, insert, select, text, update

from wave_backend.models.database import engine


class ExperimentDataService:
    """Service for managing experiment data in dynamic tables using SQLAlchemy ORM."""

    # Map schema definition types to SQLAlchemy types
    TYPE_MAPPING = {
        "INTEGER": Integer,
        "FLOAT": Float,
        "STRING": String(255),
        "TEXT": Text,
        "BOOLEAN": Boolean,
        "DATETIME": DateTime,
        "JSON": JSON,
    }

    @classmethod
    async def create_experiment_table(
        cls, table_name: str, schema_definition: Dict[str, Any]
    ) -> bool:
        """Create a dynamic table for experiment data."""
        try:
            metadata = MetaData()

            # Always include these required columns
            columns = [
                Column("id", Integer, primary_key=True, index=True),
                Column("participant_id", String(100), nullable=False, index=True),
                Column("created_at", DateTime, nullable=False, server_default=text("now()")),
                Column("updated_at", DateTime, nullable=False, server_default=text("now()")),
            ]

            # Add custom columns from schema definition
            for column_name, column_type in schema_definition.items():
                if column_name in ["id", "participant_id", "created_at", "updated_at"]:
                    continue  # Skip reserved column names

                if isinstance(column_type, str):
                    column_type = column_type.upper()
                    if column_type in cls.TYPE_MAPPING:
                        columns.append(Column(column_name, cls.TYPE_MAPPING[column_type]))
                    else:
                        # Default to String if type not recognized
                        columns.append(Column(column_name, String(255)))
                elif isinstance(column_type, dict):
                    # Handle more complex column definitions
                    col_type = column_type.get("type", "STRING").upper()
                    nullable = column_type.get("nullable", True)

                    if col_type in cls.TYPE_MAPPING:
                        columns.append(
                            Column(column_name, cls.TYPE_MAPPING[col_type], nullable=nullable)
                        )

            # Create the table
            Table(table_name, metadata, *columns)

            async with engine.begin() as conn:
                await conn.run_sync(metadata.create_all)

            return True

        except SQLAlchemyError as e:
            print(f"Error creating table {table_name}: {e}")
            return False

    @classmethod
    async def drop_experiment_table(cls, table_name: str) -> bool:
        """Drop a dynamic experiment table."""
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            return True
        except SQLAlchemyError as e:
            print(f"Error dropping table {table_name}: {e}")
            return False

    @classmethod
    async def get_table_reflected(cls, table_name: str) -> Optional[Table]:
        """Get a reflected table object for ORM operations."""
        try:
            metadata = MetaData()
            async with engine.connect() as conn:
                await conn.run_sync(metadata.reflect, only=[table_name])
            return metadata.tables.get(table_name)
        except SQLAlchemyError:
            return None

    @classmethod
    async def insert_data_row(
        cls, table_name: str, participant_id: str, data: Dict[str, Any]
    ) -> Optional[int]:
        """Insert a data row into an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return None

            # Ensure participant_id is included
            data["participant_id"] = participant_id

            # Filter out any columns that don't exist in the table
            valid_data = {}
            for key, value in data.items():
                if key in table.columns:
                    valid_data[key] = value

            async with engine.begin() as conn:
                result = await conn.execute(
                    insert(table).values(**valid_data).returning(table.c.id)
                )
                return result.scalar()

        except SQLAlchemyError as e:
            print(f"Error inserting data into {table_name}: {e}")
            return None

    @classmethod
    async def get_data_rows(
        cls,
        table_name: str,
        participant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get data rows from an experiment table with ORM-style filtering."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return []

            query = select(table)

            # Apply filters
            if participant_id:
                query = query.where(table.c.participant_id == participant_id)

            if created_after:
                query = query.where(table.c.created_at >= created_after)

            if created_before:
                query = query.where(table.c.created_at <= created_before)

            if filters:
                for key, value in filters.items():
                    if key in table.columns:
                        query = query.where(table.c[key] == value)

            # Order by created_at descending and apply pagination
            query = query.order_by(table.c.created_at.desc()).limit(limit).offset(offset)

            async with engine.connect() as conn:
                result = await conn.execute(query)
                return [dict(row._mapping) for row in result]

        except SQLAlchemyError as e:
            print(f"Error querying data from {table_name}: {e}")
            return []

    @classmethod
    async def get_data_row_by_id(cls, table_name: str, row_id: int) -> Optional[Dict[str, Any]]:
        """Get a single data row by ID."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return None

            query = select(table).where(table.c.id == row_id)

            async with engine.connect() as conn:
                result = await conn.execute(query)
                row = result.first()
                return dict(row._mapping) if row else None

        except SQLAlchemyError as e:
            print(f"Error getting data row from {table_name}: {e}")
            return None

    @classmethod
    async def update_data_row(cls, table_name: str, row_id: int, data: Dict[str, Any]) -> bool:
        """Update a data row in an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return False

            # Don't allow updating id, created_at
            forbidden_columns = ["id", "created_at"]
            valid_data = {
                k: v for k, v in data.items() if k not in forbidden_columns and k in table.columns
            }

            if not valid_data:
                return False

            # Add updated_at
            valid_data["updated_at"] = datetime.utcnow()

            query = update(table).where(table.c.id == row_id).values(**valid_data)

            async with engine.begin() as conn:
                result = await conn.execute(query)
                return result.rowcount > 0

        except SQLAlchemyError as e:
            print(f"Error updating data in {table_name}: {e}")
            return False

    @classmethod
    async def delete_data_row(cls, table_name: str, row_id: int) -> bool:
        """Delete a data row from an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return False

            query = delete(table).where(table.c.id == row_id)

            async with engine.begin() as conn:
                result = await conn.execute(query)
                return result.rowcount > 0

        except SQLAlchemyError as e:
            print(f"Error deleting data from {table_name}: {e}")
            return False

    @classmethod
    async def get_table_columns(cls, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return []

            columns = []
            for column in table.columns:
                columns.append(
                    {
                        "column_name": column.name,
                        "column_type": str(column.type),
                        "is_nullable": column.nullable,
                        "default_value": str(column.default) if column.default else None,
                    }
                )

            return columns
        except SQLAlchemyError:
            return []

    @classmethod
    async def count_data_rows(
        cls,
        table_name: str,
        participant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count data rows in an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name)
            if not table:
                return 0

            query = select(table.c.id.label("count")).select_from(table)

            # Apply filters
            if participant_id:
                query = query.where(table.c.participant_id == participant_id)

            if filters:
                for key, value in filters.items():
                    if key in table.columns:
                        query = query.where(table.c[key] == value)

            async with engine.connect() as conn:
                result = await conn.execute(query)
                return len(result.fetchall())

        except SQLAlchemyError as e:
            print(f"Error counting data rows in {table_name}: {e}")
            return 0
