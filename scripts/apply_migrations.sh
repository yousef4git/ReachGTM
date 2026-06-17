#!/usr/bin/env bash
#
# Apply the database schema to the Postgres instance pointed to by DATABASE_URL.
#
# init.sql creates the uuid-ossp + vector (pgvector) extensions, all tenant
# tables, RLS policies, and the HNSW index on document_chunks. On Railway the
# Postgres plugin does NOT auto-run init scripts (there is no
# docker-entrypoint-initdb.d), so run this once after creating the database:
#
#   DATABASE_URL="postgresql://..." ./scripts/apply_migrations.sh
#
# Requires: psql on PATH, and a Postgres image that ships the `vector`
# extension (use Railway's pgvector Postgres template — the default image may
# not include it, in which case `CREATE EXTENSION vector` will fail).
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set (e.g. Railway Postgres connection string)}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SQL="$SCRIPT_DIR/../backend/app/db/migrations/init.sql"

if [[ ! -f "$INIT_SQL" ]]; then
  echo "error: migration file not found at $INIT_SQL" >&2
  exit 1
fi

echo "Applying $INIT_SQL ..."
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$INIT_SQL"
echo "Migrations applied successfully."
