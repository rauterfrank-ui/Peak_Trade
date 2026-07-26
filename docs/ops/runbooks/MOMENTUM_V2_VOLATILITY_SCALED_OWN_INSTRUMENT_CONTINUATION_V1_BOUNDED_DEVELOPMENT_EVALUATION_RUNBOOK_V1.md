# Runbook — Momentum V2 vol-scaled bounded Development evaluation (later GO)

## Current locked state

- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_SLOT_AVAILABLE=true`
- `DEVELOPMENT_RUN_SLOT_CONSUMED=false`
- `HOLDOUT_ALLOWED=false`
- `SEALED_ALLOWED=false`
- `PROMOTION_ALLOWED=false`
- `ACTIVATION_ALLOWED=false`

## Prepared command (DO NOT RUN without separate operator GO)

```bash
python scripts&#47;research&#47;run_evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1.py
```

Without the separate GO token
`GO_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1`
the runner must exit non-zero and must not consume the slot.

## One-shot rules

- Exactly one Development run allowed after future GO
- Retry forbidden after slot consumption
- Holdout &#47; Sealed remain forbidden
- No runtime &#47; scheduler &#47; orders

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOL_SCALED_BOUNDED_DEVELOPMENT_EVALUATION_RUNBOOK_V1
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
---
