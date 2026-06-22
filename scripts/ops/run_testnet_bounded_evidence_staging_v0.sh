#!/usr/bin/env bash
# Bounded Testnet evidence staging v0 — writes wrapper_evidence only (no network, no orchestrator).
set -euo pipefail

usage() {
  echo "Usage: $0 --staging-root PATH [--run-id ID] [--duration-minutes N] [--max-steps N]" >&2
  exit 2
}

fail_closed() {
  echo "$1" >&2
  exit 1
}

STAGING_ROOT=""
RUN_ID=""
DURATION_MINUTES=10
MAX_STEPS=120
MAX_DURATION_MINUTES=10

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

if ! [[ "${DURATION_MINUTES}" =~ ^[0-9]+$ ]] \
  || [[ "${DURATION_MINUTES}" -lt 1 ]] \
  || [[ "${DURATION_MINUTES}" -gt "${MAX_DURATION_MINUTES}" ]]; then
  fail_closed "invalid --duration-minutes: must be 1..${MAX_DURATION_MINUTES}"
fi

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID="testnet_bounded_observation_$(date -u +%Y%m%dT%H%M%SZ)"
fi

EVIDENCE_ROOT="${STAGING_ROOT}/wrapper_evidence"
LOGS_DIR="${STAGING_ROOT}/logs"
mkdir -p "${EVIDENCE_ROOT}" "${LOGS_DIR}"

read -r UTC_STARTED START_MONOTONIC_SECONDS < <(
  python3 - <<'PY'
import sys
import time
from datetime import datetime, timezone

utc_started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
start_monotonic_seconds = time.monotonic()
if not isinstance(start_monotonic_seconds, (int, float)) or start_monotonic_seconds != start_monotonic_seconds:
    print("unable to capture monotonic session start", file=sys.stderr)
    sys.exit(1)
print(utc_started, start_monotonic_seconds)
PY
)

cat > "${EVIDENCE_ROOT}/TESTNET_BOUNDED_OBSERVATION.md" <<EOF
# Testnet Bounded Observation (staging-only)

RUN_ID=${RUN_ID}
GENERATED_UTC=${UTC_STARTED}

TESTNET_SANDBOX_ONLY
NO_PRODUCTION_FALLBACK
NO_LIVE_ORDER_SUBMISSION

Proof contract reference: docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md

Non-authorizing bounded staging evidence. Does not authorize Testnet execution or Live.
EOF

MANIFEST_PATH="${EVIDENCE_ROOT}/manifest.json"
if ! UTC_STARTED="${UTC_STARTED}" \
  START_MONOTONIC_SECONDS="${START_MONOTONIC_SECONDS}" \
  RUN_ID="${RUN_ID}" \
  DURATION_MINUTES="${DURATION_MINUTES}" \
  MANIFEST_PATH="${MANIFEST_PATH}" \
  python3 - <<'PY'
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

manifest_path = Path(os.environ["MANIFEST_PATH"])
run_id = os.environ["RUN_ID"]
duration_minutes = int(os.environ["DURATION_MINUTES"])
utc_started = os.environ["UTC_STARTED"]
start_monotonic_seconds = float(os.environ["START_MONOTONIC_SECONDS"])

override_names = (
    "PEAK_TRADE_BOUNDED_TESTNET_STAGING_UTC_STARTED",
    "PEAK_TRADE_BOUNDED_TESTNET_STAGING_UTC_COMPLETED",
    "PEAK_TRADE_BOUNDED_TESTNET_STAGING_START_MONOTONIC_SECONDS",
    "PEAK_TRADE_BOUNDED_TESTNET_STAGING_END_MONOTONIC_SECONDS",
)
override_values = [os.environ.get(name, "").strip() for name in override_names]
if any(override_values) and not all(override_values):
    print("partial wallclock override forbidden", file=sys.stderr)
    sys.exit(1)

if all(override_values):
    utc_started = override_values[0]
    utc_completed = override_values[1]
    start_monotonic_seconds = float(override_values[2])
    end_monotonic_seconds = float(override_values[3])
else:
    utc_completed = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_monotonic_seconds = time.monotonic()

if not utc_started or not utc_completed:
    print("missing utc_started or utc_completed", file=sys.stderr)
    sys.exit(1)

if not math.isfinite(start_monotonic_seconds) or not math.isfinite(end_monotonic_seconds):
    print("monotonic session bounds must be finite", file=sys.stderr)
    sys.exit(1)

if end_monotonic_seconds < start_monotonic_seconds:
    print("end_monotonic_seconds must be >= start_monotonic_seconds", file=sys.stderr)
    sys.exit(1)

payload = {
    "schema": "testnet_bounded_dry_run.v0",
    "run_id": run_id,
    "generated_utc": utc_completed,
    "TESTNET_SANDBOX_ONLY": True,
    "NO_PRODUCTION_FALLBACK": True,
    "NO_LIVE_ORDER_SUBMISSION": True,
    "broker_connected": False,
    "production_fallback": False,
    "dry_run_only": True,
    "proof_contract_doc": "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md",
    "duration_minutes_requested": duration_minutes,
    "utc_started": utc_started,
    "utc_completed": utc_completed,
    "start_monotonic_seconds": start_monotonic_seconds,
    "end_monotonic_seconds": end_monotonic_seconds,
    "step_interval_seconds": 0.0,
}
tmp_path = manifest_path.with_suffix(".json.tmp")
try:
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, manifest_path)
except OSError as exc:
    print(f"manifest write failed: {exc}", file=sys.stderr)
    if tmp_path.exists():
        tmp_path.unlink(missing_ok=True)
    sys.exit(1)
PY
then
  fail_closed "manifest emission failed"
fi

printf '{"step":1,"mode":"staging_only","run_id":"%s"}\n' "${RUN_ID}" > "${EVIDENCE_ROOT}/steps.jsonl"

{
  echo "testnet bounded evidence staging stdout run_id=${RUN_ID}"
} > "${LOGS_DIR}/wrapper_stdout.log"
{
  echo "testnet bounded evidence staging stderr run_id=${RUN_ID}"
} > "${LOGS_DIR}/wrapper_stderr.log"

exit 0
