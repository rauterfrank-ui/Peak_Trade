# Volatility compression breakout v1 — DEVELOPMENT evaluation entry point

## Status

`EXECUTABLE_EVALUATE_PATH_PRESENT_RUN_SLOT_CONSUMED_FAIL_CLOSED`

Executable development-evaluation path is present under the canonical entry point.
The single authorized development-evaluation run slot is consumed
(`development_run_count=1`, `runner_start_count=1`) after fail-closed
`UNEXPECTED:OverflowError:(34, 'Result too large')` during productive PnL/metrics.
Retry is forbidden. Holdout remains unbound.

## Owner

`VOLATILITY_COMPRESSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_compression_breakout_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization; run slot already consumed — retry rejected

## Bindings

- Strategy identity: `VOLATILITY_COMPRESSION_BREAKOUT_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest (counters/slot fields updated after terminal run):
  `7a4ba7b765a7e7cc16155cb77b1448536b79a5416e2d758039a5574a82a74519`
- Entry-point binding:
  `config&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_entry_point_binding_v1.json`
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Lifecycle authority:
  `config&#47;research&#47;volatility_regime_hypothesis_backlog_v1.json`

## Time-segment binding (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments

## Explicit non-actions after terminalization

No retry, no holdout access, no threshold change, no result calibration,
no Master-V2/Double-Play/risk/sizing/execution mutation, no runtime activation.
Economic/promotion gates remain closed.

## Next step

`NO_RETRY_SLOT_CONSUMED_FAIL_CLOSED_OVERFLOW_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

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
docs_token: DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: EXECUTABLE_EVALUATE_PATH_PRESENT_RUN_SLOT_CONSUMED_FAIL_CLOSED
scope: research, offline-only, terminal-development-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
