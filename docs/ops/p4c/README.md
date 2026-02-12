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
