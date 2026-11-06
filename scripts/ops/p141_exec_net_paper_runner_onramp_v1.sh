#!/usr/bin/env bash
set -euo pipefail

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

TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
export TS_UTC
EVI_DIR="out/ops/p141_exec_net_paper_runner_onramp_${TS_UTC}"
BUNDLE="out/ops/p141_exec_net_paper_runner_onramp_${TS_UTC}.bundle.tgz"
PIN="out/ops/P141_EXEC_NET_PAPER_RUNNER_ONRAMP_DONE_${TS_UTC}.txt"

mkdir -p "$EVI_DIR"
export EVI_DIR

python3 -m pytest -q tests/p140 tests/p141 > "${EVI_DIR}/pytest.log"

# Onramp calls: allow rc!=0 for allowlist-disabled paths, but capture output
python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" \
  --intent markets \
  --market BTC-USD \
  --qty 0.01 \
  > "${EVI_DIR}/onramp_markets.json" || true

python3 -m src.execution.networked.onramp_cli_v1 \
  --mode "$MODE" \
  --intent orderbook \
  --market BTC-USD \
  --qty 0.01 \
  > "${EVI_DIR}/onramp_orderbook.json" || true

python3 - <<'PY'
import json, os, pathlib, sys
evi = pathlib.Path(os.environ["EVI_DIR"])
def load(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

mk = load(evi/"onramp_markets.json") or {}
ob = load(evi/"onramp_orderbook.json") or {}

def get_path(d, path, default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

# best-effort asserts (schema may evolve)
for name, doc in [("markets", mk), ("orderbook", ob)]:
    mode = doc.get("mode") or get_path(doc, ["ctx","mode"])
    dry  = doc.get("dry_run") or get_path(doc, ["ctx","dry_run"])
    ta   = get_path(doc, ["meta","transport_allow"]) or get_path(doc, ["transport_gate","transport_allow"]) or get_path(doc, ["transport","transport_allow"])
    if mode and mode != "paper":
        print(f"ASSERT_FAIL: {name} mode={mode} expected paper", file=sys.stderr); sys.exit(3)
    if dry and str(dry) not in ("YES","True","true"):
        print(f"ASSERT_FAIL: {name} dry_run={dry} expected YES", file=sys.stderr); sys.exit(3)
    if ta and ta != "NO":
        print(f"ASSERT_FAIL: {name} transport_allow={ta} expected NO", file=sys.stderr); sys.exit(3)

manifest = {
  "ts_utc": os.environ.get("TS_UTC"),
  "mode": os.environ.get("MODE"),
  "dry_run": os.environ.get("DRY_RUN"),
  "evi_dir": str(evi),
  "artifacts": ["pytest.log","onramp_markets.json","onramp_orderbook.json","manifest.json","SHA256SUMS.txt"],
  "networkless": True
}
(evi/"manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
print("MANIFEST_OK", str(evi/"manifest.json"))
PY

# sha256 + bundle (sandbox-safe generator)
./scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR"
shasum -a 256 -c "${EVI_DIR}/SHA256SUMS.txt"

tar -czf "$BUNDLE" -C "$(dirname "$EVI_DIR")" "$(basename "$EVI_DIR")"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"
shasum -a 256 -c "${BUNDLE}.sha256"

cat > "$PIN" <<EOF2
P141_EXEC_NET_PAPER_RUNNER_ONRAMP_DONE OK
timestamp_utc=${TS_UTC}
mode=${MODE}
dry_run=${DRY_RUN}
evi=${EVI_DIR}
bundle=${BUNDLE}
bundle_sha256=$(cut -d' ' -f1 "${BUNDLE}.sha256")
EOF2
shasum -a 256 "$PIN" > "${PIN}.sha256"
shasum -a 256 -c "${PIN}.sha256"

echo "P141_DONE pin=${PIN}"
