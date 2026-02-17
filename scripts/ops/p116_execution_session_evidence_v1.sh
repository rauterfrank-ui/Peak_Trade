#!/usr/bin/env bash
set -euo pipefail

MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"
ADAPTERS="${ADAPTERS:-mock,coinbase,okx,bybit}"
INTENTS="${INTENTS:-place_order,cancel_all}"
ROOT="${ROOT:-$(pwd)}"
OPS_DIR="${OPS_DIR:-$ROOT/out/ops}"

deny_vars=(LIVE RECORD TRADING_ENABLE EXECUTION_ENABLE PT_ARMED PT_CONFIRM_TOKEN KRAKEN_API_KEY BINANCE_API_KEY COINBASE_API_KEY OKX_API_KEY BYBIT_API_KEY API_KEY API_SECRET)
for v in "${deny_vars[@]}"; do
  if [[ -n "${!v:-}" ]]; then
    echo "P116_GUARD_FAIL deny_env_var=$v" >&2
    exit 3
  fi
done

if [[ "$MODE" != "shadow" && "$MODE" != "paper" ]]; then
  echo "P116_GUARD_FAIL mode_invalid=$MODE" >&2
  exit 3
fi
if [[ "$DRY_RUN" != "YES" ]]; then
  echo "P116_GUARD_FAIL dry_run_must_be_yes=$DRY_RUN" >&2
  exit 3
fi

ts="$(date -u +%Y%m%dT%H%M%SZ)"
evi="$OPS_DIR/p116_execution_session_${ts}"
pin="$OPS_DIR/P116_EXECUTION_SESSION_DONE_${ts}.txt"
bundle="$evi.bundle.tgz"

mkdir -p "$evi"

# run session (python) -> report.json
python3 - <<PY
import json
from pathlib import Path
from src.execution.session.runner_v1 import ExecutionSessionContextV1, run_execution_session_v1

ctx = ExecutionSessionContextV1(
    mode="${MODE}",
    dry_run=True,
    adapters=tuple(a.strip() for a in "${ADAPTERS}".split(",") if a.strip()),
    intents=tuple(i.strip() for i in "${INTENTS}".split(",") if i.strip()),
)
rep = run_execution_session_v1(ctx)
# Copy full report from runner's evi_dir to our evi
runner_report = Path(rep["evi_dir"]) / "report.json"
our_evi = Path("${evi}")
our_evi.mkdir(parents=True, exist_ok=True)
with open(runner_report, encoding="utf-8") as f:
    report_data = json.load(f)
with open(our_evi / "report.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2, sort_keys=True)
print("P116_OK report=${evi}/report.json")
PY

# manifest + sha
python3 - <<PY
import hashlib
import json
import os

root = "${ROOT}"
evi = "${evi}"
evi_basename = os.path.basename(evi)

with open(os.path.join(evi, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump({"files": ["report.json"]}, f, indent=2, sort_keys=True)

sha_lines = []
for fname in ["report.json", "manifest.json"]:
    p = os.path.join(evi, fname)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    sha_lines.append(f"{h}  {fname}")
with open(os.path.join(evi, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(sha_lines) + "\n")
print("P116_SHA_OK")
PY

tar -czf "$bundle" -C "$ROOT" "out/ops/$(basename "$evi")"
bundle_sha="$(shasum -a 256 "$bundle" | awk '{print $1}')"

cat > "$pin" <<EOF
P116_EXECUTION_SESSION_DONE OK
timestamp_utc=$ts
main_head=$(git rev-parse HEAD)
mode=$MODE
dry_run=$DRY_RUN
evi=$evi
bundle=$bundle
bundle_sha256=$bundle_sha
EOF

shasum -a 256 "$pin" > "${pin}.sha256"
shasum -a 256 "$bundle" > "${bundle}.sha256"

echo "P116_DONE pin=$pin evi=$evi bundle=$bundle"
