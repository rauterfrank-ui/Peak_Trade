# Material-different cross-sectional momentum program v1

## Status

`STRATEGY_IMPLEMENTATION_PRESENT_PROGRAM_OPEN` — operator-authorized new research program;
definition&#47;preregistration only.

## Identity

- Program: `MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1`
- Strategy: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Target phenomenon: `PERSISTENCE_OF_RELATIVE_RETURNS_ACROSS_NON_BTC_LINEAR_USDT_FUTURES`

## Binding

- SSOT: `config&#47;research&#47;material_different_cross_sectional_momentum_program_v1.json`
- Validator: `src&#47;research&#47;material_different_cross_sectional_momentum_program_v1.py`
- Lane backlog: `config&#47;research&#47;material_different_cross_sectional_momentum_hypothesis_backlog_v1.json`
- Measurement contract: `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Lifecycle authority (sole): `CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`

## Causal independence

Independent from closed Bollinger&#47;MR Entry Eligibility and Exit Efficiency lanes
and from failed bindings&#47;filters including midband exit, reentry cooldown,
ADX-DI, regime-gated standaside, MA&#47;MACD&#47;RSI entry filters, and unchanged
`cross_sectional_relative_strength&#47;v0` binding retry.

## Gates (definition-only)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `HOLDOUT_AUTHORIZED=false` / `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_AUTHORIZED=false` / `PROMOTION_ELIGIBLE=false`
- `RUNTIME_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0`
- `STRATEGY_IMPLEMENTATION_PRESENT=true`
- `RUN_SLOT_CONSUMED=false`

## Non-actions

No evaluation, runner, holdout access, strategy producer, backtest, synthetic
results, Entry&#47;Exit reopen, terminal-result mutation, Master V2&#47;Double-Play&#47;risk&#47;
execution&#47;runtime mutation.

## Implementation

- Binding: `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_strategy_implementation_binding_v1.json`
- Measurement contract digest remains frozen; evaluation still unauthorized.

## Next step

`REVIEW_DEFINITION_ONLY_PREREGISTRATION_AWAITING_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT_PROGRAM_OPEN
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
