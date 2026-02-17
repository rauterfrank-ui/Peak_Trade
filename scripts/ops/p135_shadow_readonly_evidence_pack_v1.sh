#!/usr/bin/env bash
set -euo pipefail

# P135 — shadow read-only evidence pack (networkless)
# Guards: shadow|paper, DRY_RUN=YES, deny secrets/live env
MODE="${MODE:-shadow}"
DRY_RUN="${DRY_RUN:-YES}"

case "$MODE" in shadow|paper) :;; *) echo "P135_GUARD_FAIL mode_invalid=$MODE" >&2; exit 3;; esac
if [ "$DRY_RUN" != "YES" ]; then echo "P135_GUARD_FAIL dry_run_must_be_yes" >&2; exit 3; fi

# deny-list (minimal)
DENY_ENV_REGEX='^(LIVE|RECORD|TRADING_ENABLE|PT_ARMED|PT_ENABLED|API_KEY|API_SECRET|APIKEY|APISECRET|KRAKEN_|COINBASE_|OKX_|BYBIT_)'
if env | cut -d= -f1 | grep -Eq "$DENY_ENV_REGEX"; then
  echo "P135_GUARD_FAIL denied_env_present" >&2
  env | cut -d= -f1 | grep -E "$DENY_ENV_REGEX" >&2 || true
  exit 3
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

TS="$(date -u +"%Y%m%dT%H%M%SZ")"
EVI_DIR="out/ops/p135_shadow_readonly_evidence_pack_${TS}"
BUNDLE="${EVI_DIR}.bundle.tgz"
PIN="out/ops/P135_EXEC_NET_SHADOW_READONLY_EVI_DONE_${TS}.txt"

mkdir -p "$EVI_DIR"

# 1) smoke (keep tight + networkless)
python3 -m pytest -q tests/p124 tests/p125 tests/p126 tests/p127 tests/p128 tests/p129 tests/p130 tests/p131 -q > "${EVI_DIR}/pytest.log"

# 2) read-only intents via onramp CLI (transport_allow stays NO by design)
# markets
python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" --intent markets --market BTC-USD --qty 0.01 \
  > "${EVI_DIR}/onramp_markets.json" || true

# orderbook
python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" --intent orderbook --market BTC-USD --qty 0.01 \
  > "${EVI_DIR}/onramp_orderbook.json" || true

# 3) assertions (networkless)
grep -q '"transport_allow"[[:space:]]*:[[:space:]]*"NO"' "${EVI_DIR}/onramp_markets.json"
grep -q '"transport_allow"[[:space:]]*:[[:space:]]*"NO"' "${EVI_DIR}/onramp_orderbook.json"

# 4) manifest + sha256sums (repo-root-relative, no xargs)
export EVI_DIR
python3 - <<'PY'
import json, os, pathlib
evi = pathlib.Path(os.environ["EVI_DIR"])
files = []
for p in sorted(evi.rglob("*")):
    if p.is_file():
        files.append(str(p))
(evi/"manifest.json").write_text(json.dumps({"files": files}, indent=2) + "\n", encoding="utf-8")
PY
bash scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR"

# 5) bundle + sidecars
tar -czf "$BUNDLE" "$EVI_DIR"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"

# 6) pin + pin sidecar
cat > "$PIN" <<EOF2
P135_EXEC_NET_SHADOW_READONLY_EVI_DONE OK
timestamp_utc=${TS}
main_head=$(git rev-parse HEAD)
mode=${MODE}
dry_run=${DRY_RUN}
evi=${EVI_DIR}
bundle=${BUNDLE}
bundle_sha256=$(cut -d' ' -f1 "${BUNDLE}.sha256")
EOF2
shasum -a 256 "$PIN" > "${PIN}.sha256"

echo "P135_DONE pin=${PIN}"
