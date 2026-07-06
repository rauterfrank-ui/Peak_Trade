# Versioned Final Fleet Bindings and Offline Economic Evaluation Scope v0

---
docs_token: DOCS_TOKEN_RATIFY_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0
STATUS: VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED_V0
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifies the final research fleet for versioned binding materialization only. No economic evaluation execution, no runtime authority, no orders.

## Verdict

`VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED_V0`

## Scope

This scope ratifies the final research fleet for versioned binding materialization only.

Final fleet:

- `trend_following`
- `bollinger_bands`
- `momentum_1h`

This scope does not execute an economic evaluation.

## Required bindings before any evaluation

Each candidate must bind:

- strategy_id
- strategy_version
- parameter_binding
- dataset_binding
- period_binding
- instrument_binding
- fee_model_binding
- slippage_model_binding
- funding_model_binding
- execution_model_binding
- economic_policy_binding
- implementation_digest
- config_digest
- data_digest

## Authority boundaries

- `ECONOMIC_EVALUATION_AUTHORIZED=false`
- `RUNTIME_REWIRE_ADMISSIBLE=false`
- `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS_ALLOWED=false`
- `SCHEDULER_RUNTIME_ALLOWED=false`

No core trading logic, Master V2, Double Play, risk/sizing, safety/runtime, scheduler, adapter, credential, shadow, paper, testnet, canary, or live authority is introduced.

## Next step

`MATERIALIZE_VERSIONED_FINAL_FLEET_BINDINGS_PRECONDITIONS_OR_SEPARATE_OFFLINE_EVALUATION_GO_REQUIRED`
