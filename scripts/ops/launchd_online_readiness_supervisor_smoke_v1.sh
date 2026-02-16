#!/usr/bin/env bash
set -euo pipefail

# P88: launchd supervisor script — subcommands: start|stop|status|smoke
# Usage:
#   bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh start
#   bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh status
#   bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh stop
#   bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh smoke   # default
# Paper/shadow only (launchd supervisor uses P76/P86 gates).

ACTION="${1:-smoke}"
[ $# -gt 0 ] && shift || true

__label_default() {
  echo "com.peaktrade.online-readiness-supervisor"
}

__plist_dst_default() {
  echo "$HOME/Library/LaunchAgents/com.peaktrade.online_readiness_supervisor_v1.plist"
}

__domain_gui() {
  echo "gui/$(id -u)"
}

__status_only() {
  local label domain
  label="$(__label_default)"
  domain="$(__domain_gui)"
  launchctl print "$domain/$label" || return 2
}

__stop_only() {
  local label plist_dst domain
  label="$(__label_default)"
  plist_dst="$(__plist_dst_default)"
  domain="$(__domain_gui)"
  launchctl bootout "$domain" "$plist_dst" 2>/dev/null || true
  launchctl kill SIGTERM "$domain/$label" 2>/dev/null || true
  echo "OK: stop issued for $domain/$label"
}

__start_only() {
  local label plist_dst domain
  label="$(__label_default)"
  plist_dst="$(__plist_dst_default)"
  domain="$(__domain_gui)"
  launchctl bootstrap "$domain" "$plist_dst" 2>/dev/null || true
  if ! launchctl kickstart -k "$domain/$label"; then
    echo "ERR: kickstart failed for $domain/$label (check plist label/domain)" >&2
    return 3
  fi
  echo "OK: started $domain/$label"
}

case "${ACTION}" in
  status)
    __status_only
    exit $?
    ;;
  stop)
    __stop_only
    exit $?
    ;;
  start)
    # Fall through to prep + start
    ;;
  smoke|"")
    # Fall through to full smoke
    ;;
  *)
    echo "Usage: $0 [start|status|stop|smoke]" >&2
    exit 2
    ;;
esac

# --- Prep + smoke flow (for start and smoke) ---
cd "$(git rev-parse --show-toplevel)"
ROOT="$(git rev-parse --show-toplevel)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_BASE="${OUT_BASE:-$ROOT/out/ops/online_readiness_supervisor}"
OUT_DIR="${OUT_DIR:-$OUT_BASE/run_$TS}"

PLIST_SRC="$ROOT/docs/ops/services/launchd_online_readiness_supervisor_v1.plist"
PLIST_DST_DIR="$HOME/Library/LaunchAgents"
PLIST_DST="$PLIST_DST_DIR/com.peaktrade.online_readiness_supervisor_v1.plist"

MODE="${MODE:-shadow}"
INTERVAL="${INTERVAL:-10}"
MAX_AGE_SEC="${MAX_AGE_SEC:-120}"

mkdir -p "$OUT_DIR" "$PLIST_DST_DIR"
cp -v "$PLIST_SRC" "$PLIST_DST"

export ROOT OUT_DIR PLIST_DST MODE INTERVAL

python3 - <<'PY'
import os
import plistlib
from pathlib import Path

plist_path = Path(os.environ["PLIST_DST"])
root = Path(os.environ["ROOT"]).expanduser()
out_dir = Path(os.environ["OUT_DIR"]).expanduser()
mode = os.environ.get("MODE", "shadow")
interval = os.environ.get("INTERVAL", "60")

with plist_path.open("rb") as f:
    pl = plistlib.load(f)

env = pl.get("EnvironmentVariables", {})
env.update({
    "PYTHONPATH": str(root),
    "MODE": mode,
    "OUT_DIR": str(out_dir),
    "RUN_ID": "launchd_smoke",
    "INTERVAL": str(interval),
    "SUPERVISOR_ENABLE": "YES",
    "ITERATIONS": "0",
})
pl["EnvironmentVariables"] = env

args = pl.get("ProgramArguments", [])
if args:
    fixed = []
    for a in args:
        if a.endswith("scripts/ops/online_readiness_supervisor_v1.sh"):
            fixed.append(str(root / "scripts/ops/online_readiness_supervisor_v1.sh"))
        else:
            fixed.append(a)
    pl["ProgramArguments"] = fixed

pl["StandardOutPath"] = str(out_dir / "LAUNCHD_SUPERVISOR.out.log")
pl["StandardErrorPath"] = str(out_dir / "LAUNCHD_SUPERVISOR.err.log")
pl["WorkingDirectory"] = str(root)

with plist_path.open("wb") as f:
    plistlib.dump(pl, f)

print("patched:", plist_path)
PY

plutil -lint "$PLIST_DST"

LABEL="$(/usr/libexec/PlistBuddy -c 'Print :Label' "$PLIST_DST" 2>/dev/null || true)"
if [ -z "${LABEL}" ]; then
  LABEL="com.peaktrade.online_readiness_supervisor_v1"
fi

if [ "${ACTION}" = "start" ]; then
  launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
  launchctl kickstart -k "gui/$(id -u)/$LABEL" || true
  echo "OK out_dir=$OUT_DIR label=$LABEL"
  exit 0
fi

# --- smoke: full workflow ---
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
launchctl kickstart -k "gui/$(id -u)/$LABEL" || true

sleep 90

MODE="$MODE" OUT_DIR="$OUT_DIR" MAX_AGE_SEC="$MAX_AGE_SEC" \
  bash "$ROOT/scripts/ops/p79_supervisor_health_gate_v1.sh" | tee "$OUT_DIR/P79_GATE_SMOKE.log"

STOP=1 OUT_DIR="$OUT_DIR" \
  bash "$ROOT/scripts/ops/online_readiness_supervisor_v1.sh" | tee "$OUT_DIR/P80_STOP.log" || true

launchctl unload "$PLIST_DST" 2>/dev/null || true

echo "OK out_dir=$OUT_DIR label=$LABEL"
