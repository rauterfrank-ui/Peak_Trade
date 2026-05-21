#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"
cd "$ROOT"

ts_utc="${TS_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
evi="${EVI_OVERRIDE:-out/ops/p101_stop_playbook_${ts_utc}}"
mkdir -p "$evi"

# Hard guardrails: never allow live/record/execution enabling via this playbook.
deny_vars=(LIVE RECORD EXECUTION_ENABLE TRADING_ENABLE PT_ARMED PT_CONFIRM_TOKEN PT_CONFIRM_MERGE)
for v in "${deny_vars[@]}"; do
  if [ -n "${!v:-}" ]; then
    echo "P101_STOP_FAIL deny_var_set var=$v" | tee "$evi/P101_STOP_FAIL.txt"
    exit 3
  fi
done

# Sanity: repo must be clean (best effort; do not fail if user intentionally has untracked scratch excluded)
git status -sb > "$evi/GIT_STATUS.txt" || true

# Capture current ops state (best effort)
{
  echo "timestamp_utc=$ts_utc"
  echo "root=$ROOT"
  echo "user_uid=$(id -u || true)"
  echo "host=$(uname -a || true)"
} > "$evi/META.txt"

# Stop P99 ops loop (guarded) if installed
p99_plist="$HOME/Library/LaunchAgents/com.peaktrade.p99-ops-loop-guarded.plist"
if [ -f "$p99_plist" ]; then
  launchctl print "gui/$(id -u)/com.peaktrade.p99-ops-loop-guarded" > "$evi/LAUNCHD_P99_STATUS.before.txt" 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$p99_plist" > "$evi/LAUNCHD_P99_BOOTOUT.txt" 2>&1 || true
else
  echo "P99_PLIST_ABSENT" > "$evi/P99_PLIST.txt"
fi

# Stop P93 dashboard job if installed
p93_plist="$HOME/Library/LaunchAgents/com.peaktrade.p93_status_dashboard_v1.plist"
if [ -f "$p93_plist" ]; then
  launchctl print "gui/$(id -u)/com.peaktrade.p93-status-dashboard" > "$evi/LAUNCHD_P93_STATUS.before.txt" 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$p93_plist" > "$evi/LAUNCHD_P93_BOOTOUT.txt" 2>&1 || true
else
  echo "P93_PLIST_ABSENT" > "$evi/P93_PLIST.txt"
fi

# Stop P94 retention job if installed
p94_plist="$HOME/Library/LaunchAgents/com.peaktrade.p94_p93_status_dashboard_retention_v1.plist"
if [ -f "$p94_plist" ]; then
  launchctl print "gui/$(id -u)/com.peaktrade.p94-p93-status-dashboard-retention" > "$evi/LAUNCHD_P94_STATUS.before.txt" 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$p94_plist" > "$evi/LAUNCHD_P94_BOOTOUT.txt" 2>&1 || true
else
  echo "P94_PLIST_ABSENT" > "$evi/P94_PLIST.txt"
fi

# Stop P91 snapshot runner + P92 retention if installed
p91_plist="$HOME/Library/LaunchAgents/com.peaktrade.p91_audit_snapshot_runner_v1.plist"
if [ -f "$p91_plist" ]; then
  launchctl print "gui/$(id -u)/com.peaktrade.p91-audit-snapshot-runner" > "$evi/LAUNCHD_P91_STATUS.before.txt" 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$p91_plist" > "$evi/LAUNCHD_P91_BOOTOUT.txt" 2>&1 || true
else
  echo "P91_PLIST_ABSENT" > "$evi/P91_PLIST.txt"
fi

p92_plist="$HOME/Library/LaunchAgents/com.peaktrade.p92_p91_audit_snapshot_retention_v1.plist"
if [ -f "$p92_plist" ]; then
  launchctl print "gui/$(id -u)/com.peaktrade.p92-p91-audit-snapshot-retention" > "$evi/LAUNCHD_P92_STATUS.before.txt" 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$p92_plist" > "$evi/LAUNCHD_P92_BOOTOUT.txt" 2>&1 || true
else
  echo "P92_PLIST_ABSENT" > "$evi/P92_PLIST.txt"
fi

# Stop supervisor (P88 script)
bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh stop > "$evi/P88_SUPERVISOR_STOP.log" 2>&1 || true

# Final snapshot (best effort): P79 + P90 + P95 (should fail once supervisor stopped; capture anyway)
MODE="${MODE:-shadow}"
OUT_DIR="${OUT_DIR:-}"
if [ -z "$OUT_DIR" ]; then
  sup_base="out/ops/online_readiness_supervisor"
  latest="$(ls -1 "$sup_base" 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1 || true)"
  if [ -n "$latest" ]; then
    OUT_DIR="$sup_base/$latest"
  fi
fi
export OUT_DIR

