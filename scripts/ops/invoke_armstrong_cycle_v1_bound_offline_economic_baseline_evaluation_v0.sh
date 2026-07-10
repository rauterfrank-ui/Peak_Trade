#!/usr/bin/env bash
# Canonical operator entry for armstrong_cycle/v1 bound offline baseline evaluation.
# Resolves repo-local .venv/bin/python; does not rely on a global `python` on PATH.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INTERPRETER="${REPO_ROOT}/.venv/bin/python"
INVOKE_SCRIPT="${SCRIPT_DIR}/invoke_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0.py"

if [[ ! -f "${INTERPRETER}" ]]; then
  printf 'REASON_CODE=REPO_VENV_PYTHON_MISSING\nRUNNER_NOT_STARTED=RUNNER_NOT_STARTED\n' >&2
  exit 127
fi
if [[ ! -x "${INTERPRETER}" ]]; then
  printf 'REASON_CODE=REPO_VENV_PYTHON_NOT_EXECUTABLE\nRUNNER_NOT_STARTED=RUNNER_NOT_STARTED\n' >&2
  exit 127
fi

exec "${INTERPRETER}" "${INVOKE_SCRIPT}" "$@"
