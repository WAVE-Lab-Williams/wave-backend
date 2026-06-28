"""Alembic migration environment (async).

Uses the application's async engine/URL (asyncpg) so we don't need a separate
sync driver. The DB URL comes from ``db_config`` (env vars: DATABASE_URL or the
POSTGRES_* components), matching the running app.

IMPORTANT — dynamic tables: experiment *types* create their own data tables at
runtime (see services/experiment_data.py). Those are NOT in Base.metadata. The
``include_name`` filter below restricts Alembic to the managed model tables so
neither autogenerate nor comparisons can ever DROP a production data table.
"""

# alembic.context members (config, configure, run_migrations, ...) are injected
# at runtime by Alembic, so static analysis can't see them.
# pylint: disable=no-member

import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import models so every managed table is registered on Base.metadata.
from wave_backend.models import models  # noqa: F401
from wave_backend.models.database import Base
from wave_backend.models.database_config import db_config

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Only these tables are owned by the ORM models / managed by Alembic.
MANAGED_TABLES = {"tags", "experiment_types", "experiments"}


def include_name(name, type_, parent_names):
    """Keep Alembic away from runtime-created dynamic experiment data tables."""
    if type_ == "table":
        # name is None for the default schema sweep; allow it through.
        return name is None or name in MANAGED_TABLES
    return True


def _configure(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_name=include_name,
        include_schemas=False,
        compare_type=True,
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DB connection)."""
    context.configure(
        url=db_config.get_database_url(),
        target_metadata=target_metadata,
        include_name=include_name,
        include_schemas=False,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection):
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    connectable = create_async_engine(db_config.get_database_url(), poolclass=None)
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
