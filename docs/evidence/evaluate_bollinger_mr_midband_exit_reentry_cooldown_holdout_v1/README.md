# Evaluate Exit V8 holdout v1

```text
SLICE=EVALUATE_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1
BASE_SHA=4e766d0c47082a8c0342165e5b4c84c31110a405
HYPOTHESIS=BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1
RESULT_CLASS=FAIL
REASON=NET_PROFIT_FACTOR_NOT_IMPROVED
HOLDOUT_RUN_COUNT=1
HOLDOUT_RUN_LIMIT=1
RUNNER_START_COUNT=1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1
DATASET_CLASS=SEALED_HOLDOUT_FINAL_AUDIT_ONLY
PANEL_ID=offline_economic_reevaluation_sealed_long_panel_v1
CONTRACT_DIGEST=a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d
HOLDOUT_ACCESSED=true
SEALED_HOLDOUT_CONTENT_INSPECTED=true
PROMOTION_ELIGIBLE=false
ECONOMIC_GATE_OPEN=false
RUNTIME_ACTIVATED=false
ORDERS_SENT=false
NO_POST_RESULT_TUNING=true
NO_RETRY=true
OPERATOR_HOLDOUT_GO=true
SECOND_RUN_STARTED=false
```

## Result (mechanical)

- Control trades: `1024` -> Treatment trades: `659`
- Control net PF: `0.5774036019332512` -> Treatment net PF: `0.5280135615083571`
- Control net return: `-0.01687539597330001` -> Treatment: `-0.012197023845878951`
- Control max DD: `-0.016999236945931404` -> Treatment: `-0.012221591890570134`
- Control cost_drag: `6019.810565567809` -> Treatment: `3919.4833842451008`
- Control short_trade_count: `1005` -> Treatment: `642`

This is the single preregistered, execution-gated holdout run
(`holdout_run_limit=1`, `holdout_run_count_before=0`, `runner_start_count=1`).
The result is terminal: no retry, no post-result tuning, no reopening without a
new hypothesis id. The economic offline gate remains closed and no runtime/orders
are affected regardless of `RESULT_CLASS`. V7/V8 development terminals are unchanged.

## Command (single authorized run)

```bash
PYTHONPATH=src:. \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_EXECUTION_GO=true \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_HEAD_SHA=<repo_HEAD> \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_CONTRACT_DIGEST=a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_DATASET_ID=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1 \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_PANEL_ID=offline_economic_reevaluation_sealed_long_panel_v1 \
PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_SUCCESSOR_ID=BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1 \
python3 scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1.py
```
