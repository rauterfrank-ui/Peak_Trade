# Volatility decay breakout with explicit decay exit v1 — DEVELOPMENT evaluation entry point

## Status

`RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`

Executable development-evaluation path is present under the canonical entry point.
The single authorized development-evaluation run slot is consumed
(`development_run_count=1`, `runner_start_count=1`) after fail-closed
`UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:AGLD:USDT:USDT:perp:10575`
during productive PnL pairing. Retry is forbidden. Holdout remains unbound.

## Owner

`VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts/research/run_evaluate_volatility_decay_breakout_with_explicit_decay_exit_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization; consumes the single run slot only
  after the productive evaluator begins on a fully materialized DEVELOPMENT panel

## Bindings

- Strategy identity: `VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1`
- Predecessor: `VOLATILITY_DECAY_BREAKOUT_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest:
  `a49b13ecf9047fb1557537fcdd44bd1dc76359985c579048bf39c99436522434`
  (auth + durable run-counter/slot fields only; hypothesis parameters unchanged from preregistration)
- Entry-point binding:
  `config/research/volatility_decay_breakout_with_explicit_decay_exit_v1_development_evaluation_entry_point_binding_v1.json`
- Exit state machine (strategy-owned):
  `src/research/volatility_decay_breakout_with_explicit_decay_exit_v1_exit_state_machine_v1.py`
- Productive PnL evaluator (reused, not duplicated):
  `src/research/volatility_compression_breakout_v1_development_evaluation_v1/productive_exit_pnl_evaluator_v1.py`
- Treatment exits: strategy-emitted only (`SIGNAL_EXIT` included); evaluator reconstruction forbidden
- Baseline exits: shared declarative productive path (identical cost/sizing/portfolio semantics)
- Portfolio aggregation: `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`
- Shared channel core: `src/research/price_channel_breakout_core_v1.py`
- Lifecycle authority:
  `config/research/volatility_regime_hypothesis_backlog_v1.json`

## Time-segment binding (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments

## Explicit non-actions

No holdout access, no Shadow/Testnet/Live/scheduler/orders, no second PnL/equity/stats truth,
no evaluator-side reconstruction of missing strategy exits, no hypothesis/parameter mutation,
no predecessor artifact mutation, no Master-V2/Double-Play/risk/sizing/execution mutation.

## Next step

`NO_RETRY_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

## Explicitly false / post-execution counters

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `DEVELOPMENT_EVALUATION_EXECUTED=true` (slot attempt executed; gate metrics NOT_EXECUTED)
- `DEVELOPMENT_RUN_COUNT=1`
- `RUNNER_START_COUNT=1`
- `SECOND_PNL_TRUTH_CREATED=false`

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT
scope: research, offline-only, development-evaluation-entry-point, run-slot-consumed
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
