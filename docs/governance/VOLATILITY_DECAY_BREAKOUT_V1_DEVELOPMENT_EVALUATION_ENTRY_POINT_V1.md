# Volatility decay breakout v1 — DEVELOPMENT evaluation entry point

## Status

`RUN_SLOT_CONSUMED_FAIL_CLOSED_PRODUCTIVE_PNL_OVERFLOW`

Executable development-evaluation path and panel execution boundary are present.
The single authorized evaluate attempt fail-closed during productive PnL/metrics
materialization with `UNEXPECTED:OverflowError:(34, 'Result too large')`.
Durable run slot consumed (`DEVELOPMENT_RUN_COUNT=1`, `RUNNER_START_COUNT=1`).
No retry.

## Owner

`VOLATILITY_DECAY_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_decay_breakout_development_v1.py`

## Bindings

- Strategy identity: `VOLATILITY_DECAY_BREAKOUT_V1`
- Previous strategy: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Measurement contract digest:
  `2d0922f0bf4a2082a032320f1a03316012682ea4021a1677e30c481fa620590c`
- Productive PnL evaluator (reused):
  `src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`
- Terminal evidence: `docs&#47;evidence&#47;evaluate_volatility_decay_breakout_development_v1&#47;summary.json`
- Archival panel-boundary report retained:
  `docs&#47;evidence&#47;evaluate_volatility_decay_breakout_development_v1&#47;fail_closed_report.json`

## Next step

`NO_RETRY_SLOT_CONSUMED_FAIL_CLOSED_PRODUCTIVE_PNL_OVERFLOW_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

## Explicitly false

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `RETRY_FORBIDDEN=true`
- `EVALUATION_EXECUTED=false` (metrics incomplete; overflow before gate evaluation)
- `RUNNER_STARTED=true`
- `RUN_SLOT_CONSUMED=true`

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: RUN_SLOT_CONSUMED_FAIL_CLOSED_PRODUCTIVE_PNL_OVERFLOW
scope: research, offline-only, terminal-development-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
