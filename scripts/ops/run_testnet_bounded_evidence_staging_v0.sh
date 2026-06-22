#!/usr/bin/env bash
# Bounded Testnet evidence staging v0 — writes wrapper_evidence only (no network, no orchestrator).
set -euo pipefail

usage() {
  echo "Usage: $0 --staging-root PATH [--run-id ID] [--duration-minutes N] [--max-steps N] [--step-interval-seconds S]" >&2
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
STEP_INTERVAL_SECONDS=""
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
    --step-interval-seconds)
      STEP_INTERVAL_SECONDS="${2:-}"
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

if [[ -z "${STEP_INTERVAL_SECONDS}" ]]; then
  fail_closed "missing --step-interval-seconds"
fi

if ! [[ "${DURATION_MINUTES}" =~ ^[0-9]+$ ]] \
  || [[ "${DURATION_MINUTES}" -lt 1 ]] \
  || [[ "${DURATION_MINUTES}" -gt "${MAX_DURATION_MINUTES}" ]]; then
  fail_closed "invalid --duration-minutes: must be 1..${MAX_DURATION_MINUTES}"
fi

if ! [[ "${MAX_STEPS}" =~ ^[0-9]+$ ]] || [[ "${MAX_STEPS}" -lt 1 ]]; then
  fail_closed "invalid --max-steps: must be >= 1"
fi

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID="testnet_bounded_observation_$(date -u +%Y%m%dT%H%M%SZ)"
fi

EVIDENCE_ROOT="${STAGING_ROOT}/wrapper_evidence"
LOGS_DIR="${STAGING_ROOT}/logs"
MANIFEST_PATH="${EVIDENCE_ROOT}/manifest.json"
STEPS_PATH="${EVIDENCE_ROOT}/steps.jsonl"
mkdir -p "${EVIDENCE_ROOT}" "${LOGS_DIR}"

SHUTDOWN_REQUESTED=0
_on_shutdown() {
  SHUTDOWN_REQUESTED=1
}
trap _on_shutdown INT TERM

UTC_STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

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

if ! RUN_ID="${RUN_ID}" \
  DURATION_MINUTES="${DURATION_MINUTES}" \
  MAX_STEPS="${MAX_STEPS}" \
  STEP_INTERVAL_SECONDS="${STEP_INTERVAL_SECONDS}" \
  EVIDENCE_ROOT="${EVIDENCE_ROOT}" \
  MANIFEST_PATH="${MANIFEST_PATH}" \
  STEPS_PATH="${STEPS_PATH}" \
  SHUTDOWN_REQUESTED="${SHUTDOWN_REQUESTED}" \
  python3 - <<'PY'
import json
import math
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

run_id = os.environ["RUN_ID"]
duration_minutes = int(os.environ["DURATION_MINUTES"])
max_steps = int(os.environ["MAX_STEPS"])
step_interval_seconds = float(os.environ["STEP_INTERVAL_SECONDS"])
evidence_root = Path(os.environ["EVIDENCE_ROOT"])
manifest_path = Path(os.environ["MANIFEST_PATH"])
steps_path = Path(os.environ["STEPS_PATH"])

shutdown_requested = {"value": os.environ.get("SHUTDOWN_REQUESTED", "0") == "1"}


def _handle_signal(_signum, _frame) -> None:
    shutdown_requested["value"] = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

if not math.isfinite(step_interval_seconds) or step_interval_seconds <= 0.0:
    print("invalid --step-interval-seconds: must be > 0", file=sys.stderr)
    sys.exit(1)

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

wallclock_override = all(override_values)
stub_sleep = os.environ.get("PEAK_TRADE_BOUNDED_TESTNET_STAGING_STUB_SLEEP", "").strip() == "1"
steps_lines: list[str] = []
steps_emitted = 0

if wallclock_override:
    utc_started = override_values[0]
    utc_completed = override_values[1]
    start_monotonic_seconds = float(override_values[2])
    end_monotonic_seconds = float(override_values[3])
    steps_lines.append(
        json.dumps(
            {"step": 1, "mode": "staging_only", "run_id": run_id},
            sort_keys=True,
        )
        + "\n"
    )
    steps_emitted = 1
else:
    utc_started_dt = datetime.now(timezone.utc)
    utc_started = utc_started_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    fake_monotonic = {"value": time.monotonic()}

    def monotonic_now() -> float:
        return fake_monotonic["value"]

    def bounded_sleep(seconds: float) -> None:
        if stub_sleep:
            fake_monotonic["value"] += seconds
            return
        time.sleep(seconds)
        fake_monotonic["value"] = time.monotonic()

    start_monotonic_seconds = monotonic_now()
    deadline = start_monotonic_seconds + float(duration_minutes) * 60.0

    while steps_emitted < max_steps and monotonic_now() < deadline and not shutdown_requested["value"]:
        step_ts = utc_started_dt + timedelta(seconds=steps_emitted * step_interval_seconds)
        steps_lines.append(
            json.dumps(
                {
                    "step": steps_emitted + 1,
                    "mode": "bounded_staging_observation",
                    "run_id": run_id,
                    "utc": step_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                sort_keys=True,
            )
            + "\n"
        )
        steps_emitted += 1
        if steps_emitted >= max_steps or monotonic_now() >= deadline or shutdown_requested["value"]:
            break
        remaining = deadline - monotonic_now()
        if remaining > 0.0:
            bounded_sleep(min(step_interval_seconds, remaining))

    end_monotonic_seconds = monotonic_now()
    if stub_sleep:
        elapsed_seconds = end_monotonic_seconds - start_monotonic_seconds
        utc_completed_dt = utc_started_dt + timedelta(seconds=elapsed_seconds)
        utc_completed = utc_completed_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        utc_completed = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
    "max_steps": max_steps,
    "steps_emitted": steps_emitted,
    "step_interval_seconds": step_interval_seconds,
    "utc_started": utc_started,
    "utc_completed": utc_completed,
    "start_monotonic_seconds": start_monotonic_seconds,
    "end_monotonic_seconds": end_monotonic_seconds,
}
tmp_path = manifest_path.with_suffix(".json.tmp")
try:
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, manifest_path)
    steps_path.write_text("".join(steps_lines), encoding="utf-8")
except OSError as exc:
    print(f"manifest write failed: {exc}", file=sys.stderr)
    if tmp_path.exists():
        tmp_path.unlink(missing_ok=True)
    sys.exit(1)
PY
then
  fail_closed "bounded staging observation failed"
fi

{
  echo "testnet bounded evidence staging stdout run_id=${RUN_ID} steps=${MAX_STEPS}"
} > "${LOGS_DIR}/wrapper_stdout.log"
{
  echo "testnet bounded evidence staging stderr run_id=${RUN_ID} step_interval=${STEP_INTERVAL_SECONDS}"
} > "${LOGS_DIR}/wrapper_stderr.log"

exit 0
