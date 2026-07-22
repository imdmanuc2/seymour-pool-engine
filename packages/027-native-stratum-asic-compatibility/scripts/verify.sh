#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

source .venv/bin/activate

ruff check \
  src \
  tests/test_stratum_version_rolling.py

pytest -q tests/test_stratum_version_rolling.py
pytest -q

echo "Package 027 verification PASS"
