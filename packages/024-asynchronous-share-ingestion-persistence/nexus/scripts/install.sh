#!/usr/bin/env bash
set -euo pipefail

PKG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG_ROOT/../../.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$ROOT/packages/backups/024-asynchronous-share-ingestion-persistence-$STAMP"

mkdir -p \
  "$BACKUP/src/seymour_pool_engine/stratum" \
  "$BACKUP/src/seymour_pool_engine/database" \
  "$BACKUP/src/seymour_pool_engine/config" \
  "$BACKUP/tests"

cp "$ROOT/pyproject.toml" "$BACKUP/pyproject.toml"
cp "$ROOT/src/seymour_pool_engine/stratum/server.py" \
   "$BACKUP/src/seymour_pool_engine/stratum/server.py"
cp "$ROOT/src/seymour_pool_engine/database/connections.py" \
   "$BACKUP/src/seymour_pool_engine/database/connections.py"
cp "$ROOT/src/seymour_pool_engine/config/stratum.py" \
   "$BACKUP/src/seymour_pool_engine/config/stratum.py"
cp "$ROOT/tests/test_stratum_server.py" "$BACKUP/tests/test_stratum_server.py"

cp "$PKG_ROOT/payload/pyproject.toml" "$ROOT/pyproject.toml"
cp "$PKG_ROOT/payload/src/seymour_pool_engine/stratum/server.py" \
   "$ROOT/src/seymour_pool_engine/stratum/server.py"
cp "$PKG_ROOT/payload/src/seymour_pool_engine/database/connections.py" \
   "$ROOT/src/seymour_pool_engine/database/connections.py"
cp "$PKG_ROOT/payload/src/seymour_pool_engine/config/stratum.py" \
   "$ROOT/src/seymour_pool_engine/config/stratum.py"
cp "$PKG_ROOT/payload/tests/test_stratum_server.py" \
   "$ROOT/tests/test_stratum_server.py"

"$ROOT/.venv/bin/python" -m pip install 'psycopg-pool>=3.2,<4.0'

ENV_FILE="/etc/seymour-pool-engine/engine.env"
if [[ -f "$ENV_FILE" ]]; then
  for setting in \
    'SEYMOUR_STRATUM_PROCESSING_WORKERS=8' \
    'SEYMOUR_STRATUM_PROCESSING_QUEUE_LIMIT=2048' \
    'SEYMOUR_STRATUM_DATABASE_POOL_MIN_SIZE=2' \
    'SEYMOUR_STRATUM_DATABASE_POOL_MAX_SIZE=16' \
    'SEYMOUR_STRATUM_DATABASE_POOL_TIMEOUT_SECONDS=5'; do
    key="${setting%%=*}"
    if ! sudo grep -q "^${key}=" "$ENV_FILE"; then
      printf '%s\n' "$setting" | sudo tee -a "$ENV_FILE" >/dev/null
    fi
  done
fi

printf 'Install PASS\nBackup: %s\n' "$BACKUP"
