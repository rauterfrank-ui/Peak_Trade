# P4C L2 Market Outlook – Golden Fixtures

Deterministic golden fixtures for regression testing of the L2 market outlook capsule runner.

| Fixture   | Regime   | no_trade | Reason(s)       |
|-----------|----------|----------|-----------------|
| baseline  | NEUTRAL  | false    | —               |
| high_vol  | HIGH_VOL | true     | VOL_EXTREME     |
| illiquid  | NEUTRAL  | true     | MISSING_FEATURES|

## Regenerate

```bash
python3 scripts/aiops/run_l2_market_outlook_capsule.py \
  --capsule tests/fixtures/p4c/capsule_baseline.json \
  --outdir tests/fixtures/p4c_l2_market_outlook/baseline \
  --run-id baseline --deterministic --evidence 0

python3 scripts/aiops/run_l2_market_outlook_capsule.py \
  --capsule tests/fixtures/p4c/capsule_high_vol.json \
  --outdir tests/fixtures/p4c_l2_market_outlook/high_vol \
  --run-id high_vol --deterministic --evidence 0

python3 scripts/aiops/run_l2_market_outlook_capsule.py \
  --capsule tests/fixtures/p4c/capsule_illiquid.json \
  --outdir tests/fixtures/p4c_l2_market_outlook/illiquid \
  --run-id illiquid --deterministic --evidence 0
```
