#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "============================================================"
echo "Peak_Trade Typecheck: pyright (dev-only)"
echo "============================================================"
echo

# Run via the active Python interpreter to avoid PATH ambiguities.
# (pyright provides both a CLI wrapper and a python module; the module approach is most stable here.)
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "ERROR: python not found. Activate a venv or set PYTHON_BIN=..."
  exit 1
fi

if ! "${PYTHON_BIN}" -c "import pyright" >/dev/null 2>&1; then
  echo "ERROR: pyright not installed in this Python environment."
  echo "Install via: pip install -e \".[dev]\""
  exit 1
fi

"${PYTHON_BIN}" -m pyright -p pyrightconfig.json

echo
echo "PASS: pyright typecheck"
