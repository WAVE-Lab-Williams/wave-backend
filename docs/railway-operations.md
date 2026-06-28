# Railway Operations (CLI)

How to use the [Railway CLI](https://docs.railway.com/cli) to operate the wave-backend service and
its Postgres database: backups, connecting, and running Alembic migrations. Pairs with the
deploy runbook for the `config` feature.

> Tested with Railway CLI **v5.23.1**. Put Railway flags *before* the `--` child command.

## Key networking fact (read first)
A Railway Postgres has two URLs:
- **Private** `postgres.railway.internal:5432` — only resolves **inside** Railway's network (this is
  what the app uses at runtime, and what runs inside `preDeployCommand`).
- **Public** TCP proxy (`DATABASE_PUBLIC_URL`, e.g. `*.proxy.rlwy.net:PORT`) — reachable from your
  laptop.

So: anything you run **from your laptop** (pg_dump, `alembic stamp`) must use the **public** URL.
`railway run` injects the **private** URL, so it does **not** work for laptop→DB connections. The
actual schema `upgrade` runs **inside Railway** (preDeploy), where the private URL works.

## One-time setup
```bash
railway login
railway link            # pick workspace → project → environment (production) → service (wave-backend)
railway status          # confirm the linked project / environment / service
```

## Get the public DB connection string
```bash
# Replace "Postgres" with your DB service name if different (see `railway status` / dashboard).
railway variables -s Postgres --kv | grep -i DATABASE_PUBLIC_URL
```
- If there's no `DATABASE_PUBLIC_URL`, enable a public TCP proxy on the Postgres service
  (dashboard → Postgres → Settings → Networking → "Public Networking", or `railway tcp-proxy`).
- Put that value into `scripts/.env.backup` as `DATABASE_URL=...` (gitignored), along with `PG_MAJOR`.

## Connect for ad-hoc / verification SQL
```bash
railway connect Postgres          # opens psql via the public proxy
railway connect Postgres --ssh    # fallback: psql over an SSH tunnel (works without a public proxy)
```
Useful checks:
```sql
SELECT count(*) FROM experiments;
SELECT table_name FROM experiment_types ORDER BY table_name;
SELECT version_num FROM alembic_version;
```

## Back up prod (Stage 0)
```bash
make db-backup          # uses scripts/.env.backup (public DATABASE_URL); writes a pg_dump -Fc file
```

## Alembic migrations
This repo adopts Alembic; prod has the tables but no `alembic_version` yet, so it must be **stamped**
once before any upgrade (an un-stamped `upgrade` would try to re-create existing tables and fail).

**Step 1 — one-time baseline stamp (from laptop, public URL, zero DDL):**
```bash
export DATABASE_URL="$(railway variables -s Postgres --kv | sed -n 's/^DATABASE_PUBLIC_URL=//p')"
uv run alembic current            # expect: empty
uv run alembic stamp 0001_baseline
uv run alembic current            # expect: 0001_baseline
unset DATABASE_URL                 # avoid accidentally targeting prod afterward
```

**Step 2 — apply the schema migrations:**
- **Automated (preferred):** merge the backend PR → Railway runs `alembic upgrade head` in the
  `preDeployCommand` (inside the network) before the new container takes traffic.
- **Manual fallback (from laptop):**
  ```bash
  DATABASE_URL="<DATABASE_PUBLIC_URL>" uv run alembic upgrade head
  ```

> Always rehearse on an **offline restore** of the prod dump first (see the deploy runbook). The
> data-dependent `0003` migration can't be dry-run via `alembic --sql`, so the restore-rehearsal is
> the real preview.

## Watch a deploy / the migration run
```bash
railway logs -d         # deploy logs (watch the preDeploy alembic output)
railway logs -b         # build logs
railway status          # current deployment status
```

## Handy extras
```bash
railway redeploy        # redeploy latest (e.g. to roll back to a previous image's behavior)
railway ssh             # shell into the running service container (private URL works in here)
railway variables -s wave-backend --kv   # inspect the app service's env
```
⚠️ `railway variables` / `railway run printenv` print secret values — don't paste their output anywhere.
</content>
