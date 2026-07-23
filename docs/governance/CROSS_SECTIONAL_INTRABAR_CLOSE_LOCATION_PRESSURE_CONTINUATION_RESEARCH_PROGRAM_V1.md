# Cross-sectional intrabar close-location pressure continuation research program v1

## Status

`DEFINITION_ONLY` — new independent research-program identity after terminal
`DEVELOPMENT_FAIL` of `CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`.
Evaluation unauthorized.

## Identity

- Program: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1`
- Workstream: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_WORKSTREAM_V1`
- Family: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE`
- Strategy identity: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1`
- First hypothesis: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE`
- Target phenomenon: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION`
- Scope: `CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_DEFINITION_ONLY_PREREGISTRATION_V1`

## Binding

- SSOT: `config/research/cross_sectional_intrabar_close_location_pressure_continuation_research_program_v1.json`
- Validator: `src/research/cross_sectional_intrabar_close_location_pressure_continuation_research_program_v1.py`
- Lane backlog: `config/research/cross_sectional_intrabar_close_location_pressure_continuation_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/cross_sectional_intrabar_close_location_pressure_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Decision packet: `config/research/cross_sectional_intrabar_close_location_pressure_continuation_program_definition_operator_decision_packet_v1.json`
- Discovery evidence: `docs/evidence/cross_sectional_intrabar_close_location_pressure_continuation_definition_discovery_v1/`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Causal mechanism

Mean intrabar close-location value (CLV) ranks instruments whose PT1H bars close
persistently near highs or lows. Aggressive OHLC flow imprint is expected to
continue cross-sectionally under a frozen single-slot ranking cadence. Distinct
from trailing close-return momentum/reversal and from Kaufman path-efficiency
of the close path.

## Universe / data

- Venue: OKX
- Futures-only linear USDT perpetuals
- BTC excluded; spot excluded
- Timeframe: PT1H
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- PIT: sealed DEVELOPMENT_ONLY panel; holdout unbound/untouched

## Gates

- `STRATEGY_IMPLEMENTATION_PRESENT=true` (under separate implementation GO)
- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0` / `RUN_SLOT_CONSUMED=false`
- `HOLDOUT_FORBIDDEN=true`
- `ECONOMIC_GATE_OPEN=false`
- `PROMOTION_ELIGIBLE=false`
- `LIVE&#47;ORDERS&#47;SHADOW&#47;PAPER&#47;TESTNET&#47;SCHEDULER=false`
- Master V2 / Double-Play / risk / sizing / execution: consume-only, no mutation
- CSRHR remains `OPEN_BACKLOG` unchanged

## Separate GO requirements

- Bounded DEVELOPMENT evaluation requires a separate operator GO
- Holdout remains forbidden until a future explicit holdout GO (not authorized here)

## Non-actions

No evaluation, runner, holdout access, path-efficiency retry, CSRHR continue/reuse/mutation,
vol-regime/CS-momentum reopen, Master V2/Double-Play/risk/execution/runtime mutation,
orders, or promotion claims.

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
