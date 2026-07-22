# Volatility Regime Research Program v1

## Status

`DEFINITION_ONLY_PROGRAM_OPEN` — operator-authorized definition-only lane for
`VOLATILITY_DECAY_BREAKOUT_V1` after terminal
`VOLATILITY_EXPANSION_PERSISTENCE_V1` `FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`.

## Identity

- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Strategy: `VOLATILITY_DECAY_BREAKOUT_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_DECAY_AFTER_HIGH_VOL_THEN_CHANNEL_BREAKOUT`
- Hypothesis: `VOLATILITY_DECAY_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`

## Binding

- SSOT: `config/research/volatility_regime_research_program_v1.json`
- Validator: `src/research/volatility_regime_research_program_v1.py`
- Lane backlog: `config/research/volatility_regime_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/volatility_decay_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Material difference vs terminal VEP-V1

High→low vol decay admission (percentile from >=0.70 to <0.40 with falling
normalized ATR) and post-decay window t+1..t+8; not expansion persistence;
not an exit repair of `UNPAIRABLE_ENTRY_NO_EXIT`.

## Material difference vs VCB-V1

No compression prerequisite; decay transition vs compression→expansion;
ATR(14) vs ATR(20).

## Gates (definition-only)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `HOLDOUT_AUTHORIZED=false` / `HOLDOUT_FORBIDDEN=true` / `HOLDOUT_BOUND=false`
- `DEVELOPMENT_DATASET_BOUND=true` (`pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`)
- `PROMOTION_AUTHORIZED=false` / `PROMOTION_ELIGIBLE=false`
- `RUNTIME_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=1` / `RUNNER_START_COUNT=1` / `RUN_LIMIT=1` / `RUN_SLOT_CONSUMED=true`
- `STRATEGY_IMPLEMENTATION_PRESENT=false`
- `RETRY_ALLOWED=false`

## Non-actions

No evaluation, runner, dataset load, holdout access, VEP/VCB retry, reopen,
CS-momentum lane reopen, Master V2/Double-Play/risk/execution/runtime mutation.

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY_PROGRAM_OPEN
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
