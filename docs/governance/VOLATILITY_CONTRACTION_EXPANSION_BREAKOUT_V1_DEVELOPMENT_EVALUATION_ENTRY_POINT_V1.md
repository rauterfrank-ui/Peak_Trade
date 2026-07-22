# Volatility contraction-expansion breakout v1 — DEVELOPMENT evaluation entry point

DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1

## Status

`EXECUTABLE_EVALUATE_PATH_PRESENT_EVALUATION_UNAUTHORIZED`

Executable development-evaluation path is present under the canonical entry point.
Development evaluation remains unauthorized on the entry-point binding
(`development_evaluation_authorized=false`). No development evaluation executed.
Run counts remain `0`.

## Owner

`VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_contraction_expansion_breakout_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start, no slot claim
- `dry-validate`: prove executable-path contracts without runner start or counter mutation
- `evaluate`: requires machine-checkable authorization (token **and** repo flags); fail-closed on HEAD

## Bindings

- Strategy identity: `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
  (`DEVELOPMENT_ONLY`)
- Time segments: `CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Measurement contract digest (frozen):
  `e2e5414041c04ed756fe1315938eb49a8196caf416d33feb58055d641c7f5784`
- Entry-point binding:
  `config&#47;research&#47;volatility_contraction_expansion_breakout_v1_development_evaluation_entry_point_binding_v1.json`
- Productive PnL evaluator (reused, not duplicated):
  `src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`

## Non-actions

- No Development evaluation authorization or execution in this slice
- No holdout access
- No run-slot consumption
- No parameter / hypothesis mutation
- No Shadow / Testnet / Live / Orders
