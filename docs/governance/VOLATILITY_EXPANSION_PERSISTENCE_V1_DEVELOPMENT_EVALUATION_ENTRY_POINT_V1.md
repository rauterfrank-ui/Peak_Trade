# Volatility expansion persistence v1 — DEVELOPMENT evaluation entry point

## Status

`RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`

Executable development-evaluation path is present under the canonical entry point.
The single authorized development-evaluation run slot is consumed
(`development_run_count=1`, `runner_start_count=1`) after fail-closed
`UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:CHZ:USDT:USDT:perp:10575`
during productive PnL pairing. Retry is forbidden. Holdout remains unbound.

## Owner

`VOLATILITY_EXPANSION_PERSISTENCE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_expansion_persistence_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization; single bounded run slot is now consumed

## Bindings

- Strategy identity: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest (frozen after slot terminalization):
  `3718bb162de2af9f613638336a5bd093f977e610dc8dfcdb22621ec186623b86`
- Entry-point binding:
  `config&#47;research&#47;volatility_expansion_persistence_v1_development_evaluation_entry_point_binding_v1.json`
- Productive PnL evaluator (reused, not duplicated):
  `src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Panel execution boundary:
  `src&#47;research&#47;volatility_expansion_persistence_v1_development_evaluation_v1&#47;execution_boundary_v1.py`
- Lifecycle authority:
  `config&#47;research&#47;volatility_regime_hypothesis_backlog_v1.json`

## Time-segment binding (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments

## Explicit non-actions after this terminal slice

No retry, no threshold change, no result calibration, no Master-V2&#47;Double-Play&#47;risk&#47;sizing&#47;execution
mutation, no runtime activation, no holdout access. Economic&#47;promotion gates remain closed.
No second PnL truth.

## Next step

`NO_RETRY_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

## Explicitly false

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `EVALUATION_EXECUTED=false`
- `RUNNER_STARTED=true`
- `RUN_SLOT_CONSUMED=true`

---
docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_PERSISTENCE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT
scope: research, offline-only, fail-closed-evidence, run-slot-consumed
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
