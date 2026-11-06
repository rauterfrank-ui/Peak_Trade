#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Generate a deterministic pack from the fixture and validate it.
OUT_ROOT="out/ops/evidence_packs_ci_smoke"
rm -rf "$OUT_ROOT"
mkdir -p "$OUT_ROOT"

python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir "$(git rev-parse --show-toplevel)" \
  --in tests/fixtures/p5b/sample_dir \
  --pack-id ci_smoke \
  --out-root "$OUT_ROOT" \
  --deterministic >/tmp/p5b_pack_paths.txt

MANIFEST="$(sed -n '1p' /tmp/p5b_pack_paths.txt)"
python3 scripts/aiops/validate_evidence_pack.py --manifest "$MANIFEST"
