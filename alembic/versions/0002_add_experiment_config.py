"""add nullable config column to experiments

Revision ID: 0002_add_experiment_config
Revises: 0001_baseline
Create Date: 2026-06-27

Adds the optional, free-form ``config`` JSON column used to store per-experiment
hyperparameters pulled by the frontend at runtime.

This is the ONLY migration run against production. Adding a nullable column with
no default is a metadata-only change in Postgres (no table rewrite, near-instant,
brief lock) and is fully backwards compatible: existing rows get NULL, which the
API serializes as ``{}``.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_experiment_config"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("experiments", sa.Column("config", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("experiments", "config")
