# Volatility compression breakout v1 — DEVELOPMENT evaluation entry point

## Status

`EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED`

Executable development-evaluation path is present under the canonical entry point.
Development evaluation remains unauthorized (`development_evaluation_authorized=false`).
No development evaluation executed. Run counts remain `0`.

## Owner

`VOLATILITY_COMPRESSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_compression_breakout_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization (token **and** repo flags); fail-closed on HEAD

## Bindings

- Strategy identity: `VOLATILITY_COMPRESSION_BREAKOUT_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest (frozen):
  `3b9e65121dd359742b427f3fba6aab18622858aca93e2f5400e617c8cbbcf069`
- Entry-point binding:
  `config&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_entry_point_binding_v1.json`
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Lifecycle authority:
  `config&#47;research&#47;volatility_regime_hypothesis_backlog_v1.json`

## Time-segment binding (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments

## Explicit non-actions in this slice

No evaluation run, no authorization flip, no dataset load, no holdout access, no retry,
no threshold change, no result calibration, no Master-V2/Double-Play/risk/sizing/execution
mutation, no runtime activation. Economic/promotion gates remain closed.

## Next step

`SEPARATE_OPERATOR_GO_FOR_DEVELOPMENT_EVALUATION_AUTHORIZATION`

## Explicitly false

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `EVALUATION_EXECUTED=false`
- `RUNNER_STARTED=false`

---
docs_token: DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED
scope: research, offline-only, non-authorizing, entry-point-infrastructure
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
