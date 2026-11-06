#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"
TS="${TS_UTC:-$(date -u +%Y%m%dT%H%M%SZ)}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OPS_DIR="out/ops"
EVI_DIR="${OPS_DIR}/p121_execution_wiring_proof_${TS}"
BUNDLE="${EVI_DIR}.bundle.tgz"
PIN="${OPS_DIR}/P121_EXECUTION_WIRING_PROOF_DONE_${TS}.txt"

# Guards
case "$MODE" in shadow|paper) ;;
  *)
  echo "P121_GUARD_FAIL: mode_must_be_shadow_or_paper mode=${MODE}" >&2
  exit 3
esac
if [[ "$DRY_RUN" != "YES" ]]; then
  echo "P121_GUARD_FAIL: dry_run_must_be_yes dry_run=${DRY_RUN}" >&2
  exit 3
fi
for v in LIVE RECORD TRADING_ENABLE PT_ARMED PT_ENABLED API_KEY API_SECRET API_PASSPHRASE; do
  if [[ -n "${!v:-}" ]]; then
    echo "P121_GUARD_FAIL: forbidden_env ${v} is set" >&2
    exit 3
  fi
done

mkdir -p "$EVI_DIR"

# 1) Router CLI matrix (place_order + cancel_all) across adapters
REPORT1="${EVI_DIR}/router_place_order.json"
REPORT2="${EVI_DIR}/router_cancel_all.json"

python3 -m src.execution.router.cli_v1 \
  --mode "$MODE" \
  --dry-run YES \
  --adapter mock \
  --intent place_order \
  --market BTC-USD \
  --side buy \
  --qty 0.01 \
  > "$REPORT1" 2>> "${EVI_DIR}/router_place_order.log"

python3 -m src.execution.router.cli_v1 \
  --mode "$MODE" \
  --dry-run YES \
  --adapter mock \
  --intent cancel_all \
  --market BTC-USD \
  > "$REPORT2" 2>> "${EVI_DIR}/router_cancel_all.log"

# 2) Session runner matrix (already mocks-only)
python3 -c "
from src.execution.session.runner_v1 import run_execution_session_v1, ExecutionSessionContextV1
ctx = ExecutionSessionContextV1(mode='${MODE}', dry_run=True)
run_execution_session_v1(ctx)
" > "${EVI_DIR}/session_runner.log" 2>&1

# 3) Minimal pytest proof (fast, skip p117 ops_loop tests that need Supervisor)
python3 -m pytest -q tests/p112 tests/p113 tests/p115 tests/p116 tests/p118 \
  > "${EVI_DIR}/pytest_smoke.log" 2>&1

# 4) Manifest + SHA256SUMS (repo-root-relative, sandbox-safe)
export EVI_DIR
python3 - <<'PY'
import json, os
root = os.getcwd()
evi = os.environ["EVI_DIR"]
items = []
for dirpath, _, filenames in os.walk(evi):
    for fn in sorted(filenames):
        p = os.path.join(dirpath, fn)
        items.append(os.path.relpath(p, root))
# Include manifest.json (written next)
manifest_path = os.path.relpath(os.path.join(evi, "manifest.json"), root)
if manifest_path not in items:
    items.append(manifest_path)
with open(os.path.join(evi, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump({"files": sorted(items)}, f, indent=2)
PY

bash scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR" > "${EVI_DIR}/sha256sums.log" 2>&1

# 5) Bundle (include evi dir only)
tar -czf "$BUNDLE" "$EVI_DIR"

# 6) Pin + sidecar
BUNDLE_SHA="$(shasum -a 256 "$BUNDLE" | awk '{print $1}')"

cat > "$PIN" <<EOF2
P121_EXECUTION_WIRING_PROOF_DONE OK
timestamp_utc=${TS}
main_head=$(git rev-parse HEAD)
mode=${MODE}
dry_run=${DRY_RUN}
evi=${EVI_DIR}
bundle=${BUNDLE}
bundle_sha256=${BUNDLE_SHA}
EOF2

shasum -a 256 "$PIN" > "${PIN}.sha256"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"

echo "P121_DONE pin=${PIN} evi=${EVI_DIR} bundle=${BUNDLE}"
