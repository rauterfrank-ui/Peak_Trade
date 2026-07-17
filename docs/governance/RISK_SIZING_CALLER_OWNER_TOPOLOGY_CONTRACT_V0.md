# Risk / Sizing Caller→Owner Topology Contract v0

**Status:** BINDING inventory &#47; caller→owner topology freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_CALLER_TO_OWNER_TOPOLOGY_CONTRACT_V0`  
**Machine contract:** [`config/governance/risk_sizing_caller_owner_topology_contract_v0.json`](../../config/governance/risk_sizing_caller_owner_topology_contract_v0.json)  
**Related (unchanged):** [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md) (5&#47;5 owner&#47;bypass surface) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) (units&#47;dimensions)

```
RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0=true
INVENTORY_ONLY=true
CALLER_TO_OWNER_TOPOLOGY_FROZEN=true
CALLER_TO_OWNER_TOPOLOGY_RESOLVED=false
NO_SIZING_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_UNITS_DIMENSIONS_SEMANTICS_CHANGE=true
NO_REWIRE=true
NO_DELEGATION=true
NO_DECOMMISSION=true
CONSOLIDATION_STATUS=NOT_STARTED
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
EXPECTED_PRIMARY_OWNER_COUNT=5
EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT=8
EXPECTED_COMPANION_EDGE_COUNT=2
EXPECTED_DIRECT_SIZING_BYPASS_COUNT=5
EXPECTED_PASS_THROUGH_EDGE_COUNT=2
EXPECTED_AMBIGUOUS_EDGE_COUNT=3
EXPECTED_UNRESOLVED_SYMBOL_COUNT=0
EXPECTED_PERCENT_CONFLICT_COUNT=2
EXPECTED_OWNER_WITHOUT_EXTERNAL_PRODUCTIVE_CALLER_COUNT=1
EXPECTED_PRODUCTIVE_CALLER_WITHOUT_PINNED_CANONICAL_OWNER_COUNT=2
EXPECTED_EXECUTE_FROM_SIGNALS_EXTERNAL_CALLER_COUNT=0
LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain
```

## Purpose

Closed-world freeze of the existing **caller→owner topology** for Risk&#47;Sizing. This slice does **not**:

- assign `CANONICAL_RISK_SIZING_OWNER` or execution authority
- change sizing formulas, defaults, percent&#47;decimal conventions, leverage application, or caller behavior
- add&#47;remove&#47;rename owner or bypass allowlist entries on the surface contract
- redefine units&#47;dimensions (references v0 contract only)
- activate runtime bridge, live, shadow, testnet, or orders

## Expected counts

| Surface | Count |
|---|---|
| Primary owners | 5 |
| Productive direct edges | 8 |
| Companion edges | 2 |
| Direct sizing bypasses | 5 |
| Pass-through edges | 2 |
| Ambiguous edges | 3 |
| Unresolved symbols | 0 |
| Percent conflicts (unresolved) | 2 |
| Owners without external productive caller | 1 |
| Productive callers without pinned canonical owner | 2 |
| `execute_from_signals` external productive callers | 0 |

## Primary owners (exactly 5; referenced)

Same IDs as `risk_sizing_owner_and_bypass_surface_contract_v1` &#47; units contract.

## Productive direct edges (exactly 8)

| edge_id | caller | callee | owner |
|---|---|---|---|
| `EDGE_CRS_INTENT_PIPELINE_BRIDGE` | intent pipeline bridge | `evaluate_capital_risk_sizing_v1` | CRS |
| `EDGE_CRS_OFFLINE_REPLAY_ADAPTER` | offline replay adapter | `evaluate_capital_risk_sizing_v1` | CRS |
| `EDGE_ENGINE_CALC_POSITION_SIZE` | `BacktestEngine.run_realistic` | `calc_position_size` | position_sizer |
| `EDGE_ENGINE_GET_TARGET_POSITION` | `BacktestEngine.run_realistic` | `get_target_position` | core.position_sizing |
| `EDGE_ENGINE_OFFLINE_EVAL_SIZING` | `BacktestEngine.run_realistic` | `size_offline_evaluation_entry_v1` | offline-eval |
| `EDGE_FEEDBACK_CALC_POSITION_SIZE` | `step_legacy_realistic_bar_v1` | `calc_position_size` | position_sizer |
| `EDGE_FEEDBACK_GET_TARGET_POSITION` | `step_legacy_realistic_bar_v1` | `get_target_position` | core.position_sizing |
| `EDGE_FEEDBACK_OFFLINE_EVAL_SIZING` | `step_legacy_realistic_bar_v1` | `size_offline_evaluation_entry_v1` | offline-eval |

CRS adapter edges are also `PASS_THROUGH_ONLY` (not additional owners).

## Companion edges (exactly 2; not primary owners)

Referenced from units&#47;dimensions contract: Shadow `step_once` and Live `step_once` pass `position_fraction` as absolute units into `signal_to_orders`.

## Direct sizing bypasses (exactly 5; referenced)

Referenced from owner&#47;bypass surface contract v1 — unchanged allowlist.

## Ambiguous edges (exactly 3)

- Offline-eval wraps `calc_position_size` (owner wraps other owner)
- Sweeps &#47; Diagnostics `build_position_sizer_from_config` (`OFFLINE_ANALYTICS_ONLY`; callers without pinned canonical owner)

## Authority &#47; leverage &#47; percent

- `canonical_execution_authority_owner = UNRESOLVED`
- `canonical_risk_sizing_authority_owner = UNRESOLVED`
- Leverage: declared&#47;pass-through, **not** applied in quantity chain
- Percent conflicts remain unresolved; `PERCENT_0_100` must not be equated with `FRACTION_DECIMAL_0_1`

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- Owner count 5 and bypass count 5 remain unchanged on the surface contract
- Units&#47;dimensions contract remains separate and unchanged in semantics
- Legacy Order Intent surface contracts remain separate and unchanged

## Next

Topology is **frozen** but **not resolved** (`CALLER_TO_OWNER_TOPOLOGY_RESOLVED=false`). Output consumption&#47;overwrite is frozen separately in [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) (`OBL_B05_RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0`). Authority assignment, rewire, decommission, and percent&#47;leverage normalization remain Operator-GO gated.
