# Evaluate ADX DI direction confirmation MR eligibility development v1

```text
SLICE=EVALUATE_ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_DEVELOPMENT_V1
BASE_SHA=d8ddca59280402df6116810953ca6d2dcb6454c0
BRANCH=research/evaluate-adx-di-direction-confirmation-mr-development-v1
HYPOTHESIS=ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
RESULT_CLASS=PASS
REASON=ALL_PASS_REQUIRES_MET
EVALUATION_RUN_COUNT=1
EVALUATION_RUN_LIMIT=1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
HOLDOUT_ACCESSED=false
PROMOTION_ELIGIBLE=false
ECONOMIC_GATE_OPENED=false
RUNTIME_ACTIVATED=false
ORDERS_SENT=false
NO_POST_RESULT_TUNING=true
NO_RETRY=true
```

## Result (mechanical)

- Control trades: `117` → Treatment trades: `100`
- Control net PF: `0.732436` → Treatment net PF: `0.810055`
- Control net return: `-0.003597` → Treatment: `-0.002299`
- Control max DD: `-0.013820` → Treatment: `-0.011062`
- `entries_blocked_by_gate` (treatment): `256`
- Divergence observed: `true`

PASS does **not** open the economic offline gate and does **not** activate any strategy/runtime.

## Command (single authorized run; already executed)

```bash
PYTHONPATH=src:. python3 scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1.py \
  --output-dir docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1
```
