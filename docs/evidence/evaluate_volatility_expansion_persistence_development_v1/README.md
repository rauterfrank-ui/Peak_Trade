# Evaluate volatility expansion persistence development v1 — terminal FAIL_CLOSED

```text
SLICE=EVALUATE_VOLATILITY_EXPANSION_PERSISTENCE_DEVELOPMENT_V1
BASE_SHA=2eb034bc1c6c7e5a165f24e8fe25ba40b0d0bc41
STRATEGY_ID=VOLATILITY_EXPANSION_PERSISTENCE_V1
BASELINE_ID=UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
STATUS=FAIL_CLOSED
REASON=UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:CHZ:USDT:USDT:perp:10575
EVALUATION_EXECUTED=false
RUNNER_STARTED=true
CLI_REPORTED_RUNNER_STARTED=false
DEVELOPMENT_DATASET_LOADED=true
RUN_BUDGET_CONSUMED=true
EVALUATION_RUN_COUNT=1
RUNNER_START_COUNT=1
HOLDOUT_ACCESSED=false
RETRY_FORBIDDEN=true
PREREGISTERED_GATES=NOT_EVALUATED
PRODUCTIVE_EXIT_PNL_EVALUATOR_BOUND=true
PRODUCTIVE_PNL_EVALUATOR_REUSED=true
SECOND_PNL_TRUTH_CREATED=false
```

## Exact command (single authorized attempt; budget consumed)

```bash
python3 scripts/research/run_evaluate_volatility_expansion_persistence_development_v1.py --mode evaluate --authorize-single-development-evaluation VOLATILITY_EXPANSION_PERSISTENCE_NON_BITCOIN_PERPETUALS_V1
```

Authorized single development-evaluation attempt on `2eb034bc1c6c7e5a165f24e8fe25ba40b0d0bc41` entered the
evaluate path with the panel execution boundary and productive exit/PnL evaluator
bound, then fail-closed with `UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:CHZ:USDT:USDT:perp:10575` during productive PnL pairing.
No retry. Acceptance criteria were not evaluated.

Prior historical note: `fail_closed_report.json` records an earlier
panel-boundary-not-materialized fail-closed on `c3479e0b...` that did **not**
consume the durable run slot.

---
docs_token: DOCS_TOKEN_EVALUATE_VOLATILITY_EXPANSION_PERSISTENCE_DEVELOPMENT_V1_FAIL_CLOSED_UNPAIRABLE_ENTRY
STATUS: FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT
scope: research, offline-only, terminal-development-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
