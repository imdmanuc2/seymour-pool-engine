#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
BACKUP="${1:-$(find "$ROOT/packages/backups" -maxdepth 1 -type d -name '024-asynchronous-share-ingestion-persistence-*' | sort | tail -1)}"

if [[ -z "$BACKUP" || ! -d "$BACKUP" ]]; then
  echo "Rollback FAIL: backup not found" >&2
  exit 1
fi

cp "$BACKUP/pyproject.toml" "$ROOT/pyproject.toml"
cp "$BACKUP/src/seymour_pool_engine/stratum/server.py" \
   "$ROOT/src/seymour_pool_engine/stratum/server.py"
cp "$BACKUP/src/seymour_pool_engine/database/connections.py" \
   "$ROOT/src/seymour_pool_engine/database/connections.py"
cp "$BACKUP/src/seymour_pool_engine/config/stratum.py" \
   "$ROOT/src/seymour_pool_engine/config/stratum.py"
cp "$BACKUP/tests/test_stratum_server.py" "$ROOT/tests/test_stratum_server.py"

sudo systemctl restart seymour-pool-engine-stratum.service
printf 'Rollback PASS\nRestored: %s\n' "$BACKUP"
