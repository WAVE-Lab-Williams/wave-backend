"""API routes for tag operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.models.database import get_db
from wave_backend.schemas.schemas import TagCreate, TagResponse, TagUpdate
from wave_backend.services.tags import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=TagResponse)
async def create_tag(tag: TagCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tag."""
    # Check if tag with same name already exists
    existing_tag = await TagService.get_tag_by_name(db, tag.name)
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")

    try:
        db_tag = await TagService.create_tag(db, tag)
        return db_tag
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Get a tag by ID."""
    db_tag = await TagService.get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get tags with pagination."""
    tags = await TagService.get_tags(db, skip=skip, limit=limit)
    return tags


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: int, tag_update: TagUpdate, db: AsyncSession = Depends(get_db)):
    """Update a tag."""
    # If updating name, check for conflicts
    if tag_update.name:
        existing_tag = await TagService.get_tag_by_name(db, tag_update.name)
        if existing_tag and existing_tag.id != tag_id:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")

    db_tag = await TagService.update_tag(db, tag_id, tag_update)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a tag."""
    success = await TagService.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted successfully"}
