#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

run_id="${PT_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
export PT_RUN_ID="$run_id"

python3 scripts/aiops/run_prj_features_smoke.py
out_base="out/ops/prj_smoke/${run_id}"

# Evidence pack (base-dir = out/ops for portable relpaths in artifact)
python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir "out/ops" \
  --in "out/ops/prj_smoke/${run_id}" \
  --pack-id "prj_smoke_${run_id}" \
  --out-root "out/ops/evidence_packs" \
  --deterministic

manifest="out/ops/evidence_packs/pack_prj_smoke_${run_id}/manifest.json"
python3 scripts/aiops/validate_evidence_pack.py --manifest "$manifest"

echo "PRJ_SMOKE_OUT_BASE=${out_base}"
echo "PRJ_SMOKE_MANIFEST=${manifest}"
