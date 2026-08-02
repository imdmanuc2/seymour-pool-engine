#!/usr/bin/env bash
set -euo pipefail
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PACKAGE_DIR/../../.." && pwd)"
PAYLOAD_DIR="$PACKAGE_DIR/payload"
BACKUP_MARKER="$PACKAGE_DIR/.last_backup_dir"
heading(){ printf '\n== %s ==\n' "$1"; }
pass(){ printf '%-47s PASS\n' "$1"; }
fail(){ printf '%-47s FAIL\n' "$1" >&2; exit 1; }
require_repo(){ [[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "Repository detected"; }
load_env(){
    local service_env="/etc/seymour-pool-engine/engine.env"
    local line=""
    local value=""

    # Load repository defaults first when available.
    if [[ -f "$REPO_ROOT/.env" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "$REPO_ROOT/.env"
        set +a
    fi

    # Do not source the systemd EnvironmentFile with Bash.
    # Read only the authoritative database URL.
    if [[ -r "$service_env" ]]; then
        line="$(
            grep -m1 '^SEYMOUR_ENGINE_DATABASE_URL='                 "$service_env" || true
        )"

        if [[ -n "$line" ]]; then
            value="${line#*=}"

            # Remove matching outer quotes when present.
            if [[ "$value" == \"*\" ]]; then
                value="${value:1:${#value}-2}"
            elif [[ "$value" == \'*\' ]]; then
                value="${value:1:${#value}-2}"
            fi

            export SEYMOUR_ENGINE_DATABASE_URL="$value"
        fi
    fi
}

python_bin(){ [[ -x "$REPO_ROOT/.venv/bin/python" ]] && printf '%s' "$REPO_ROOT/.venv/bin/python" || command -v python3; }
