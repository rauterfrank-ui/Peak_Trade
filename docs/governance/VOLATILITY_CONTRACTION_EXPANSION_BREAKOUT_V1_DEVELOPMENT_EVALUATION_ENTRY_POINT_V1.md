# Volatility contraction-expansion breakout v1 — DEVELOPMENT evaluation entry point

DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1

## Status

`RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`

Single authorized Development evaluation on base `e0d90625664139765ade4fc43fb4679421d0d5d5`
entered the evaluate path with panel boundary + productive exit/PnL evaluator bound, then
fail-closed with `UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:AGLD:USDT:USDT:perp:10575`.
Run slot consumed. No retry. No new hypothesis started.

## Owner

`VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1`

## Canonical entry point

`scripts&#47;research&#47;run_evaluate_volatility_contraction_expansion_breakout_development_v1.py`

Modes:

- `preflight` (default): no panel open, no runner start; reports exhausted slot after terminal run
- `dry-validate`: prove executable-path contracts without counter mutation
- `evaluate`: authorization-gated; slot exhausted — retry forbidden

## Bindings

- Strategy identity: `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Measurement contract digest (post-slot):
  `222a4127834a837d2afc23e97849b075360755bd720288340fea097c1f03ff8e`
- Evidence:
  `docs&#47;evidence&#47;evaluate_volatility_contraction_expansion_breakout_development_v1&#47;`
- Productive PnL evaluator (reused, not duplicated):
  `src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`

## Non-actions

- No retry / no second development run
- No holdout access
- No parameter / hypothesis mutation after result knowledge
- No Shadow / Testnet / Live / Orders
- No second PnL truth
- No new hypothesis started in this slice

## Next step

`NO_RETRY_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

## Explicitly false

- `SHADOW=false`
- `TESTNET=false`
- `HOLDOUT_ACCESS=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- `DEVELOPMENT_SLOT_CONSUMED=true`
- `DEVELOPMENT_RUN_COUNT=1`

---
docs_token: DOCS_TOKEN_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1
STATUS: RUN_SLOT_CONSUMED_FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT
scope: research, offline-only, terminal-development-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
