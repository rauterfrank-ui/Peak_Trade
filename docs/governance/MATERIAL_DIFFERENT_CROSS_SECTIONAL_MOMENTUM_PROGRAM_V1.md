# Material-different cross-sectional momentum program v1

## Status

`PROGRAM_CLOSED_NO_FURTHER_RESEARCH` — definition-only terminal lane closure after
`CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1` `FAIL_CLOSED_NO_RETRY`.

## Identity

- Program: `MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1`
- Terminal strategy: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Terminal result: `FAIL_CLOSED_NO_RETRY`
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

## Gates (definition-only closure)

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `HOLDOUT_AUTHORIZED=false` &#47; `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_AUTHORIZED=false` &#47; `PROMOTION_ELIGIBLE=false`
- `RUNTIME_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=1` &#47; `RUNNER_START_COUNT=1`
- `RUN_SLOT_CONSUMED=true` &#47; `RUN_BUDGET_CONSUMED=true`
- `RETRY_ALLOWED=false` &#47; `REOPEN_ALLOWED=false`
- `SUCCESSOR_FOUND=false` &#47; `NEXT_ELIGIBLE=NONE`
- `CREATE_SUCCESSOR_HYPOTHESIS=false` &#47; `AUTOMATIC_SUCCESSOR_CREATION=false`
- `REQUIRES_NEW_SEPARATE_OPERATOR_AUTHORIZATION=true`
- `STRATEGY_IMPLEMENTATION_PRESENT=true` (historical; no new authorization)

## Non-actions

No evaluation, runner, holdout access, retry, reopen, successor invention,
run-slot reset, Entry&#47;Exit reopen, terminal-result mutation, Master V2&#47;Double-Play&#47;risk&#47;
execution&#47;runtime mutation.

## Next step

`LANE_CLOSED_NO_FURTHER_RESEARCH_NO_EXECUTABLE_GO`

Future research requires a new, separately operator-authorized and preregistered
program. This closure does not authorize any successor.

---
docs_token: DOCS_TOKEN_MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1
STATUS: PROGRAM_CLOSED_NO_FURTHER_RESEARCH
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
