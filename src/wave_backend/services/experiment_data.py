"""Service for managing experiment data with dynamic tables."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import delete, insert, select, text, update

from wave_backend.schemas.column_types import TYPE_MAPPING
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


class ExperimentDataService:
    """Service for managing experiment data in dynamic tables using SQLAlchemy ORM."""

    # Map schema definition types to SQLAlchemy types

    @classmethod
    async def create_experiment_table(
        cls, table_name: str, schema_definition: Dict[str, Any], db: AsyncSession
    ) -> bool:
        """Create a dynamic table for experiment data."""
        try:
            metadata = MetaData()

            # Always include these required columns
            columns = [
                Column("id", Integer, primary_key=True, index=True),
                Column("experiment_uuid", PostgresUUID(as_uuid=True), nullable=False, index=True),
                Column("participant_id", String(100), nullable=False, index=True),
                Column("created_at", DateTime, nullable=False, server_default=text("now()")),
                Column("updated_at", DateTime, nullable=False, server_default=text("now()")),
            ]

            # Add custom columns from schema definition
            for column_name, column_type in schema_definition.items():
                if column_name in [
                    "id",
                    "experiment_uuid",
                    "participant_id",
                    "created_at",
                    "updated_at",
                ]:
                    continue  # Skip reserved column names

                if isinstance(column_type, str):
                    column_type = column_type.upper()
                    if column_type in TYPE_MAPPING:
                        columns.append(Column(column_name, TYPE_MAPPING[column_type]))
                    else:
                        # Default to String if type not recognized
                        columns.append(Column(column_name, String(255)))
                elif isinstance(column_type, dict):
                    # Handle more complex column definitions
                    col_type = column_type.get("type", "STRING").upper()
                    nullable = column_type.get("nullable", True)

                    if col_type in TYPE_MAPPING:
                        columns.append(
                            Column(column_name, TYPE_MAPPING[col_type], nullable=nullable)
                        )

            # Create the table
            Table(table_name, metadata, *columns)

            # Use the provided database session's connection
            connection = await db.connection()
            await connection.run_sync(metadata.create_all)

            # Commit the transaction to ensure the table is persisted
            await db.commit()

            return True

        except SQLAlchemyError as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating table {table_name}: {e}")
            return False

    @classmethod
    async def drop_experiment_table(cls, table_name: str, db: AsyncSession) -> bool:
        """Drop a dynamic experiment table."""
        try:
            # Use the provided database session's connection
            await db.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            await db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error dropping table {table_name}: {e}")
            return False

    @classmethod
    async def get_table_reflected(cls, table_name: str, db: AsyncSession) -> Optional[Table]:
        """Get a reflected table object for ORM operations."""
        try:
            metadata = MetaData()
            # Use the provided database session's connection
            connection = await db.connection()
            await connection.run_sync(metadata.reflect, only=[table_name])
            return metadata.tables.get(table_name)
        except SQLAlchemyError:
            return None

    @classmethod
    async def insert_data_row(
        cls,
        table_name: str,
        experiment_uuid: str,
        participant_id: str,
        data: Dict[str, Any],
        db: AsyncSession,
    ) -> Optional[int]:
        """Insert a data row into an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return None

            # Ensure experiment_uuid and participant_id are included
            data["experiment_uuid"] = experiment_uuid
            data["participant_id"] = participant_id

            # Check for columns that don't exist in the table
            missing_columns = []
            valid_data = {}
            for key, value in data.items():
                if key in table.columns:
                    valid_data[key] = value
                else:
                    missing_columns.append(key)

            # If there are missing columns, raise an error
            if missing_columns:
                raise ValueError(
                    f"Unknown columns: {missing_columns}. "
                    "Please update the experiment type schema to include these columns."
                )

            # Use the provided database session
            result = await db.execute(insert(table).values(**valid_data).returning(table.c.id))
            await db.commit()
            return result.scalar()

        except SQLAlchemyError as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
            raise

    @classmethod
    def _apply_query_filters(
        cls,
        query,
        table,
        experiment_uuid: Optional[str] = None,
        participant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ):
        """Apply filters to a query."""
        if experiment_uuid:
            query = query.where(table.c.experiment_uuid == experiment_uuid)

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

        return query

    @classmethod
    async def get_data_rows(
        cls,
        table_name: str,
        db: AsyncSession,
        experiment_uuid: Optional[str] = None,
        participant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get data rows from an experiment table with ORM-style filtering."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return []

            query = select(table)
            query = cls._apply_query_filters(
                query,
                table,
                experiment_uuid,
                participant_id,
                filters,
                created_after,
                created_before,
            )
            query = query.order_by(table.c.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            return [dict(row._mapping) for row in result]

        except SQLAlchemyError as e:
            logger.error(f"Error querying data from {table_name}: {e}")
            return []

    @classmethod
    async def get_data_row_by_id(
        cls, table_name: str, row_id: int, db: AsyncSession, experiment_uuid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a single data row by ID."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return None

            query = select(table).where(table.c.id == row_id)

            # Optionally filter by experiment_uuid for additional security
            if experiment_uuid:
                query = query.where(table.c.experiment_uuid == experiment_uuid)

            # Use the provided database session
            result = await db.execute(query)
            row = result.first()
            return dict(row._mapping) if row else None

        except SQLAlchemyError as e:
            logger.error(f"Error getting data row from {table_name}: {e}")
            return None

    @classmethod
    async def update_data_row(
        cls,
        table_name: str,
        row_id: int,
        data: Dict[str, Any],
        db: AsyncSession,
        experiment_uuid: Optional[str] = None,
    ) -> bool:
        """Update a data row in an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return False

            # Don't allow updating id, experiment_uuid, created_at
            forbidden_columns = ["id", "experiment_uuid", "created_at"]
            valid_data = {
                k: v for k, v in data.items() if k not in forbidden_columns and k in table.columns
            }

            if not valid_data:
                return False

            # Add updated_at
            valid_data["updated_at"] = datetime.now(UTC).replace(tzinfo=None)

            query = update(table).where(table.c.id == row_id)

            # Optionally filter by experiment_uuid for additional security
            if experiment_uuid:
                query = query.where(table.c.experiment_uuid == experiment_uuid)

            query = query.values(**valid_data)

            # Use the provided database session
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0

        except SQLAlchemyError as e:
            logger.error(f"Error updating data in {table_name}: {e}")
            return False

    @classmethod
    async def delete_data_row(
        cls, table_name: str, row_id: int, db: AsyncSession, experiment_uuid: Optional[str] = None
    ) -> bool:
        """Delete a data row from an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return False

            query = delete(table).where(table.c.id == row_id)

            # Optionally filter by experiment_uuid for additional security
            if experiment_uuid:
                query = query.where(table.c.experiment_uuid == experiment_uuid)

            # Use the provided database session
            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0

        except SQLAlchemyError as e:
            logger.error(f"Error deleting data from {table_name}: {e}")
            return False

    @classmethod
    async def get_table_columns(cls, table_name: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
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
        db: AsyncSession,
        experiment_uuid: Optional[str] = None,
        participant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count data rows in an experiment table."""
        try:
            table = await cls.get_table_reflected(table_name, db)
            if table is None:
                return 0

            query = select(func.count(table.c.id)).select_from(table)
            query = cls._apply_query_filters(query, table, experiment_uuid, participant_id, filters)

            # Use the provided database session
            result = await db.execute(query)
            return result.scalar()

        except SQLAlchemyError as e:
            logger.error(f"Error counting data rows in {table_name}: {e}")
            return 0
