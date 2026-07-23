# Cross-sectional path-efficiency continuation research program v1

## Status

`DEFINITION_ONLY` — new independent research-program identity, separate from open
`CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1` and closed
`VOLATILITY_REGIME_RESEARCH_PROGRAM_V1` / CS-momentum. Evaluation unauthorized.

## Identity

- Workstream: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_WORKSTREAM_V1`
- Program: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1`
- Family: `CROSS_SECTIONAL_PATH_EFFICIENCY`
- Strategy identity: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1`
- First hypothesis: `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_PATH_EFFICIENCY`
- Target phenomenon: `CROSS_SECTIONAL_PATH_EFFICIENCY_DIRECTIONAL_CONTINUATION`
- Treatment: `OWN_INSTRUMENT_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_ADMISSION`

## Binding

- SSOT: `config/research/cross_sectional_path_efficiency_continuation_research_program_v1.json`
- Validator: `src/research/cross_sectional_path_efficiency_continuation_research_program_v1.py`
- Lane backlog: `config/research/cross_sectional_path_efficiency_continuation_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/cross_sectional_path_efficiency_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Decision packet: `config/research/cross_sectional_path_efficiency_continuation_program_definition_operator_decision_packet_v1.json`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Causal mechanism

Kaufman path-efficiency of trailing PT1H closes (`ER = |net_log_return| / path_sum`)
times `sign(net_log_return)` ranks instruments for directional continuation. Not
endpoint-return momentum, not negated-return reversal (CSRHR), not RV-rank.

## Universe / data

- Venue: OKX
- Futures-only linear USDT perpetuals
- BTC excluded; spot excluded
- Timeframe: PT1H
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- PIT: sealed DEVELOPMENT_ONLY panel; holdout unbound/untouched/access forbidden

## Gates (definition-only)

- `EVALUATION_AUTHORIZED=false`
- `IMPLEMENTATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `DEVELOPMENT_RUN_LIMIT=1` / `RUNNER_START_COUNT=0` / `RUN_SLOT_CONSUMED=false`
- `FAIL_CLOSED_NO_RETRY=true`
- `HOLDOUT_FORBIDDEN=true`
- `ECONOMIC_GATE_OPEN=false`
- `PROMOTION_ELIGIBLE=false`
- `LIVE&#47;ORDERS&#47;SHADOW&#47;PAPER&#47;TESTNET&#47;SCHEDULER=false`
- Master V2 / Double-Play / risk / sizing / execution: consume-only, no mutation

## Separate GO requirements

- Strategy implementation requires a separate operator GO
- Bounded DEVELOPMENT evaluation requires a separate operator GO
- Holdout remains forbidden until a future explicit holdout GO (not authorized here)

## Non-actions

No evaluation, runner, holdout access, CSRHR continue/reuse/mutation, vol-regime reopen,
CS-momentum reopen/retune, Entry/Exit-MR reopen, Funding/OI/term-structure reopen,
MA-crossover-rank reopen, lead-lag elevation, relative-volume breakout, skewness fade,
Master V2/Double-Play/risk/execution/runtime mutation, orders, or promotion claims.

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_OR_BOUNDED_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
