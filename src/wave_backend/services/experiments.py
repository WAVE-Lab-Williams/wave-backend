"""Service layer for experiment operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wave_backend.models.models import Experiment, Tag
from wave_backend.schemas.schemas import (
    ColumnTypeInfo,
    ExperimentColumnsResponse,
    ExperimentCreate,
    ExperimentUpdate,
)


class ExperimentService:
    """Service for experiment CRUD operations."""

    @staticmethod
    async def create_experiment(db: AsyncSession, experiment: ExperimentCreate) -> Experiment:
        """Create a new experiment."""
        # Validate that all tags exist
        if experiment.tags:
            for tag_name in experiment.tags:
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                if not result.scalar_one_or_none():
                    raise ValueError(
                        f"Tag '{tag_name}' does not exist. Please create the tag first."
                    )

        db_experiment = Experiment(**experiment.model_dump())
        db.add(db_experiment)
        await db.commit()
        await db.refresh(db_experiment)

        # Load the experiment_type relationship to avoid lazy loading issues during serialization
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.experiment_type))
            .where(Experiment.uuid == db_experiment.uuid)
        )
        return result.scalar_one()

    @staticmethod
    async def get_experiment(db: AsyncSession, experiment_uuid: UUID) -> Optional[Experiment]:
        """Get an experiment by UUID."""
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.experiment_type))
            .where(Experiment.uuid == experiment_uuid)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_experiments(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        experiment_type_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Experiment]:
        """Get experiments with optional filtering."""
        query = select(Experiment).options(selectinload(Experiment.experiment_type))

        if experiment_type_id:
            query = query.where(Experiment.experiment_type_id == experiment_type_id)

        if tags:
            for tag in tags:
                query = query.where(Experiment.tags.any(tag))

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_experiment(
        db: AsyncSession, experiment_uuid: UUID, experiment_update: ExperimentUpdate
    ) -> Optional[Experiment]:
        """Update an experiment."""
        db_experiment = await ExperimentService.get_experiment(db, experiment_uuid)
        if not db_experiment:
            return None

        # Validate that all tags exist if tags are being updated
        update_data = experiment_update.model_dump(exclude_unset=True)
        if "tags" in update_data and update_data["tags"]:
            for tag_name in update_data["tags"]:
                result = await db.execute(select(Tag).where(Tag.name == tag_name))
                if not result.scalar_one_or_none():
                    raise ValueError(
                        f"Tag '{tag_name}' does not exist. Please create the tag first."
                    )

        for field, value in update_data.items():
            setattr(db_experiment, field, value)

        await db.commit()
        await db.refresh(db_experiment)

        # Load the experiment_type relationship to avoid lazy loading issues during serialization
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.experiment_type))
            .where(Experiment.uuid == db_experiment.uuid)
        )
        return result.scalar_one()

    @staticmethod
    async def delete_experiment(db: AsyncSession, experiment_uuid: UUID) -> bool:
        """Delete an experiment."""
        db_experiment = await ExperimentService.get_experiment(db, experiment_uuid)
        if not db_experiment:
            return False

        await db.delete(db_experiment)
        await db.commit()
        return True

    @staticmethod
    async def get_experiment_columns(
        db: AsyncSession,
        experiment_uuid: Optional[UUID] = None,
        experiment_type_name: Optional[str] = None,
    ) -> Optional[ExperimentColumnsResponse]:
        """Get column information for an experiment or experiment type."""

        if experiment_uuid:
            experiment = await ExperimentService.get_experiment(db, experiment_uuid)
            if not experiment:
                return None
            experiment_type_name = experiment.experiment_type.name

        if not experiment_type_name:
            return None

        # Get the table schema from the database
        base_columns = []
        try:

            def get_columns_sync(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_columns("experiments")

            columns_info = await db.run_sync(get_columns_sync)
            for col in columns_info:
                base_columns.append(
                    ColumnTypeInfo(
                        column_name=col["name"],
                        column_type=str(col["type"]),
                        is_nullable=col["nullable"],
                        default_value=col["default"],
                    )
                )
        except Exception:
            # Fallback to known base columns
            base_columns = [
                ColumnTypeInfo(column_name="uuid", column_type="UUID", is_nullable=False),
                ColumnTypeInfo(
                    column_name="experiment_type_id", column_type="INTEGER", is_nullable=False
                ),
                ColumnTypeInfo(
                    column_name="participant_id", column_type="VARCHAR(100)", is_nullable=False
                ),
                ColumnTypeInfo(column_name="description", column_type="TEXT", is_nullable=False),
                ColumnTypeInfo(column_name="tags", column_type="VARCHAR[]", is_nullable=True),
                ColumnTypeInfo(column_name="additional_data", column_type="JSON", is_nullable=True),
                ColumnTypeInfo(
                    column_name="created_at",
                    column_type="TIMESTAMP WITH TIME ZONE",
                    is_nullable=True,
                ),
                ColumnTypeInfo(
                    column_name="updated_at",
                    column_type="TIMESTAMP WITH TIME ZONE",
                    is_nullable=True,
                ),
            ]

        return ExperimentColumnsResponse(
            experiment_uuid=experiment_uuid,
            experiment_type=experiment_type_name,
            columns=base_columns,
        )
