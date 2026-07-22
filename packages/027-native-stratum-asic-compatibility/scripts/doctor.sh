#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

test -f "$ROOT/src/seymour_pool_engine/stratum/dispatcher.py"
test -f "$ROOT/src/seymour_pool_engine/engines/session/models.py"
test -f "$ROOT/tests/test_stratum_version_rolling.py"

grep -q \
  "SUPPORTED_VERSION_ROLLING_MASK = 0x1FFFE000" \
  "$ROOT/src/seymour_pool_engine/stratum/dispatcher.py"

grep -q \
  "version_rolling_mask" \
  "$ROOT/src/seymour_pool_engine/engines/session/models.py"

echo "Package 027 doctor PASS"
