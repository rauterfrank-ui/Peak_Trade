# Cross-sectional short-horizon return reversal v1 — DEVELOPMENT evaluation

## Status

`DEVELOPMENT_FAIL` after exactly one authorized bounded DEVELOPMENT evaluation.
Run slot consumed. Retry forbidden.

## Binding

- Scope: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1`
- Hypothesis: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Entry-point binding: `config/research/cross_sectional_short_horizon_return_reversal_v1_development_evaluation_entry_point_binding_v1.json`
- Evidence: `docs/evidence/evaluate_cross_sectional_short_horizon_return_reversal_development_v1/`
- CLI: `scripts/research/run_evaluate_cross_sectional_short_horizon_return_reversal_development_v1.py`

## Frozen treatment

- Score: negated trailing log return, lookback_N=24, rebalance=4, lag=1
- Selection: `single_top1_by_score_desc` + `symmetric_top1_sign`
- No parameter optimization; single frozen point; no grid

## Outcome gates (preregistered)

Joint admission failed (`DEVELOPMENT_FAIL`). Economic gate remains closed. Holdout
untouched. No promotion, runtime, orders, shadow, or testnet activation.
Activation remains ineligible.

## Next step

`RETURN_TO_OPERATOR_FOR_EXACT_HEAD_FORENSIC_REVIEW; NO_HOLDOUT_OR_SEALED_EVALUATION_WITHOUT_NEW_EXPLICIT_GO`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: DEVELOPMENT_FAIL_SLOT_CONSUMED
scope: research, offline-only, non-authorizing, development-evaluation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
