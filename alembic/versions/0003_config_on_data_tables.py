"""add experiment_config column to every experiment data table

Revision ID: 0003_config_on_data_tables
Revises: 0002_add_experiment_config
Create Date: 2026-06-27

The frontend logs a snapshot of each run's resolved hyperparameters as a data
field (`experiment_config`). That data lands in the per-experiment-type *dynamic*
data tables (one per experiment type, named by experiment_types.table_name).

This migration adds a nullable ``experiment_config TEXT`` column to every such
existing data table so the snapshot can be logged WITHOUT a manual per-type
schema change — and so an existing experiment never starts rejecting rows when it
picks up the updated template. (New experiment types created via the template
include the column in their schema from the start.)

Notes:
- We iterate ``experiment_types.table_name`` rather than guessing table names.
- ``ADD COLUMN IF NOT EXISTS`` makes this idempotent and safe to re-run.
- A nullable column with no default is a metadata-only change in Postgres (no
  table rewrite), so this is fast and safe even on large data tables.
- This is an explicit data migration; Alembic's ``include_name`` filter only
  affects autogenerate/compare, not the operations we run here by hand.
"""

# alembic.op members (get_bind, execute, ...) are injected at runtime, so static
# analysis can't see them.
# pylint: disable=no-member

from typing import Sequence, Union

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_config_on_data_tables"
down_revision: Union[str, None] = "0002_add_experiment_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMN_NAME = "experiment_config"


def _data_table_names(bind) -> list[str]:
    """Return the data-table name for every registered experiment type whose
    table actually exists.

    ``to_regclass(quote_ident(...))`` returns NULL when the (case-sensitive)
    table is absent, so an orphaned experiment_types row can't abort the whole
    migration.
    """
    rows = bind.execute(
        text(
            "SELECT table_name FROM experiment_types "
            "WHERE to_regclass(quote_ident(table_name)) IS NOT NULL"
        )
    ).fetchall()
    return [r[0] for r in rows]


def _quote_ident(name: str) -> str:
    """Safely quote a SQL identifier (double-quote, escaping embedded quotes)."""
    return '"' + name.replace('"', '""') + '"'


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in _data_table_names(bind):
        op.execute(
            f"ALTER TABLE {_quote_ident(table_name)} "
            f"ADD COLUMN IF NOT EXISTS {COLUMN_NAME} TEXT"
        )


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in _data_table_names(bind):
        op.execute(
            f"ALTER TABLE {_quote_ident(table_name)} " f"DROP COLUMN IF EXISTS {COLUMN_NAME}"
        )
