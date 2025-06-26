"""Service layer for tag operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.models.models import Tag
from wave_backend.schemas.schemas import TagCreate, TagUpdate


class TagService:
    """Service for tag CRUD operations."""

    @staticmethod
    async def create_tag(db: AsyncSession, tag: TagCreate) -> Tag:
        """Create a new tag."""
        db_tag = Tag(**tag.model_dump())
        db.add(db_tag)
        await db.commit()
        await db.refresh(db_tag)
        return db_tag

    @staticmethod
    async def get_tag(db: AsyncSession, tag_id: int) -> Optional[Tag]:
        """Get a tag by ID."""
        result = await db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
        """Get a tag by name."""
        result = await db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_tags(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Tag]:
        """Get tags with pagination."""
        result = await db.execute(select(Tag).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_tag(db: AsyncSession, tag_id: int, tag_update: TagUpdate) -> Optional[Tag]:
        """Update a tag."""
        db_tag = await TagService.get_tag(db, tag_id)
        if not db_tag:
            return None

        update_data = tag_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tag, field, value)

        await db.commit()
        await db.refresh(db_tag)
        return db_tag

    @staticmethod
    async def delete_tag(db: AsyncSession, tag_id: int) -> bool:
        """Delete a tag."""
        db_tag = await TagService.get_tag(db, tag_id)
        if not db_tag:
            return False

        await db.delete(db_tag)
        await db.commit()
        return True
