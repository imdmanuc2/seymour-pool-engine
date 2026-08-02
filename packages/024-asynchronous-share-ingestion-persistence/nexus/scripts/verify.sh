#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

"$ROOT/.venv/bin/python" -m py_compile \
  src/seymour_pool_engine/stratum/server.py \
  src/seymour_pool_engine/database/connections.py \
  src/seymour_pool_engine/config/stratum.py

"$ROOT/.venv/bin/python" - <<'PY'
from psycopg_pool import ConnectionPool
from seymour_pool_engine.config.stratum import StratumSettings

settings = StratumSettings()
assert settings.processing_workers >= 1
assert settings.processing_queue_limit >= 16
assert settings.database_pool_max_size >= settings.database_pool_min_size
print("Configuration PASS")
PY

"$ROOT/.venv/bin/python" -m pytest -q \
  tests/test_stratum_dispatcher.py \
  tests/test_stratum_server.py

if command -v systemctl >/dev/null 2>&1 && \
   systemctl list-unit-files seymour-pool-engine-stratum.service >/dev/null 2>&1; then
  sudo systemctl restart seymour-pool-engine-stratum.service
  sleep 2
  sudo systemctl is-active --quiet seymour-pool-engine-stratum.service
  sudo systemctl status seymour-pool-engine-stratum.service --no-pager | head -20
fi

echo "Verify PASS"
