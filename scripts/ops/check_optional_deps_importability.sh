#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "============================================================"
echo "Peak_Trade Optional Deps Importability Gate"
echo "============================================================"
echo "root: ${ROOT_DIR}"
echo

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python}"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "ERROR: python not found. Set PYTHON_BIN=... (e.g. python3.11)"
  exit 1
fi

TMP_BASE="${ROOT_DIR}/.tmp_optional_deps_gate"
VENV_CORE="${TMP_BASE}/venv_core"
VENV_KRAKEN="${TMP_BASE}/venv_kraken"

cleanup() {
  rm -rf "${TMP_BASE}" || true
}
trap cleanup EXIT

echo "==> Creating venvs under ${TMP_BASE}"
rm -rf "${TMP_BASE}"
mkdir -p "${TMP_BASE}"

cd "${ROOT_DIR}"

"${PYTHON_BIN}" -m venv "${VENV_CORE}"
"${PYTHON_BIN}" -m venv "${VENV_KRAKEN}"

PIP_CORE="${VENV_CORE}/bin/pip"
PY_CORE="${VENV_CORE}/bin/python"
PIP_KRAKEN="${VENV_KRAKEN}/bin/pip"
PY_KRAKEN="${VENV_KRAKEN}/bin/python"

echo
echo "============================================================"
echo "A) Core install (no extras): pip install -e ."
echo "============================================================"
"${PIP_CORE}" -q install -U pip setuptools wheel
"${PIP_CORE}" -q install -e .

echo
echo "-- Imports (core, no extras)"
"${PY_CORE}" -c "import src.data; import src.data.backend"
"${PY_CORE}" -c "import importlib; importlib.import_module('src.data.providers')"
echo "OK: core imports"

echo
echo "============================================================"
echo "B) Optional install ([kraken]): pip install -e .[kraken]"
echo "============================================================"
"${PIP_KRAKEN}" -q install -U pip setuptools wheel
"${PIP_KRAKEN}" -q install -e ".[kraken]"

echo
echo "-- Provider import smoke (no network)"
"${PY_KRAKEN}" -c "from src.data.providers.kraken_ccxt_backend import KrakenCcxtBackend; KrakenCcxtBackend()"
echo "OK: kraken provider import + init"

echo
echo "============================================================"
echo "PASS: Optional deps importability gate"
echo "============================================================"
