#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}"

TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="out/ops/live_pilot_session_${TS_UTC}"
mkdir -p "${OUT}"

die() { echo "ERROR: $*" | tee -a "${OUT}/session.log" >&2; exit 2; }

echo "ts_utc=${TS_UTC}" | tee "${OUT}/session.env"
echo "git_head=$(git rev-parse HEAD)" | tee -a "${OUT}/session.env"
echo "mode=${PT_EXEC_MODE:-__UNSET__}" | tee -a "${OUT}/session.env"

PT_LIVE_ENABLED="${PT_LIVE_ENABLED:-NO}"
PT_LIVE_ARMED="${PT_LIVE_ARMED:-NO}"
PT_LIVE_ALLOW_FLAGS="${PT_LIVE_ALLOW_FLAGS:-}"
PT_LIVE_DRY_RUN="${PT_LIVE_DRY_RUN:-YES}"
PT_CONFIRM_TOKEN="${PT_CONFIRM_TOKEN:-}"
PT_CONFIRM_TOKEN_EXPECTED="${PT_CONFIRM_TOKEN_EXPECTED:-}"

echo "PT_LIVE_ENABLED=${PT_LIVE_ENABLED}" | tee -a "${OUT}/session.env"
echo "PT_LIVE_ARMED=${PT_LIVE_ARMED}" | tee -a "${OUT}/session.env"
echo "PT_LIVE_ALLOW_FLAGS=${PT_LIVE_ALLOW_FLAGS}" | tee -a "${OUT}/session.env"
echo "PT_LIVE_DRY_RUN=${PT_LIVE_DRY_RUN}" | tee -a "${OUT}/session.env"
echo "PT_CONFIRM_TOKEN_PRESENT=$([ -n "${PT_CONFIRM_TOKEN}" ] && echo YES || echo NO)" | tee -a "${OUT}/session.env"
echo "PT_CONFIRM_TOKEN_EXPECTED_PRESENT=$([ -n "${PT_CONFIRM_TOKEN_EXPECTED}" ] && echo YES || echo NO)" | tee -a "${OUT}/session.env"

if [ "${PT_LIVE_ENABLED}" != "YES" ]; then
  die "PT_LIVE_ENABLED must be YES"
fi
if [ "${PT_LIVE_ARMED}" != "YES" ]; then
  die "PT_LIVE_ARMED must be YES"
fi
echo "${PT_LIVE_ALLOW_FLAGS}" | rg -q '(^|,|\s)pilot_only(,|\s|$)' || die "PT_LIVE_ALLOW_FLAGS must include pilot_only"
if [ "${PT_LIVE_DRY_RUN}" != "YES" ]; then
  die "PT_LIVE_DRY_RUN must be YES for the first pilot runs"
fi
if [ -z "${PT_CONFIRM_TOKEN_EXPECTED}" ]; then
  die "PT_CONFIRM_TOKEN_EXPECTED must be set (one-time token)"
fi
if [ "${PT_CONFIRM_TOKEN}" != "${PT_CONFIRM_TOKEN_EXPECTED}" ]; then
  die "PT_CONFIRM_TOKEN mismatch"
fi

echo "GATES_OK=YES" | tee -a "${OUT}/session.env"
echo "NOTE: This wrapper does NOT implement live trading itself. It only gates and then invokes the existing orchestrator entrypoint." | tee -a "${OUT}/session.log"

PROFILE="${PROFILE:-btc_momentum}"
DURATION_MIN="${DURATION_MIN:-10}"
CONFIG_PATH="${CONFIG_PATH:-config/config.toml}"

echo "PROFILE=${PROFILE}" | tee -a "${OUT}/session.env"
echo "DURATION_MIN=${DURATION_MIN}" | tee -a "${OUT}/session.env"
echo "CONFIG_PATH=${CONFIG_PATH}" | tee -a "${OUT}/session.env"

shasum -a 256 "${OUT}/session.env" > "${OUT}/session.env.sha256"
shasum -a 256 -c "${OUT}/session.env.sha256" >/dev/null

echo "START_ORCHESTRATOR" | tee -a "${OUT}/session.log"
python3 scripts/orchestrate_testnet_runs.py \
  --config "${CONFIG_PATH}" \
  --profile "${PROFILE}" \
  --override-duration "${DURATION_MIN}" \
  | tee -a "${OUT}/orchestrator.log"

echo "DONE" | tee -a "${OUT}/session.log"
