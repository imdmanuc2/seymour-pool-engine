#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$PACKAGE_ROOT/../.." && pwd)"

install -D -m 0644 \
  "$PACKAGE_ROOT/payload/src/seymour_pool_engine/stratum/dispatcher.py" \
  "$PROJECT_ROOT/src/seymour_pool_engine/stratum/dispatcher.py"

install -D -m 0644 \
  "$PACKAGE_ROOT/payload/src/seymour_pool_engine/engines/session/models.py" \
  "$PROJECT_ROOT/src/seymour_pool_engine/engines/session/models.py"

install -D -m 0644 \
  "$PACKAGE_ROOT/payload/tests/test_stratum_version_rolling.py" \
  "$PROJECT_ROOT/tests/test_stratum_version_rolling.py"

echo "Package 027 install PASS"
