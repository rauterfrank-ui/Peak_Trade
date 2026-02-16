#!/usr/bin/env bash
# P91 Audit Snapshot Runner v1
# One-shot: collect P79 + P90 + P91, package, pin. Read-only, paper/shadow.
# Invoke anytime; optional cron/launchd later.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUT_DIR_DEFAULT="out/ops/online_readiness_supervisor/$(ls -1 out/ops/online_readiness_supervisor 2>/dev/null | grep '^run_' | LC_ALL=C sort | tail -n 1)"
export OUT_DIR="${OUT_DIR:-$OUT_DIR_DEFAULT}"
test -d "$OUT_DIR" || { echo "ERR missing OUT_DIR=$OUT_DIR" >&2; exit 2; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/p91_shadow_soak_audit_snapshot_${TS}"
mkdir -p "$EVI"

MODE=shadow MAX_AGE_SEC=900 OUT_DIR="$OUT_DIR" \
  bash scripts/ops/p79_supervisor_health_gate_v1.sh | tee "$EVI/P79_GATE.log"

MIN_TICKS=2 MAX_AGE_SEC=900 OUT_DIR="$OUT_DIR" \
  bash scripts/ops/p90_supervisor_metrics_v1.sh | tee "$EVI/P90_METRICS.json"

export TS_OVERRIDE="$TS"
python3 - <<PY
import json, pathlib, os
ts = os.environ["TS_OVERRIDE"]
p = pathlib.Path(f"out/ops/p91_shadow_soak_audit_snapshot_{ts}")
j = json.loads(p.joinpath("P90_METRICS.json").read_text())
p.joinpath("P90_METRICS.pretty.json").write_text(json.dumps(j, indent=2, sort_keys=True) + "\n")
PY

OUT_DIR="$OUT_DIR" TS_OVERRIDE="$TS" python3 - <<'PY'
import json, os
from pathlib import Path
from src.ops.p91 import P91AuditContextV1, build_shadow_soak_audit_v1

out_dir = Path(os.environ["OUT_DIR"])
evi = Path(f"out/ops/p91_shadow_soak_audit_snapshot_{os.environ['TS_OVERRIDE']}")

ctx = P91AuditContextV1(out_dir=out_dir, max_age_sec=900, min_ticks=2)
rep = build_shadow_soak_audit_v1(ctx)

(evi / "P91_AUDIT.json").write_text(json.dumps(rep, sort_keys=True) + "\n")
(evi / "P91_AUDIT.pretty.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
(evi / "manifest.json").write_text(json.dumps({
    "out_dir": str(out_dir),
    "files": ["P79_GATE.log", "P90_METRICS.json", "P90_METRICS.pretty.json", "P91_AUDIT.json", "P91_AUDIT.pretty.json", "manifest.json"],
    "ts_utc": os.environ["TS_OVERRIDE"],
}, indent=2, sort_keys=True) + "\n")
print("P91_AUDIT_SNAPSHOT_OK", "evi=" + str(evi))
PY

(
  find "$EVI" -type f ! -name 'SHA256SUMS.txt' -print \
    | LC_ALL=C sort \
    | while IFS= read -r f; do shasum -a 256 "$f"; done > "$EVI/SHA256SUMS.txt"
)
shasum -a 256 -c "$EVI/SHA256SUMS.txt"

BUNDLE="${EVI}.bundle.tgz"
tar -czf "$BUNDLE" "$EVI"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"
shasum -a 256 -c "${BUNDLE}.sha256"

PIN="out/ops/P91_AUDIT_SNAPSHOT_DONE_${TS}.txt"
{
  echo "P91_AUDIT_SNAPSHOT_DONE OK"
  echo "timestamp_utc=$TS"
  echo "main_head=$(git rev-parse HEAD)"
  echo "out_dir=$OUT_DIR"
  echo "evi=$EVI"
  echo "bundle=$BUNDLE"
  echo "bundle_sha256=$(cut -d' ' -f1 < "${BUNDLE}.sha256")"
} > "$PIN"
shasum -a 256 "$PIN" > "${PIN}.sha256"
shasum -a 256 -c "${PIN}.sha256"

echo "OK OUT_DIR=$OUT_DIR"
echo "EVI=$EVI"
echo "BUNDLE=$BUNDLE"
echo "PIN=$PIN"
