#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ts_utc="${TS_OVERRIDE:-$(date -u +%Y%m%dT%H%M%SZ)}"
evi="${EVI_OVERRIDE:-out/ops/p93_online_readiness_status_${ts_utc}}"
mkdir -p "$evi"

# OUT_DIR resolution
out_dir_default="out/ops/online_readiness_supervisor/$(ls -1 out/ops/online_readiness_supervisor 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1)"
OUT_DIR="${OUT_DIR:-$out_dir_default}"
MODE="${MODE:-shadow}"
MAX_AGE_SEC="${MAX_AGE_SEC:-900}"
MIN_TICKS="${MIN_TICKS:-2}"

{
  echo "P93_STATUS_DASHBOARD"
  echo "timestamp_utc=$ts_utc"
  echo "main_head=$(git rev-parse HEAD)"
  echo "out_dir=$OUT_DIR"
  echo "mode=$MODE"
  echo "max_age_sec=$MAX_AGE_SEC"
  echo "min_ticks=$MIN_TICKS"
} > "$evi/META.txt"

# launchd supervisor status (best-effort)
if [ -x "$ROOT/scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh" ]; then
  (cd "$ROOT" && bash scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh status) > "$evi/LAUNCHD_STATUS.txt" 2>&1 || true
else
  echo "missing scripts/ops/launchd_online_readiness_supervisor_smoke_v1.sh" > "$evi/LAUNCHD_STATUS.txt"
fi

# P79 gate
(cd "$ROOT" && OUT_DIR="$OUT_DIR" MODE="$MODE" MAX_AGE_SEC="$MAX_AGE_SEC" bash scripts/ops/p79_supervisor_health_gate_v1.sh) \
  > "$evi/P79_GATE.log" 2>&1 || true

# P90 metrics
(cd "$ROOT" && OUT_DIR="$OUT_DIR" MIN_TICKS="$MIN_TICKS" MAX_AGE_SEC="$MAX_AGE_SEC" bash scripts/ops/p90_supervisor_metrics_v1.sh) \
  > "$evi/P90_METRICS.json" 2>&1 || true

# Pretty-print P90_METRICS if valid JSON
python3 -c "
import json
from pathlib import Path
p = Path(r'$evi') / 'P90_METRICS.json'
if p.exists():
    try:
        obj = json.loads(p.read_text())
        (Path(r'$evi') / 'P90_METRICS.pretty.json').write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    except Exception:
        pass
" 2>/dev/null || true

# latest P76 result
latest_p76="$(find "$OUT_DIR" -type f -path '*/tick_*/p76/P76_RESULT.txt' 2>/dev/null | LC_ALL=C sort | tail -n 1 || true)"
echo "LATEST_P76=$latest_p76" > "$evi/LATEST_P76.txt"
if [ -n "$latest_p76" ]; then
  tail -n 20 "$latest_p76" > "$evi/LATEST_P76.tail.txt" 2>/dev/null || true
fi

# latest P91 pin (best-effort)
latest_p91_evi="$(ls -1 out/ops 2>/dev/null | grep '^p91_shadow_soak_audit_snapshot_' | LC_ALL=C sort | tail -n 1 || true)"
latest_p91_pin="$(ls -1 out/ops 2>/dev/null | grep '^P91_AUDIT_SNAPSHOT_DONE_.*\.txt$' | LC_ALL=C sort | tail -n 1 || true)"
{
  echo "LATEST_P91_EVI=$latest_p91_evi"
  echo "LATEST_P91_PIN=$latest_p91_pin"
} > "$evi/LATEST_P91.txt"

# rollup index tail
if [ -f "$OUT_DIR/SHADOW_SOAK_INDEX.ndjson" ]; then
  tail -n 200 "$OUT_DIR/SHADOW_SOAK_INDEX.ndjson" > "$evi/SHADOW_SOAK_INDEX.tail.ndjson"
else
  echo "missing $OUT_DIR/SHADOW_SOAK_INDEX.ndjson" > "$evi/SHADOW_SOAK_INDEX.tail.ndjson"
fi

# manifest
python3 -c "
import json
from pathlib import Path
root = Path(r'$evi')
files = sorted([p.name for p in root.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt'])
if 'manifest.json' not in files:
    files.append('manifest.json')
    files.sort()
print(json.dumps({'version': 'p93_status_dashboard_v1', 'files': files}, indent=2))
" > "$evi/manifest.json"

# sha256sums (exclude SHA256SUMS itself)
(cd "$ROOT" && find "$evi" -type f ! -name 'SHA256SUMS.txt' -print | LC_ALL=C sort | while read -r f; do shasum -a 256 "$f"; done) \
  > "$evi/SHA256SUMS.txt"

shasum -a 256 -c "$evi/SHA256SUMS.txt" > "$evi/SHA256SUMS.verify.log" 2>&1 || true

# bundle
bundle="$evi.bundle.tgz"
tar -czf "$bundle" "$evi"
shasum -a 256 "$bundle" > "$bundle.sha256"

# pin
pin="out/ops/P93_STATUS_DASHBOARD_DONE_${ts_utc}.txt"
{
  echo "P93_STATUS_DASHBOARD_DONE OK"
  echo "timestamp_utc=$ts_utc"
  echo "main_head=$(git rev-parse HEAD)"
  echo "evi=$evi"
  echo "bundle=$bundle"
  echo "bundle_sha256=$(cut -d ' ' -f1 < "$bundle.sha256")"
} > "$pin"
shasum -a 256 "$pin" > "$pin.sha256"

echo "P93_OK pin=$pin evi=$evi"
