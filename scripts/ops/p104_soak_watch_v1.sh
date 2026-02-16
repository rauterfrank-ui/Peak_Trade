#!/usr/bin/env bash
set -euo pipefail

# --- Hard safety defaults (non-negotiable) ---
MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"                 # do not allow side-effects beyond stop-playbook
MAX_AGE_SEC="${MAX_AGE_SEC:-900}"
MIN_TICKS="${MIN_TICKS:-2}"
SLEEP_SEC="${SLEEP_SEC:-1800}"            # 30 min
ITERATIONS="${ITERATIONS:-0}"             # 0 = forever

# deny-list env vars (prevent accidental escalation)
deny_vars=(
  LIVE RECORD
  EXECUTION_ENABLE TRADING_ENABLE ENABLE_LIVE_TRADING
  PT_ARMED PT_ENABLED PT_CONFIRM_TOKEN PT_CONFIRM_MERGE
  KRAKEN_API_KEY KRAKEN_API_SECRET
  BINANCE_API_KEY BINANCE_API_SECRET
  API_KEY API_SECRET
)
for v in "${deny_vars[@]}"; do
  if [ -n "${!v:-}" ]; then
    echo "P104_GUARD_FAIL: env_var_disallowed $v" >&2
    exit 3
  fi
done

if [ "$MODE" != "shadow" ] && [ "$MODE" != "paper" ]; then
  echo "P104_GUARD_FAIL: mode_not_allowed mode=$MODE" >&2
  exit 3
fi
if [ "$DRY_RUN" != "YES" ]; then
  echo "P104_GUARD_FAIL: DRY_RUN_required DRY_RUN=$DRY_RUN" >&2
  exit 3
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

ts_utc(){ date -u +%Y%m%dT%H%M%SZ; }

echo "P104_SOAK_WATCH_START mode=$MODE dry_run=$DRY_RUN max_age_sec=$MAX_AGE_SEC min_ticks=$MIN_TICKS sleep_sec=$SLEEP_SEC iterations=$ITERATIONS"

i=0
while true; do
  i=$((i+1))
  TS="$(ts_utc)"
  echo "[$TS] heartbeat start i=$i"

  if MODE="$MODE" MAX_AGE_SEC="$MAX_AGE_SEC" MIN_TICKS="$MIN_TICKS" bash scripts/ops/p95_ops_health_meta_gate_v1.sh; then
    echo "[$TS] P95_OK"
  else
    rc=$?
    echo "[$TS] P95_FAIL rc=$rc -> incident snapshot + stop playbook" >&2

    # Incident snapshots (best-effort)
    MODE="$MODE" MAX_AGE_SEC="$MAX_AGE_SEC" MIN_TICKS="$MIN_TICKS" bash scripts/ops/p93_online_readiness_status_dashboard_v1.sh || true
    DRY_RUN=YES OUT_DIR="${OUT_DIR:-}" bash scripts/ops/p91_kickstart_when_ready_v1.sh || true

    # Stop playbook (best-effort)
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p99-ops-loop-guarded.plist" 2>/dev/null || true
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p93_status_dashboard_v1.plist" 2>/dev/null || true
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p94_p93_status_dashboard_retention_v1.plist" 2>/dev/null || true
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p91_audit_snapshot_runner_v1.plist" 2>/dev/null || true
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p92_p91_audit_snapshot_retention_v1.plist" 2>/dev/null || true
    launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.peaktrade.p104_soak_watch_v1.plist" 2>/dev/null || true
    bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh stop || true

    echo "[$TS] P104_SOAK_WATCH_STOPPED_AFTER_FAIL"
    exit "$rc"
  fi

  echo "[$TS] latest_p93_pin=$(ls -1 out/ops/P93_STATUS_DASHBOARD_DONE_*.txt 2>/dev/null | tail -n 1 || true)"
  echo "[$TS] latest_p91_pin=$(ls -1 out/ops/P91_AUDIT_SNAPSHOT_DONE_*.txt 2>/dev/null | tail -n 1 || true)"
  echo "[$TS] latest_p99_pin=$(ls -1 out/ops/P99_OPS_LOOP_DONE_*.txt 2>/dev/null | tail -n 1 || true)"

  if [ "$ITERATIONS" != "0" ] && [ "$i" -ge "$ITERATIONS" ]; then
    echo "P104_SOAK_WATCH_DONE iterations=$ITERATIONS"
    exit 0
  fi

  sleep "$SLEEP_SEC"
done
