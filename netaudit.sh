#!/usr/bin/env bash
# Convenience wrapper: creates a venv on first run, installs deps, and
# runs NetAudit with any arguments passed to this script.
#
#   ./netaudit.sh scan 192.168.1.0/24
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -d "$VENV_DIR" ]; then
    echo "First run: creating virtual environment..." >&2
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip >/dev/null
    pip install -e . >/dev/null
else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
fi

exec python -m netaudit "$@"
