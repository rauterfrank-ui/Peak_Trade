# Evaluate ADX DI direction confirmation MR eligibility holdout v1

```text
SLICE=EVALUATE_ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_V2
BASE_SHA=d039f346431fb0f4abc60da8f7ab112478c51c0d
HYPOTHESIS=ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2
RESULT_CLASS=FAIL
REASON=NET_PROFIT_FACTOR_NOT_IMPROVED
HOLDOUT_RUN_COUNT=1
HOLDOUT_RUN_LIMIT=1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1
DATASET_CLASS=SEALED_HOLDOUT_FINAL_AUDIT_ONLY
HOLDOUT_ACCESSED=true
SEALED_HOLDOUT_CONTENT_INSPECTED=true
PROMOTION_ELIGIBLE=false
ECONOMIC_VALIDITY_OFFLINE_GATE_CHANGED=false
RUNTIME_ACTIVATED=false
ORDERS_SENT=false
NO_POST_RESULT_TUNING=true
NO_RETRY=true
OPERATOR_HOLDOUT_GO=true
```

## Result (mechanical)

- Control trades: `303` -> Treatment trades: `204`
- Control net PF: `0.0` -> Treatment net PF: `0.0`
- Control net return: `-0.02567328065039287` -> Treatment: `-0.017336020979707656`
- Control max DD: `-0.025673280650392916` -> Treatment: `-0.01733602097970761`
- `entries_blocked_by_gate` (treatment): `328`
- Divergence observed: `True`

This is the single preregistered, execution-gated holdout run
(`holdout_run_limit=1`, `holdout_run_count_before=0`). The result is terminal:
no retry, no post-result tuning, no reopening without a new hypothesis id.
The economic offline gate remains closed and no runtime/orders are affected
regardless of `RESULT_CLASS`.

## Command (single authorized run)

```bash
PYTHONPATH=src:. PEAK_TRADE_ADX_DI_HOLDOUT_V2_EXECUTION_GO=true python3 scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2.py \
  --output-dir docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v2
```
