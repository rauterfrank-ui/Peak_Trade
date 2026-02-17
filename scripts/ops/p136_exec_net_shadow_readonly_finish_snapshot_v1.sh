#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-$(pwd)}"
cd "$ROOT"

ts_utc="$(date -u +%Y%m%dT%H%M%SZ)"

MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"

# hard guards
if [[ "$MODE" != "shadow" && "$MODE" != "paper" ]]; then
  echo "P136_GUARD_FAIL: bad_mode=$MODE" >&2
  exit 3
fi
if [[ "$DRY_RUN" != "YES" ]]; then
  echo "P136_GUARD_FAIL: dry_run_must_be_yes" >&2
  exit 3
fi

# deny env (minimal, keep aligned with existing patterns)
DENY_ENV_RE='(^| )(LIVE|RECORD|TRADING_ENABLE|PT_ARMED|PT_ENABLED|PT_CONFIRM|API_KEY|API_SECRET|API_TOKEN|COINBASE_|KRAKEN_|OKX_|BYBIT_)'
if env | grep -Eqi "$DENY_ENV_RE"; then
  echo "P136_GUARD_FAIL: deny_env_present" >&2
  env | grep -Ei "$DENY_ENV_RE" >&2 || true
  exit 3
fi

EVI_DIR="out/ops/p136_exec_net_shadow_readonly_finish_snapshot_${ts_utc}"
BUNDLE="out/ops/p136_exec_net_shadow_readonly_finish_snapshot_${ts_utc}.bundle.tgz"
PIN="out/ops/P136_EXEC_NET_SHADOW_READONLY_FINISH_SNAPSHOT_DONE_${ts_utc}.txt"

mkdir -p "$EVI_DIR"

# 1) pytest (only relevant suites)
python3 -m pytest -q tests/p124 tests/p125 tests/p126 tests/p127 tests/p128 tests/p129 tests/p130 tests/p131 tests/p133 -q > "${EVI_DIR}/pytest.log"

# 2) smokes (read-only intents)
# allowlist disabled by default; CLI may return rc=2; keep JSON output anyway
python3 -m src.execution.networked.onramp_cli_v1 --mode "$MODE" --intent markets --market BTC-USD --qty 0.01 > "${EVI_DIR}/onramp_markets.json" || true
python3 -m src.execution.networked.onramp_cli_v1 --mode "$MODE" --intent orderbook --market BTC-USD --qty 0.01 > "${EVI_DIR}/onramp_orderbook.json" || true

# 3) assertions (networkless, default deny is expected)
grep -Eq '"transport_allow"[[:space:]]*:[[:space:]]*"NO"' "${EVI_DIR}/onramp_markets.json"
grep -Eq '"transport_allow"[[:space:]]*:[[:space:]]*"NO"' "${EVI_DIR}/onramp_orderbook.json"

# 4) manifest + sha256sums (+ style guard auto-called by generator)
export EVI_DIR
python3 - <<'PY'
import json
import os

evi = os.environ["EVI_DIR"]
files = []
for root, _, fnames in os.walk(evi):
    for f in fnames:
        p = os.path.join(root, f)
        files.append(p)
files = sorted(files)
with open(os.path.join(evi, "manifest.json"), "w", encoding="utf-8") as fp:
    json.dump({"evi_dir": evi, "files": files}, fp, indent=2)
PY
bash scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR"

# 5) bundle (include evi only; paths in SHA256SUMS are repo-root-relative)
tar -czf "$BUNDLE" "$EVI_DIR"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"

# 6) pin + pin sha
cat > "$PIN" <<EOF2
P136_EXEC_NET_SHADOW_READONLY_FINISH_SNAPSHOT_DONE OK
timestamp_utc=${ts_utc}
mode=${MODE}
dry_run=${DRY_RUN}
main_head=$(git rev-parse HEAD)
evi=${EVI_DIR}
bundle=${BUNDLE}
bundle_sha256=$(shasum -a 256 "$BUNDLE" | awk '{print $1}')
EOF2
shasum -a 256 "$PIN" > "${PIN}.sha256"

echo "P136_DONE pin=${PIN}"
