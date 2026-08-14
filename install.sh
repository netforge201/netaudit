#!/usr/bin/env bash
# Install NetAudit into a virtual environment (recommended) or system-wide.
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Error: $PYTHON_BIN not found. Install Python 3.11+ first." >&2
    exit 1
fi

PY_VERSION=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
echo "Using Python $PY_VERSION ($PYTHON_BIN)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v pipx >/dev/null 2>&1; then
    echo "pipx detected - installing NetAudit with pipx..."
    pipx install --force .
    echo "Done. Run: netaudit --help"
    exit 0
fi

echo "pipx not found - creating a local virtual environment (.venv) instead."
"$PYTHON_BIN" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install .

echo ""
echo "Installed into .venv/"
echo "Activate it with:  source .venv/bin/activate"
echo "Then run:           netaudit --help"
echo "Or use the wrapper: ./netaudit.sh --help"
