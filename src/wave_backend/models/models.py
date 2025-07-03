"""Database models for the WAVE backend."""

from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from wave_backend.models.database import Base


class Tag(Base):
    """Model for experiment tags."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExperimentType(Base):
    """Model for experiment types."""

    __tablename__ = "experiment_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    table_name = Column(String(100), unique=True, nullable=False)
    schema_definition = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to experiments
    experiments = relationship("Experiment", back_populates="experiment_type")


class Experiment(Base):
    """Base model for experiments."""

    __tablename__ = "experiments"

    uuid = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    experiment_type_id = Column(Integer, ForeignKey("experiment_types.id"), nullable=False)
    participant_id = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    tags = Column(ARRAY(String(50)), nullable=True, default=list)
    additional_data = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to experiment type
    experiment_type = relationship("ExperimentType", back_populates="experiments")
