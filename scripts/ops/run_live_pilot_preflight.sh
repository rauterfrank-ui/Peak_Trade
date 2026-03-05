#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}"

TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/live_pilot_preflight_${TS_UTC}"
mkdir -p "${OUT}"

echo "GIT_HEAD=$(git rev-parse HEAD)" | tee "${OUT}/preflight.env"
echo "TS_UTC=${TS_UTC}" | tee -a "${OUT}/preflight.env"

./scripts/ops/pull_latest_prbi_scorecard.sh | tee "${OUT}/pull_prbi.log"
./scripts/ops/pull_latest_prbg_execution_evidence.sh | tee "${OUT}/pull_prbg.log"

set +e
./scripts/ops/ops_status.sh
OPS_EXIT=$?
set -e
echo "OPS_STATUS_EXIT=${OPS_EXIT}" | tee -a "${OUT}/preflight.env"

if [ "${OPS_EXIT}" -ne 0 ]; then
  echo "NO_GO: ops_status exit=${OPS_EXIT}" | tee "${OUT}/verdict.txt"
  exit 2
fi

echo "GO_PRECHECK: ops_status OK" | tee "${OUT}/verdict.txt"
echo "NOTE: This script performs NO_TRADE actions only." | tee -a "${OUT}/verdict.txt"
