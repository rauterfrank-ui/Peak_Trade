# Momentum V2 — volatility-scaled own-instrument continuation research program v1

Status: `DEFINITION_ONLY`

## Identity

- Program: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1`
- Workstream: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1`
- Scope: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_DEFINITION_ONLY_PREREGISTRATION_V1`
- Hypothesis: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity (research-only): `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1`

## Purpose

Define exactly one new independent Momentum-V2 research program after the
docs-only Momentum surface disambiguation. The program tests whether
**volatility scaling** of own-instrument lookback returns improves post-cost
economics versus the frozen raw-return `momentum_1h` ENTRY&#47;EXIT baseline.

## Non-identity clarifications

- Not a class named `MomentumV2` and not a second registry implementation.
- Registry strategy `momentum_1h` &#47; `MomentumStrategy` remains unchanged.
- Research binding `momentum_1h&#47;v2` &#47; `MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2`
  remains a separate pending offline-evaluation scope and is **not** renamed,
  retuned, or executed in this slice.
- Closed CS relative-strength momentum lane remains closed.

## Dataset

- `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Class: `DEVELOPMENT_ONLY`
- BTC excluded; spot excluded; PIT-safe features only

## Authority

- `EVALUATION_AUTHORIZED=false`
- `IMPLEMENTATION_AUTHORIZED=true`
- `DEVELOPMENT_RUN_COUNT=0`
- `RUN_SLOT_CONSUMED=false`
- Double-Play remains sole directional transition authority
- Runtime Bridge remains `BOUND_NOT_ACTIVATED`
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`

## SSOT

- Program: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_research_program_v1.json`
- Backlog: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_backlog_v1.json`
- Contract: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
