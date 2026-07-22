# Evaluate volatility compression breakout development v1 — terminal FAIL_CLOSED

```text
SLICE=EVALUATE_VOLATILITY_COMPRESSION_BREAKOUT_DEVELOPMENT_V1
BASE_SHA=cb0f7997e07f72a37c4ca3c7f125532709f6fe85
STRATEGY_ID=VOLATILITY_COMPRESSION_BREAKOUT_V1
BASELINE_ID=UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
STATUS=FAIL_CLOSED
REASON=UNEXPECTED:OverflowError:(34, 'Result too large')
EVALUATION_EXECUTED=false
RUNNER_STARTED=true
CLI_REPORTED_RUNNER_STARTED=false
RUN_BUDGET_CONSUMED=true
EVALUATION_RUN_COUNT=1
RUNNER_START_COUNT=1
HOLDOUT_ACCESSED=false
RETRY_FORBIDDEN=true
PREREGISTERED_GATES=NOT_EVALUATED
PRODUCTIVE_EXIT_PNL_EVALUATOR_BOUND=true
```

## Exact command (single authorized attempt; budget consumed)

```bash
python3 scripts/research/run_evaluate_volatility_compression_breakout_development_v1.py --mode evaluate --authorize-single-development-evaluation VOLATILITY_COMPRESSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1
```

Authorized single development-evaluation attempt on `cb0f7997e07f72a37c4ca3c7f125532709f6fe85` entered the
evaluate path with the productive exit/PnL evaluator bound, then fail-closed
with `UNEXPECTED:OverflowError:(34, 'Result too large')` during productive PnL/metrics materialization. No retry.

Prior historical note: `fail_closed_report.json` records an earlier unbound-evaluator
fail-closed on `9b6be6a3...` that did **not** consume the durable run slot.

---
docs_token: DOCS_TOKEN_EVALUATE_VOLATILITY_COMPRESSION_BREAKOUT_DEVELOPMENT_V1_FAIL_CLOSED_OVERFLOW
STATUS: FAIL_CLOSED_PRODUCTIVE_PNL_OVERFLOW
scope: research, offline-only, terminal-development-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
