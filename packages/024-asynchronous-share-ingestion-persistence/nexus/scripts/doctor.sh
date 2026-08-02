#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

required=(
  "$ROOT/pyproject.toml"
  "$ROOT/src/seymour_pool_engine/stratum/server.py"
  "$ROOT/src/seymour_pool_engine/database/connections.py"
  "$ROOT/src/seymour_pool_engine/config/stratum.py"
  "$ROOT/.venv/bin/python"
)

for path in "${required[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "Doctor FAIL: missing $path" >&2
    exit 1
  fi
done

"$ROOT/.venv/bin/python" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ is required")
print(f"Python {sys.version.split()[0]}")
PY

echo "Doctor PASS"
