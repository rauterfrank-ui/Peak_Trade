#!/usr/bin/env bash
set -euo pipefail

# P140 — Exec-Net Paper Evidence Pack v1 (networkless)
# Guards: paper/shadow only, DRY_RUN=YES required, transport_allow remains NO (default deny)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

MODE="${MODE:-paper}"
DRY_RUN="${DRY_RUN:-YES}"

if [[ "$MODE" != "paper" && "$MODE" != "shadow" ]]; then
  echo "DENY: MODE must be paper|shadow (got: $MODE)" >&2
  exit 2
fi

if [[ "$DRY_RUN" != "YES" ]]; then
  echo "DENY: DRY_RUN must be YES (got: $DRY_RUN)" >&2
  exit 2
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
EVI_DIR="out/ops/p140_paper_evidence_pack_${TS}"
export EVI_DIR

mkdir -p "$EVI_DIR"

REPORT_MARKETS="${EVI_DIR}/onramp_markets.json"
REPORT_ORDERBOOK="${EVI_DIR}/onramp_orderbook.json"
PYTEST_LOG="${EVI_DIR}/pytest.log"
MANIFEST="${EVI_DIR}/manifest.json"

# Run networked onramp CLI in read-only intents
set +e
python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" --intent markets --market BTC-USD --qty 0.01 > "$REPORT_MARKETS"
RC1=$?

python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" --intent orderbook --market BTC-USD --qty 0.01 > "$REPORT_ORDERBOOK"
RC2=$?
set -e

# We accept non-zero (e.g., allowlist disabled / denied) as long as JSON exists
test -s "$REPORT_MARKETS"
test -s "$REPORT_ORDERBOOK"

# Minimal smoke for this pack
python3 -m pytest -q tests/p140 -q | tee "$PYTEST_LOG"

# Manifest
python3 - <<'PY'
import json, os, time
evi = os.environ["EVI_DIR"]
manifest = {
  "version": "p140_exec_net_paper_evidence_pack_v1",
  "timestamp_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
  "mode": os.environ.get("MODE","paper"),
  "dry_run": os.environ.get("DRY_RUN","YES"),
  "artifacts": [
    "onramp_markets.json",
    "onramp_orderbook.json",
    "pytest.log",
  ],
}
with open(os.path.join(evi, "manifest.json"), "w", encoding="utf-8") as f:
  json.dump(manifest, f, indent=2, sort_keys=True)
PY

# SHA256SUMS (style-guarded)
bash scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR"

# Bundle + sidecars
tar -C "$(dirname "$EVI_DIR")" -czf "${EVI_DIR}.bundle.tgz" "$(basename "$EVI_DIR")"
shasum -a 256 "${EVI_DIR}.bundle.tgz" > "${EVI_DIR}.bundle.tgz.sha256"

# DONE pin
PIN="out/ops/P140_EXEC_NET_PAPER_EVI_DONE_${TS}.txt"
cat > "$PIN" <<EOF2
P140_EXEC_NET_PAPER_EVI_DONE OK
timestamp_utc=${TS}
mode=${MODE}
dry_run=${DRY_RUN}
evi=${EVI_DIR}
bundle=${EVI_DIR}.bundle.tgz
bundle_sha256=$(cut -d' ' -f1 "${EVI_DIR}.bundle.tgz.sha256")
EOF2
shasum -a 256 "$PIN" > "${PIN}.sha256"

echo "OK PIN=$PIN"
