#!/usr/bin/env bash
set -euo pipefail

# P95 — Ops Health Meta Gate v1
# Purpose: Assert "shadow readiness loop is healthy" on macOS launchd:
# - Supervisor job present
# - P93 dashboard job present
# - P94 retention job present
# - latest P93 pin exists and points to valid EVI
# - P79/P90 in that EVI are green
#
# Exit codes: 0 OK, 2 usage, 3 gate failed
#
# Env:
#   MAX_AGE_SEC (default 900) for P79 age threshold (P93 already uses it but we validate snapshot too)

MAX_AGE_SEC="${MAX_AGE_SEC:-900}"

fail() { echo "P95_GATE_FAIL: $*" >&2; exit 3; }
ok() { echo "P95_GATE_OK $*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "missing_cmd:$1"; }

need_cmd launchctl
need_cmd python3
need_cmd bash
need_cmd awk
need_cmd sed

uid="$(id -u)"

# 1) launchd jobs should exist
for label in \
  "com.peaktrade.online-readiness-supervisor" \
  "com.peaktrade.p93-status-dashboard" \
  "com.peaktrade.p94-p93-status-dashboard-retention"; do
  if ! launchctl print "gui/$uid/$label" >/dev/null 2>&1; then
    fail "launchd_job_missing:$label"
  fi
done

# 2) latest P93 pin + evi
pin="$(ls -1 out/ops/P93_STATUS_DASHBOARD_DONE_*Z.txt 2>/dev/null | LC_ALL=C sort | tail -n 1 || true)"
[ -n "$pin" ] || fail "p93_pin_missing"

evi="$(awk -F= '/^evi=/{print $2}' "$pin" | tail -n 1 || true)"
[ -n "$evi" ] || fail "p93_pin_missing_evi"
[ -d "$evi" ] || fail "p93_evi_missing:$evi"

# 3) P79 must be OK and not stale beyond MAX_AGE_SEC
p79_log="$evi/P79_GATE.log"
[ -f "$p79_log" ] || fail "p79_gate_log_missing"
grep -q "P79_GATE_OK" "$p79_log" || fail "p79_gate_not_ok"

age="$(python3 - <<PY
import re
from pathlib import Path
t = Path(r"$p79_log").read_text(errors="ignore")
m = re.search(r'age_sec=(\d+)', t)
print(m.group(1) if m else "")
PY
)"
[ -n "$age" ] || fail "p79_age_missing"
if [ "$age" -gt "$MAX_AGE_SEC" ]; then
  fail "p79_stale age_sec=$age max_age_sec=$MAX_AGE_SEC"
fi

# 4) P90 alerts must be empty and status ready
p90="$evi/P90_METRICS.json"
[ -f "$p90" ] || fail "p90_metrics_missing"
python3 -c "
import json, sys
p = sys.argv[1]
j = json.load(open(p))
alerts = j.get('alerts') or []
if alerts:
    print('P95_GATE_FAIL: p90_alerts', alerts, file=sys.stderr)
    sys.exit(3)
if (j.get('latest_p76_status') or '').lower() != 'ready':
    print('P95_GATE_FAIL: p90_not_ready', j.get('latest_p76_status'), file=sys.stderr)
    sys.exit(3)
print('P90_OK tick_count=%s age_sec=%s' % (j.get('tick_count'), j.get('age_sec')))
" "$p90" || fail "p90_metrics_invalid"

ok "pin=$pin evi=$evi p79_age_sec=$age max_age_sec=$MAX_AGE_SEC"
