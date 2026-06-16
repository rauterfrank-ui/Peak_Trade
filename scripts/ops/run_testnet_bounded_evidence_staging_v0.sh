#!/usr/bin/env bash
# Bounded Testnet evidence staging v0 — writes wrapper_evidence only (no network, no orchestrator).
set -euo pipefail

usage() {
  echo "Usage: $0 --staging-root PATH [--run-id ID] [--duration-minutes N] [--max-steps N]" >&2
  exit 2
}

STAGING_ROOT=""
RUN_ID=""
DURATION_MINUTES=10
MAX_STEPS=120

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging-root)
      STAGING_ROOT="${2:-}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:-}"
      shift 2
      ;;
    --duration-minutes)
      DURATION_MINUTES="${2:-10}"
      shift 2
      ;;
    --max-steps)
      MAX_STEPS="${2:-120}"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "${STAGING_ROOT}" ]]; then
  echo "missing --staging-root" >&2
  usage
fi

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID="testnet_bounded_observation_$(date -u +%Y%m%dT%H%M%SZ)"
fi

EVIDENCE_ROOT="${STAGING_ROOT}/wrapper_evidence"
LOGS_DIR="${STAGING_ROOT}/logs"
mkdir -p "${EVIDENCE_ROOT}" "${LOGS_DIR}"

UTC_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "${EVIDENCE_ROOT}/TESTNET_BOUNDED_OBSERVATION.md" <<EOF
# Testnet Bounded Observation (staging-only)

RUN_ID=${RUN_ID}
GENERATED_UTC=${UTC_NOW}

TESTNET_SANDBOX_ONLY
NO_PRODUCTION_FALLBACK
NO_LIVE_ORDER_SUBMISSION

Proof contract reference: docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md

Non-authorizing bounded staging evidence. Does not authorize Testnet execution or Live.
EOF

cat > "${EVIDENCE_ROOT}/manifest.json" <<EOF
{
  "schema": "testnet_bounded_dry_run.v0",
  "run_id": "${RUN_ID}",
  "generated_utc": "${UTC_NOW}",
  "TESTNET_SANDBOX_ONLY": true,
  "NO_PRODUCTION_FALLBACK": true,
  "NO_LIVE_ORDER_SUBMISSION": true,
  "broker_connected": false,
  "production_fallback": false,
  "dry_run_only": true,
  "proof_contract_doc": "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"
}
EOF

printf '{"step":1,"mode":"staging_only","run_id":"%s"}\n' "${RUN_ID}" > "${EVIDENCE_ROOT}/steps.jsonl"

{
  echo "testnet bounded evidence staging stdout run_id=${RUN_ID}"
} > "${LOGS_DIR}/wrapper_stdout.log"
{
  echo "testnet bounded evidence staging stderr run_id=${RUN_ID}"
} > "${LOGS_DIR}/wrapper_stderr.log"

exit 0
