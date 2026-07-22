# Volatility Regime Research Program v1

## Status

`DEFINITION_ONLY_PROGRAM_OPEN` — operator-authorized definition-only lane for
`VOLATILITY_COMPRESSION_BREAKOUT_V1`.

## Identity

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Strategy: `VOLATILITY_COMPRESSION_BREAKOUT_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_COMPRESSION_TO_EXPANSION_TRANSITION`
- Hypothesis: `VOLATILITY_COMPRESSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`

## Binding

- SSOT: `config/research/volatility_regime_research_program_v1.json`
- Validator: `src/research/volatility_regime_research_program_v1.py`
- Lane backlog: `config/research/volatility_regime_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/volatility_compression_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Material difference vs terminal coiled spring

Against `VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1` / `vol_breakout&#47;v1`:
regime state uses ATR(20)/close percentile rank (lookback 120), requires 12-bar
compression at <=0.20, separate expansion release at >=0.75 within 6 bars, then
a causally subsequent 20-bar channel break; baseline is unconditional channel
breakout isolating admission value. Not a rename, reopen, or parameter retry of
the terminal binding.

## Gates (definition-only)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `HOLDOUT_AUTHORIZED=false` / `HOLDOUT_FORBIDDEN=true` / `HOLDOUT_BOUND=false`
- `DEVELOPMENT_DATASET_BOUND=true` (`pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`)
- `PROMOTION_AUTHORIZED=false` / `PROMOTION_ELIGIBLE=false`
- `RUNTIME_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0` / `RUN_LIMIT=1`
- `STRATEGY_IMPLEMENTATION_PRESENT=false`
- `RETRY_ALLOWED=false`

## Non-actions

No evaluation, runner, dataset load, holdout access, retry, reopen, CS-momentum
lane reopen, Master V2/Double-Play/risk/execution/runtime mutation.

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_SEMANTICS_COMPLETION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY_PROGRAM_OPEN
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
