#!/usr/bin/env bash
set -euo pipefail

# Smoke workflow for macOS launchd Supervisor v1 (paper/shadow only).
# Creates OUT_DIR, patches plist, starts agent, runs P79 gate, stops agent.

cd "$(git rev-parse --show-toplevel)"
ROOT="$(git rev-parse --show-toplevel)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
# OUT_DIR must be under $ROOT/out/ops/ (supervisor P78 constraint)
OUT_BASE="${OUT_BASE:-$ROOT/out/ops/online_readiness_supervisor}"
OUT_DIR="${OUT_DIR:-$OUT_BASE/run_$TS}"

PLIST_SRC="$ROOT/docs/ops/services/launchd_online_readiness_supervisor_v1.plist"
PLIST_DST_DIR="$HOME/Library/LaunchAgents"
PLIST_DST="$PLIST_DST_DIR/com.peaktrade.online_readiness_supervisor_v1.plist"

MODE="${MODE:-shadow}"
INTERVAL="${INTERVAL:-10}"   # 10s for smoke (first tick + gate ~30-60s); override for stability runs
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

# Start (best effort idempotent)
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
launchctl kickstart -k "gui/$(id -u)/$LABEL" || true

# Wait for first tick (tick runs p86/gate; allow ~90s for gate + startup)
sleep 90

# Health gate
MODE="$MODE" OUT_DIR="$OUT_DIR" MAX_AGE_SEC="$MAX_AGE_SEC" \
  bash "$ROOT/scripts/ops/p79_supervisor_health_gate_v1.sh" | tee "$OUT_DIR/P79_GATE_SMOKE.log"

# Stop: first graceful via P80, then ensure agent is unloaded
STOP=1 OUT_DIR="$OUT_DIR" \
  bash "$ROOT/scripts/ops/online_readiness_supervisor_v1.sh" | tee "$OUT_DIR/P80_STOP.log" || true

launchctl unload "$PLIST_DST" 2>/dev/null || true

echo "OK out_dir=$OUT_DIR label=$LABEL"
