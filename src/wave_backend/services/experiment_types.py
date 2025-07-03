"""Service layer for experiment type operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.models.models import ExperimentType
from wave_backend.schemas.schemas import ExperimentTypeCreate, ExperimentTypeUpdate
from wave_backend.services.experiment_data import ExperimentDataService


class ExperimentTypeService:
    """Service for experiment type CRUD operations."""

    @staticmethod
    async def create_experiment_type(
        db: AsyncSession, experiment_type: ExperimentTypeCreate
    ) -> ExperimentType:
        """Create a new experiment type and its corresponding data table."""
        db_experiment_type = ExperimentType(**experiment_type.model_dump())
        db.add(db_experiment_type)
        await db.commit()
        await db.refresh(db_experiment_type)

        # Create the dynamic table for this experiment type
        table_created = await ExperimentDataService.create_experiment_table(
            db_experiment_type.table_name, db_experiment_type.schema_definition, db
        )

        if not table_created:
            # If table creation fails, rollback the experiment type creation
            await db.delete(db_experiment_type)
            await db.commit()
            raise RuntimeError(
                f"Failed to create experiment data table: {db_experiment_type.table_name}"
            )

        return db_experiment_type

    @staticmethod
    async def get_experiment_type(
        db: AsyncSession, experiment_type_id: int
    ) -> Optional[ExperimentType]:
        """Get an experiment type by ID."""
        result = await db.execute(
            select(ExperimentType).where(ExperimentType.id == experiment_type_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_experiment_type_by_name(db: AsyncSession, name: str) -> Optional[ExperimentType]:
        """Get an experiment type by name."""
        result = await db.execute(select(ExperimentType).where(ExperimentType.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_experiment_types(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ExperimentType]:
        """Get experiment types with pagination."""
        result = await db.execute(select(ExperimentType).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_experiment_type(
        db: AsyncSession, experiment_type_id: int, experiment_type_update: ExperimentTypeUpdate
    ) -> Optional[ExperimentType]:
        """Update an experiment type."""
        db_experiment_type = await ExperimentTypeService.get_experiment_type(db, experiment_type_id)
        if not db_experiment_type:
            return None

        update_data = experiment_type_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_experiment_type, field, value)

        await db.commit()
        await db.refresh(db_experiment_type)
        return db_experiment_type

    @staticmethod
    async def delete_experiment_type(db: AsyncSession, experiment_type_id: int) -> bool:
        """Delete an experiment type and its corresponding data table."""
        db_experiment_type = await ExperimentTypeService.get_experiment_type(db, experiment_type_id)
        if not db_experiment_type:
            return False

        # Drop the dynamic table first
        table_name = db_experiment_type.table_name
        await ExperimentDataService.drop_experiment_table(table_name, db)

        await db.delete(db_experiment_type)
        await db.commit()
        return True