MODE="$MODE" MAX_AGE_SEC="${MAX_AGE_SEC:-900}" bash scripts/ops/p79_supervisor_health_gate_v1.sh > "$evi/P79_GATE_AFTER_STOP.log" 2>&1 || true
MIN_TICKS="${MIN_TICKS:-2}" MAX_AGE_SEC="${MAX_AGE_SEC:-900}" bash scripts/ops/p90_supervisor_metrics_v1.sh > "$evi/P90_METRICS_AFTER_STOP.json" 2>&1 || true
MODE="$MODE" MAX_AGE_SEC="${MAX_AGE_SEC:-900}" MIN_TICKS="${MIN_TICKS:-2}" bash scripts/ops/p95_ops_health_meta_gate_v1.sh > "$evi/P95_META_GATE_AFTER_STOP.log" 2>&1 || true

# Evidence manifest + checksums (exclude SHA256SUMS itself)
EVI="$evi" python3 - <<'PY'
import json, os
from pathlib import Path
evi = Path(os.environ["EVI"])
files = sorted([p.name for p in evi.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt"])
(evi/"manifest.json").write_text(json.dumps({"files": files}, indent=2, sort_keys=True), encoding="utf-8")
PY
EVI="$evi" python3 - <<'PY'
import hashlib, os
from pathlib import Path
evi = Path(os.environ["EVI"])
lines=[]
for p in sorted(evi.iterdir()):
    if p.is_file() and p.name != "SHA256SUMS.txt":
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{h}  {p.name}")
(evi/"SHA256SUMS.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
PY
( cd "$evi" && shasum -a 256 -c SHA256SUMS.txt ) > "$evi/SHA256_VERIFY.txt" 2>&1 || true

bundle="${evi}.bundle.tgz"
tar -czf "$bundle" -C "$(dirname "$evi")" "$(basename "$evi")"
bundle_sha256="$(shasum -a 256 "$bundle" | awk '{print $1}')"
echo "$bundle_sha256  $(basename "$bundle")" > "${bundle}.sha256"
shasum -a 256 -c "${bundle}.sha256" > "${bundle}.sha256.verify" 2>&1 || true

pin="out/ops/P101_STOP_PLAYBOOK_DONE_${ts_utc}.txt"
{
  echo "P101_STOP_PLAYBOOK_DONE OK"
  echo "timestamp_utc=$ts_utc"
  echo "main_head=$(git rev-parse HEAD)"
  echo "evi=$evi"
  echo "bundle=$bundle"
  echo "bundle_sha256=$bundle_sha256"
} > "$pin"
shasum -a 256 "$pin" | awk '{print $1}' > "${pin}.sha256"
shasum -a 256 -c "${pin}.sha256" > "${pin}.sha256.verify" 2>&1 || true

# Post-stop primary evidence pack + P79 archive verify — operator hints only (non-executing v0).
pack_out_dir="${OUT_DIR:-out/ops/online_readiness_supervisor/run_<SESSION>}"
pack_archive_root="${ARCHIVE_ROOT_HINT:-/path/to/durable/archive/supervisor_pack_${ts_utc}}"
hint_file="$evi/P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt"
{
  echo "P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS_v0"
  echo "HINT_ONLY=true"
  echo "WRAPPER_REFERENCED=true"
  echo "WRAPPER_NOT_EXECUTED_BY_P101=true"
  echo "PACK_NOT_EXECUTED_BY_P101=true"
  echo "P79_ARCHIVE_VERIFY_NOT_EXECUTED_BY_P101=true"
  echo "OPERATOR_MUST_RUN_EXPLICITLY=true"
  echo "EVIDENCE_NON_AUTHORIZING=true"
  echo "timestamp_utc=$ts_utc"
  echo "supervisor_out_dir=$pack_out_dir"
  echo "suggested_archive_root=$pack_archive_root"
  echo ""
  echo "# Copy-paste: post-stop pack via operator wrapper (delegates to pack script; non-authorizing)"
  echo "bash scripts/ops/run_online_readiness_post_stop_pack_v0.sh \\"
  echo "  --out-dir \"${pack_out_dir}\" \\"
  echo "  --archive-root \"${pack_archive_root}\" \\"
  echo "  --primary-evidence-enforce"
  echo ""
  echo "# Optional: wrapper with explicit P79 ARCHIVE_ROOT verify (--p79-archive-verify; off by default)"
  echo "bash scripts/ops/run_online_readiness_post_stop_pack_v0.sh \\"
  echo "  --out-dir \"${pack_out_dir}\" \\"
  echo "  --archive-root \"${pack_archive_root}\" \\"
  echo "  --primary-evidence-enforce \\"
  echo "  --p79-archive-verify"
} > "$hint_file"
cat "$hint_file"

echo "P101_STOP_OK evi=$evi pin=$pin bundle=$bundle hint=$hint_file"
