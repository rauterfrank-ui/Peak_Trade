# Cross-sectional relative-strength momentum v1 — DEVELOPMENT evaluation entry point

## Status

`EXECUTABLE_EVALUATE_PATH_PRESENT_DEVELOPMENT_EVALUATION_AUTHORIZED`

Executable development-evaluation path is present under the canonical entry point.
Development evaluation is authorized (`development_evaluation_authorized=true`); execution still requires a separate operator GO and has not run.
No development evaluation executed. Run counts remain `0`.

## Owner

`CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts/research/run_evaluate_cross_sectional_relative_strength_momentum_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization (token **and** repo flags)

## Bindings

- Strategy identity: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Measurement contract digest (frozen):
  `54a6e4222ecb286a579780c53dddf509f2308f3b997ebef9e3a123a95ae1c3ed`
- Entry-point binding:
  `config/research/cross_sectional_relative_strength_momentum_v1_development_evaluation_entry_point_binding_v1.json`
- Lifecycle authority:
  `config/research/material_different_cross_sectional_momentum_hypothesis_backlog_v1.json`

## Reused canonical owners (no second metrics truth)

- Score/selection: already-merged CS RS momentum v1 modules
- Backtest/PnL metrics: `src.research.cross_sectional_single_slot_backtest_wiring_v0`
- Stats: `src.backtest.stats`
- Economic validity policy: `src.backtest.economic_validity_policy_v1`
- DEVELOPMENT panel resolve/hash:
  `src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1`

## Time-segment / sample guards (preregistered, unchanged)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Exactly 4 chronological equal-duration quarters; remainder to earliest segments
- Valid rebalance observations = evaluable rebalance timestamps only (not trades/bars/instruments)
- `minimum_rebalance_observations=30`
- `minimum_passing_segments=2` / `time_segment_robustness_pass_ratio=0.5`

## Explicit non-actions in this slice

No evaluation run, no holdout access, no retry, no threshold change, no result
calibration, no Master-V2/Double-Play/risk/sizing/execution/runtime activation,
economic/promotion gates remain closed. Development evaluation authorization is true; evaluation not executed.

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_THEN_EXECUTE_EXACTLY_ONE_PREVIOUSLY_AUTHORIZED_BOUNDED_DEVELOPMENT_EVALUATION_RUN`

## Explicitly false

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `EVALUATION_EXECUTED=false`
- `RUNNER_STARTED=false`
