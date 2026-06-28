# Database Migrations (Alembic)

How schema changes are made and applied for the WAVE backend, plus a log of how each prod migration
was actually run. See also `docs/railway-operations.md` (Railway CLI / DB access).

## How migrations work here

- Migrations live in `alembic/versions/`. The chain is linear: `0001_baseline` → `0002...` → `0003...`.
- **Revision ids must be ≤ 32 chars** — Alembic's `alembic_version.version_num` column is
  `VARCHAR(32)`; a longer id fails when it tries to record the version.
- **Hand-write migrations; do not trust autogenerate.** Experiment *types* create their own dynamic
  data tables at runtime (`services/experiment_data.py`) that are not in the ORM metadata.
  `alembic/env.py` sets an `include_name` filter so Alembic only ever manages the three model tables
  (`tags`, `experiment_types`, `experiments`) — this keeps autogenerate/compare from emitting
  `DROP TABLE` for production data tables. A data migration may still touch those tables explicitly
  (see `0003`).
- `env.py` is async (asyncpg) and reads the DB URL from `db_config` (`DATABASE_URL`), so the same
  config as the app.
- Baseline adoption: prod predates Alembic (tables were created by `Base.metadata.create_all`), so
  it must be **stamped** at `0001_baseline` once before any `upgrade` — otherwise `upgrade` would try
  to re-create existing tables. `0001_baseline` is therefore stamp-only on prod and never run there.

## Adding a migration

```bash
# create an empty revision (then hand-edit upgrade/downgrade)
uv run alembic revision -m "short description"     # keep the resulting id <= 32 chars
# inspect / sanity-check the chain
uv run alembic history
uv run alembic heads
```

## Getting the prod connection URL (Railway CLI)

Laptop-side commands (backup, manual stamp/upgrade) connect over Railway's **public TCP proxy**, not
the private `*.railway.internal` URL. Fetch the public URL with the CLI:

```bash
railway login                 # one-time; opens a browser
railway link                  # pick: workspace -> WAVE Backend -> production -> service: Postgres
railway variables -s Postgres --kv | grep -i DATABASE_PUBLIC_URL
```

Copy that value into `scripts/.env.backup` as `DATABASE_PUBLIC_URL=...` (gitignored). The backup
scripts read it automatically. For alembic, load it into `DATABASE_URL`:

```bash
set -a; . scripts/.env.backup; set +a        # loads DATABASE_PUBLIC_URL (+ PG_MAJOR, BACKUP_DIR)
export DATABASE_URL="$DATABASE_PUBLIC_URL"    # alembic/env.py reads DATABASE_URL
```

Notes:
- ⚠️ `railway variables` prints **secret** values — don't paste its output anywhere.
- `railway run <cmd>` injects the **private** URL (`*.railway.internal`), which doesn't resolve from a
  laptop — so it can't be used for migrations from your machine. Use the public URL above.
- `railway connect Postgres` opens an interactive `psql` over the same proxy (handy for verification
  SQL); add `--ssh` if the public proxy isn't enabled.

## Running a migration SAFELY (the standard procedure)

> Golden rule: **back up prod, rehearse on an offline restore, then apply.** The full, checkbox
> version is in `wave/DEPLOY-RUNBOOK.md`.

1. **Back up prod** (laptop, public proxy URL — see `docs/railway-operations.md`):
   ```bash
   make db-backup                       # uses scripts/.env.backup (DATABASE_PUBLIC_URL, PG_MAJOR)
   cp backups/<dump> backups/<dump>.golden   # keep an untouched copy
   ```
2. **Rehearse on a version-matched throwaway** (never prod). Match the prod major version
   (`PG_MAJOR` / `SELECT version();`):
   ```bash
   docker run -d --name pg-rehearse -e POSTGRES_PASSWORD=x -p 5434:5432 postgres:17
   docker exec pg-rehearse createdb -U postgres wave_restore
   docker cp backups/<dump> pg-rehearse:/tmp/d.dump
   docker exec pg-rehearse pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d wave_restore /tmp/d.dump
   DATABASE_URL=postgresql://postgres:x@localhost:5434/wave_restore uv run alembic stamp 0001_baseline
   DATABASE_URL=postgresql://postgres:x@localhost:5434/wave_restore uv run alembic upgrade head
   # verify columns added + row counts unchanged + alembic downgrade/upgrade round-trips, then:
   docker rm -f pg-rehearse
   ```
   > Note: data-dependent migrations (like `0003`, which queries `experiment_types`) cannot be
   > dry-run via `alembic upgrade --sql` (offline has no DB connection) — the restore-rehearsal is
   > the real preview.
3. **Apply to prod** — either:
   - **Manual (supervised):** from the laptop via the public URL — `alembic stamp 0001_baseline`
     (first time only) then `alembic upgrade head`. Decouples the DB change from the code deploy.
   - **Automated:** merge to `main`; Railway's `preDeployCommand: alembic upgrade head` runs it
     inside the network (requires the one-time baseline stamp to have happened already).
4. **Verify** on prod: expected columns exist, row counts unchanged, `alembic current` at head.

## Run log

### 2026-06-28 — config feature (`0001_baseline`, `0002_add_experiment_config`, `0003_config_on_data_tables`)
Adopted Alembic + added the per-experiment `config` column and the per-run `experiment_config`
snapshot column. Run **manually/supervised** from a laptop over the Railway public proxy.

- **Prod server:** PostgreSQL 17.10. **`PG_MAJOR=17`.**
- **Backups:** `backups/wave_prod_20260628T173948Z.dump` (+ `.golden`) pre-migration;
  `backups/wave_prod_20260628T180707Z.dump` post-migration.
- **Rehearsal:** restored the pre-migration dump into a throwaway PG 17.10 (`wave_restore`), ran
  `stamp 0001_baseline` → `upgrade head`. Result: `config` added, `experiment_config` on 28/28
  existing data tables, 263,139 rows unchanged across 36 tables, `downgrade`→`upgrade` round-tripped.
  Also validated the live `/config` endpoints against that copy (experimentee GET 200 / PUT 403;
  researcher PUT+GET 200).
- **Commands run against prod** (env `DATABASE_URL` = the `DATABASE_PUBLIC_URL` from
  `scripts/.env.backup`):
  ```bash
  uv run alembic current            # empty (unstamped) — confirmed pre-flight
  uv run alembic stamp 0001_baseline
  uv run alembic upgrade head       # applied 0002 + 0003
  uv run alembic current            # 0003_config_on_data_tables
  ```
- **Result on prod:** `experiments.config` present; `experiment_config` on **28/28** existing data
  tables (4 orphan `experiment_types` rows — no backing table — skipped by the `to_regclass` guard);
  `alembic_version = 0003_config_on_data_tables`; **row-count drift: NONE** (263,139 rows intact).
- **Deploy interaction:** prod was migrated *before* the backend deploy, so the deploy's
  `preDeploy alembic upgrade head` is a no-op. Old code kept running fine throughout (new columns are
  nullable / ignored by the old ORM models).
- **Follow-up (non-blocking):** 4 orphan `experiment_types` rows are candidates for cleanup.
</content>
