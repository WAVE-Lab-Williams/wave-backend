#!/usr/bin/env bash
#
# db_backup.sh — self-hosted Postgres backup for the WAVE backend.
#
# Dumps a Postgres database to a local directory using `pg_dump -Fc` (custom,
# compressed format -> restore with `pg_restore`). The dump runs inside a pinned
# `postgres:<major>` container so the client version always matches the server
# (Railway runs PG 15-17; an older local pg_dump will refuse with a version
# mismatch). No Railway managed backups required.
#
# Usage:
#   # Option A — put settings in a gitignored env file (recommended):
#   #   cp scripts/.env.backup.example scripts/.env.backup  &&  edit it
#   ./scripts/db_backup.sh
#
#   # Option B — pass inline:
#   DATABASE_URL="postgresql://user:pass@host:port/db" \
#   BACKUP_DIR="/Volumes/your-drive/wave-backups" PG_MAJOR=16 ./scripts/db_backup.sh
#
# Env vars (from scripts/.env.backup if present, or the environment):
#   DATABASE_URL     (required) connection string to dump (e.g. prod from Railway).
#   BACKUP_DIR       (default ./backups) where .dump files are written.
#   PG_MAJOR         (default 16) Postgres major version — MATCH the server.
#   RETENTION_DAYS   (default 30) prune dumps older than this. 0 disables pruning.
#   CONTAINER_RUNTIME(default: podman if present, else docker)
#   ENV_FILE         (default scripts/.env.backup) gitignored file to source.
#
set -euo pipefail

# Load connection settings from a gitignored env file if present (keeps prod
# creds out of git and out of your shell history).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env.backup}"
if [ -f "$ENV_FILE" ]; then
  echo "==> Loading settings from $ENV_FILE"
  set -a; . "$ENV_FILE"; set +a
fi

: "${DATABASE_URL:?set DATABASE_URL (in scripts/.env.backup or the environment) to the connection string you want to back up}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
PG_MAJOR="${PG_MAJOR:-16}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-$(command -v podman >/dev/null 2>&1 && echo podman || echo docker)}"

mkdir -p "$BACKUP_DIR"
abs_backup_dir="$(cd "$BACKUP_DIR" && pwd)"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
filename="wave_prod_${ts}.dump"

echo "==> Backing up database via ${CONTAINER_RUNTIME} (postgres:${PG_MAJOR})"
echo "    -> ${abs_backup_dir}/${filename}"

"$CONTAINER_RUNTIME" run --rm \
  -e PGCONNECT_TIMEOUT=15 \
  -v "${abs_backup_dir}:/backups" \
  "postgres:${PG_MAJOR}" \
  pg_dump -Fc --no-owner --no-privileges "$DATABASE_URL" -f "/backups/${filename}"

# Sanity check: file exists and is non-trivial in size.
if [ ! -s "${abs_backup_dir}/${filename}" ]; then
  echo "!! Backup file is empty or missing — aborting." >&2
  exit 1
fi

echo "==> Backup complete: ${abs_backup_dir}/${filename} ($(du -h "${abs_backup_dir}/${filename}" | cut -f1))"

if [ "${RETENTION_DAYS}" -gt 0 ]; then
  echo "==> Pruning dumps older than ${RETENTION_DAYS} days"
  find "$abs_backup_dir" -name 'wave_prod_*.dump' -type f -mtime +"${RETENTION_DAYS}" -print -delete || true
fi

echo "==> Done. To rehearse a restore into a throwaway DB (NEVER prod):"
echo "    ./scripts/db_restore.sh ${abs_backup_dir}/${filename} postgresql://localhost:5432/wave_restore"
