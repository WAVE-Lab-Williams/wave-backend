"""Service layer for advanced search and filtering operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wave_backend.models.models import Experiment, ExperimentType, Tag
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for advanced search and filtering across all entities."""

    @staticmethod
    async def search_experiments_by_tags(
        db: AsyncSession,
        tags: List[str],
        match_all: bool = True,
        skip: int = 0,
        limit: int = 100,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Experiment]:
        """Search experiments by tags with date filtering."""
        query = select(Experiment).options(selectinload(Experiment.experiment_type))

        # Tag filtering
        if tags:
            if match_all:
                # Must contain ALL specified tags
                for tag in tags:
                    query = query.where(Experiment.tags.any(tag))
            else:
                # Must contain ANY of the specified tags
                tag_conditions = [Experiment.tags.any(tag) for tag in tags]
                query = query.where(or_(*tag_conditions))

        # Date range filtering
        if created_after:
            query = query.where(Experiment.created_at >= created_after)
        if created_before:
            query = query.where(Experiment.created_at <= created_before)

        query = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_experiment_types_by_description(
        db: AsyncSession,
        search_text: str,
        skip: int = 0,
        limit: int = 100,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[ExperimentType]:
        """Search experiment types by description text."""
        query = select(ExperimentType)

        # Text search (case-insensitive)
        if search_text:
            search_pattern = f"%{search_text.lower()}%"
            query = query.where(
                or_(
                    func.lower(ExperimentType.description).like(search_pattern),
                    func.lower(ExperimentType.name).like(search_pattern),
                )
            )

        # Date range filtering
        if created_after:
            query = query.where(ExperimentType.created_at >= created_after)
        if created_before:
            query = query.where(ExperimentType.created_at <= created_before)

        query = query.order_by(ExperimentType.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_tags_by_name(
        db: AsyncSession,
        search_text: str,
        skip: int = 0,
        limit: int = 100,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Tag]:
        """Search tags by name or description."""
        query = select(Tag)

        # Text search (case-insensitive)
        if search_text:
            search_pattern = f"%{search_text.lower()}%"
            query = query.where(
                or_(
                    func.lower(Tag.name).like(search_pattern),
                    func.lower(Tag.description).like(search_pattern),
                )
            )

        # Date range filtering
        if created_after:
            query = query.where(Tag.created_at >= created_after)
        if created_before:
            query = query.where(Tag.created_at <= created_before)

        query = query.order_by(Tag.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_experiments_by_description_and_type(
        db: AsyncSession,
        experiment_type_id: int,
        search_text: str,
        skip: int = 0,
        limit: int = 100,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Experiment]:
        """Search experiment descriptions within a specific experiment type."""
        query = select(Experiment).options(selectinload(Experiment.experiment_type))

        # Filter by experiment type
        query = query.where(Experiment.experiment_type_id == experiment_type_id)

        # Text search in description
        if search_text:
            search_pattern = f"%{search_text.lower()}%"
            query = query.where(func.lower(Experiment.description).like(search_pattern))

        # Date range filtering
        if created_after:
            query = query.where(Experiment.created_at >= created_after)
        if created_before:
            query = query.where(Experiment.created_at <= created_before)

        query = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def advanced_experiment_search(
        db: AsyncSession,
        search_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        match_all_tags: bool = True,
        experiment_type_id: Optional[int] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Experiment]:
        """Advanced search combining multiple criteria."""
        query = select(Experiment).options(selectinload(Experiment.experiment_type))

        conditions = []

        # Text search in description
        if search_text:
            search_pattern = f"%{search_text.lower()}%"
            conditions.append(func.lower(Experiment.description).like(search_pattern))

        # Experiment type filtering
        if experiment_type_id:
            conditions.append(Experiment.experiment_type_id == experiment_type_id)

        # Tag filtering
        if tags:
            if match_all_tags:
                # Must contain ALL specified tags
                for tag in tags:
                    conditions.append(Experiment.tags.any(tag))
            else:
                # Must contain ANY of the specified tags
                tag_conditions = [Experiment.tags.any(tag) for tag in tags]
                conditions.append(or_(*tag_conditions))

        # Date range filtering
        if created_after:
            conditions.append(Experiment.created_at >= created_after)
        if created_before:
            conditions.append(Experiment.created_at <= created_before)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_experiment_data_by_tags(
        db: AsyncSession,
        tags: List[str],
        match_all: bool = True,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get all experiment data for experiments matching specific tags."""
        from wave_backend.services.experiment_data import ExperimentDataService

        # First get experiments matching the tags
        experiments = await SearchService.search_experiments_by_tags(
            db,
            tags,
            match_all,
            0,
            1000,
            created_after,
            created_before,  # Get all matching experiments
        )

        # Collect data from all matching experiments
        all_data = []
        experiment_info = {}

        for experiment in experiments:
            # Get data for this experiment
            experiment_data = await ExperimentDataService.get_data_rows(
                experiment.experiment_type.table_name,
                db,
                experiment_uuid=str(experiment.uuid),
                created_after=created_after,
                created_before=created_before,
                limit=1000,  # Get all data for each experiment
                offset=0,
            )

            # Add experiment metadata to each data row
            for row in experiment_data:
                row["experiment_metadata"] = {
                    "experiment_uuid": str(experiment.uuid),
                    "experiment_description": experiment.description,
                    "experiment_type_name": experiment.experiment_type.name,
                    "experiment_tags": experiment.tags,
                }
                all_data.append(row)

            experiment_info[str(experiment.uuid)] = {
                "description": experiment.description,
                "type_name": experiment.experiment_type.name,
                "tags": experiment.tags,
                "data_count": len(experiment_data),
            }

        # Apply pagination to the combined results
        paginated_data = all_data[skip : skip + limit]  # noqa: E203

        return {
            "data": paginated_data,
            "total_rows": len(all_data),
            "total_experiments": len(experiments),
            "experiment_info": experiment_info,
            "pagination": {"skip": skip, "limit": limit, "total": len(all_data)},
        }
