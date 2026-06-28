#!/usr/bin/env bash
#
# db_restore.sh — restore a WAVE backend Postgres dump produced by db_backup.sh.
#
# Restores a `pg_dump -Fc` custom-format dump into an EXPLICIT target database
# using `pg_restore --clean --if-exists`. Runs inside a pinned postgres:<major>
# container so the client version matches.
#
# !! SAFETY: the target URL is a required positional arg with no default. This
#    script will gladly --clean (drop & recreate objects in) whatever you point
#    it at. Do NOT point it at production unless that is genuinely what you want.
#    Intended use: rehearse a migration on a throwaway restored copy.
#
# Usage:
#   ./scripts/db_restore.sh <dump-file> <target_database_url>
#
# Example (rehearsal target, not prod):
#   ./scripts/db_restore.sh ./backups/wave_prod_20260627T000000Z.dump \
#       postgresql://wave_user:wave_password@localhost:5432/wave_restore
#
# Env vars (from scripts/.env.backup if present, or the environment):
#   PG_MAJOR          (default 16) Postgres major version — match the dump's server.
#   CONTAINER_RUNTIME (default: podman if present, else docker)
#   ENV_FILE          (default scripts/.env.backup) gitignored file to source.
#
set -euo pipefail

# Load settings (e.g. PG_MAJOR) from the gitignored env file if present.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env.backup}"
if [ -f "$ENV_FILE" ]; then
  echo "==> Loading settings from $ENV_FILE"
  set -a; . "$ENV_FILE"; set +a
fi

DUMP="${1:?usage: db_restore.sh <dump-file> <target_database_url>}"
TARGET_URL="${2:?refusing to guess target DB; pass it explicitly (NOT prod unless intended)}"
PG_MAJOR="${PG_MAJOR:-16}"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-$(command -v podman >/dev/null 2>&1 && echo podman || echo docker)}"

if [ ! -s "$DUMP" ]; then
  echo "!! Dump file not found or empty: $DUMP" >&2
  exit 1
fi

dump_dir="$(cd "$(dirname "$DUMP")" && pwd)"
dump_file="$(basename "$DUMP")"

echo "==> Restoring '${dump_file}'"
echo "    into target: ${TARGET_URL}"
echo "    (this will --clean/--if-exists drop & recreate objects in the target)"
read -r -p "Type 'yes' to proceed: " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

"$CONTAINER_RUNTIME" run --rm \
  -e PGCONNECT_TIMEOUT=15 \
  -v "${dump_dir}:/in" \
  "postgres:${PG_MAJOR}" \
  pg_restore --clean --if-exists --no-owner --no-privileges \
  -d "$TARGET_URL" "/in/${dump_file}"

echo "==> Restore complete into ${TARGET_URL}"
