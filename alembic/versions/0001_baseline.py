"""baseline: tags, experiment_types, experiments (pre-config schema)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-27

Represents the schema as it existed BEFORE the experiment ``config`` column.

On an existing production database (tables already created historically by
``Base.metadata.create_all``), DO NOT run this upgrade — instead record it as
already applied:

    alembic stamp 0001_baseline

then ``alembic upgrade head`` applies only the additive 0002 migration.

For a brand-new database that uses Alembic from scratch, this builds the base
tables. (Dev/test environments that rely on ``create_all`` never run Alembic.)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_id", "tags", ["id"])
    op.create_index("ix_tags_name", "tags", ["name"], unique=True)

    op.create_table(
        "experiment_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("table_name", sa.String(length=100), nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("table_name"),
    )
    op.create_index("ix_experiment_types_id", "experiment_types", ["id"])
    op.create_index("ix_experiment_types_name", "experiment_types", ["name"], unique=True)

    op.create_table(
        "experiments",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("experiment_type_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50)), nullable=True),
        sa.Column("additional_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["experiment_type_id"], ["experiment_types.id"]),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index("ix_experiments_uuid", "experiments", ["uuid"])


def downgrade() -> None:
    op.drop_index("ix_experiments_uuid", table_name="experiments")
    op.drop_table("experiments")
    op.drop_index("ix_experiment_types_name", table_name="experiment_types")
    op.drop_index("ix_experiment_types_id", table_name="experiment_types")
    op.drop_table("experiment_types")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_index("ix_tags_id", table_name="tags")
    op.drop_table("tags")
