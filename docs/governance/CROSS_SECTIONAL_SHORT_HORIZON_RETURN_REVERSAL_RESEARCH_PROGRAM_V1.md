# Cross-sectional short-horizon return-reversal research program v1

## Status

`DEFINITION_ONLY` — new independent research-program identity after closed
`VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`. Evaluation unauthorized.

## Identity

- Program: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1`
- Family: `CROSS_SECTIONAL_RETURN_REVERSAL`
- Strategy identity: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1`
- First hypothesis: `CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1`
- Signal family: `CROSS_SECTIONAL_RETURN_REVERSAL`
- Target phenomenon: `SHORT_HORIZON_CROSS_SECTIONAL_RELATIVE_RETURN_REVERSAL`

## Binding

- SSOT: `config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json`
- Validator: `src/research/cross_sectional_short_horizon_return_reversal_research_program_v1.py`
- Lane backlog: `config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json`
- Measurement contract: `config/research/cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Decision packet: `config/research/cross_sectional_short_horizon_return_reversal_program_definition_operator_decision_packet_v1.json`
- Discovery evidence: `docs/evidence/new_research_program_identity_definition_discovery_v1/`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Causal mechanism

Short-horizon cross-sectional relative losers (negated trailing log-return rank) are
expected to reverse over a frozen forward holding cadence. Opposite polarity to
terminal CS momentum persistence; not a volatility-regime RV-rank mechanism.

## Universe / data

- Venue: OKX
- Futures-only linear USDT perpetuals
- BTC excluded; spot excluded
- Timeframe: PT1H
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- PIT: sealed DEVELOPMENT_ONLY panel; holdout unbound/untouched

## Gates (definition-only)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0` / `RUN_SLOT_CONSUMED=false`
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

No evaluation, runner, holdout access, vol-regime reopen, CS-momentum reopen/retune,
Master V2/Double-Play/risk/execution/runtime mutation, orders, or promotion claims.

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_OR_BOUNDED_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
