#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/ops/fetch_registry_pointer_artifacts.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer out/ops/gh_runs
#
# Requires: gh auth already configured.
POINTER="${1:?pointer file required}"
OUT_BASE="${2:-out/ops/gh_runs}"

# parse key=value lines
repo="$(rg -m1 '^repo=' "$POINTER" | cut -d= -f2- || true)"
workflow="$(rg -m1 '^workflow=' "$POINTER" | cut -d= -f2- || true)"
run_id="$(rg -m1 '^run_id=' "$POINTER" | cut -d= -f2- || true)"

if [[ -z "${run_id}" ]]; then
  echo "ERR: run_id missing in pointer: ${POINTER}" >&2
  exit 2
fi

mkdir -p "${OUT_BASE}/${run_id}"
echo "INFO: downloading run_id=${run_id} -> ${OUT_BASE}/${run_id}"

# NOTE: repo/workflow are informational; gh run download uses run_id globally within current repo context.
# If user is in a fork/other repo, they should 'gh repo set-default' accordingly.
gh run download "${run_id}" -D "${OUT_BASE}/${run_id}"
echo "OK: downloaded"
