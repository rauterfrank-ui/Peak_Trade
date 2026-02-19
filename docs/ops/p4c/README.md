# P4C — L2 Market Outlook

This folder contains P4C-specific notes and (later) the definitive documentation for:
- Regime scenarios
- NO-TRADE triggers
- Evidence pack format

See: `docs/ops/p4c/P4C_TODO.md` for the working checklist.

## Runner (Capsule) usage

Generate outlook (and evidence manifest by default):

```bash
python3 scripts/aiops/run_l2_market_outlook_capsule.py \
  --capsule tests/fixtures/p4c/capsule_min_v0.json \
  --outdir out/ops/p4c/demo_run \
  --evidence 1 \
  --dry-run
```

Deterministic run (CI/testing):

```bash
python3 scripts/aiops/run_l2_market_outlook_capsule.py \
  --capsule tests/fixtures/p4c/capsule_min_v0.json \
  --outdir out/ops/p4c/demo_run \
  --run-id fixed \
  --deterministic \
  --evidence 1
```

## Evidence Pack workflow (L2 transcript → pack → validate)

Run a fresh P4C L2 run, generate evidence pack, validate:

```bash
set -euo pipefail
ts=$(date -u +"%Y%m%dT%H%M%SZ")
outdir="out/ops/p4c_runs/${ts}"
mkdir -p "$outdir"

# 1) Run L2 Market Outlook (replay mode, deterministic)
PYTHONPATH=. python3 scripts/aiops/run_l2_market_outlook.py \
  --mode replay \
  --fixture l2_market_outlook_sample \
  --out "$outdir" \
  --deterministic \
  --notes "p4c evidence run ${ts}"

# 2) Generate evidence pack (--in must be full path under base-dir)
python3 scripts/aiops/generate_evidence_pack.py \
  --base-dir out/ops \
  --in "out/ops/p4c_runs/${ts}" \
  --out-root out/ops/evidence_packs \
  --pack-id "p4c_${ts}" \
  --deterministic

# 3) Validate evidence pack
manifest=$(ls -1t out/ops/evidence_packs/*/manifest.json | head -n 1)
python3 scripts/aiops/validate_evidence_pack.py --manifest "$manifest"
# Exit 0: VALIDATION_OK
```
