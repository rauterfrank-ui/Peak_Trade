# Runbook — Momentum V2 vol-scaled Development evaluation (executed)

## Locked terminal state

- `DEVELOPMENT_EVALUATION_AUTHORIZED=true` (historical GO consumed)
- `DEVELOPMENT_RUN_SLOT_AVAILABLE=false`
- `DEVELOPMENT_RUN_SLOT_CONSUMED=true`
- `DEVELOPMENT_RUN_COUNT=1`
- `DEVELOPMENT_VERDICT=DEVELOPMENT_FAIL`
- `ECONOMIC_VALIDITY=FAIL`
- `HOLDOUT_ALLOWED=false`
- `SEALED_ALLOWED=false`
- `PROMOTION_ALLOWED=false`
- `ACTIVATION_ALLOWED=false`

## Executed command (do not rerun)

```bash
python3 scripts/research/run_evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1.py \
  --mode evaluate \
  --authorize-single-development-evaluation MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1
```

Retry forbidden. Holdout/Sealed remain forbidden.

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOL_SCALED_BOUNDED_DEVELOPMENT_EVALUATION_RUNBOOK_V1
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
---
