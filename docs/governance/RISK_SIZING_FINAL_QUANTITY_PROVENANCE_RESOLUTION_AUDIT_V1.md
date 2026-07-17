# Risk / Sizing Final Quantity Provenance Resolution Audit v1

**Status:** BINDING semantics-free resolution-audit freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_CONTRACT_V1`  
**Machine contract:** [`config/governance/risk_sizing_final_quantity_provenance_resolution_audit_v1.json`](../../config/governance/risk_sizing_final_quantity_provenance_resolution_audit_v1.json)  
**Related (unchanged):** [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) · [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md)

```
RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1=true
INVENTORY_ONLY=true
RESOLUTION_AUDIT_FROZEN=true
FINAL_QUANTITY_PROVENANCE_RESOLVED=false
NO_SIZING_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_UNITS_DIMENSIONS_SEMANTICS_CHANGE=true
NO_TOPOLOGY_SEMANTICS_CHANGE=true
NO_CONSUMPTION_OVERWRITE_SEMANTICS_CHANGE=true
NO_INTENT_LINE_CHOSEN=true
NO_REWIRE=true
NO_DELEGATION=true
NO_DECOMMISSION=true
NO_FEDERATION_IMPLEMENTED=true
CONSOLIDATION_STATUS=NOT_STARTED
RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION
SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true
SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false
NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED=false
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
EXPECTED_CONSUMPTION_EDGE_COUNT=27
EXPECTED_OVERWRITE_EDGE_COUNT=13
EXPECTED_WRAP_DELEGATE_EDGE_COUNT=1
EXPECTED_FINAL_QUANTITY_PROVENANCE_RESOLVED_PATH_COUNT=5
EXPECTED_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATH_COUNT=3
EXPECTED_SEMANTIC_CONFLICT_PATH_COUNT=3
EXPECTED_CONTRACT_FAMILY_COUNT=1
EXPECTED_SUBCONTRACT_COUNT=2
EXPECTED_COMPANION_CONFLICT_PATH_COUNT=2
EXPECTED_EFS_CONFLICT_PATH_COUNT=1
LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain
COMMON_UNIFIED_SEMANTICS_DECISION=NOT_TAKEN
COMPANION_SHARED_CONTRACT_POSSIBLE=true
EFS_REMAINS_SEPARATE=true
```

## Purpose

Closed-world freeze of the **resolution-audit classification** for the three unresolved Final Quantity Provenance paths. This slice pins that each path is a `SEMANTIC_CONFLICT` (declared dimension vs runtime consumption) **without** choosing a productive intent line, assigning authority, or mutating runtime code.

This slice does **not**:

- resolve Final Quantity Provenance (`FINAL_QUANTITY_PROVENANCE_RESOLVED=false`)
- choose fraction vs absolute-units intent
- assign a canonical Risk &#47; Sizing or Execution authority owner
- change sizing formulas, capital allocation, validators, defaults, or execution semantics
- mutate inventory &#47; topology &#47; units &#47; consumption-overwrite contracts
- implement federation, delegation, consolidation, or rewire
- activate runtime bridge, live, shadow, testnet, or orders
- treat smoke assertions such as `quantity == position_size` as semantic proof

## Federated contract family (exactly two subcontracts)

| subcontract_id | Paths | Role |
|---|---|---|
| `COMPANION_FRACTION_TO_ABSOLUTE_UNITS_CONFLICT` | `PATH_SHADOW_COMPANION`, `PATH_LIVE_COMPANION` | Shared companion conflict; sizing pass-through |
| `EFS_CAPITAL_SHARE_TO_ABSOLUTE_UNITS_CONFLICT` | `PATH_EXECUTE_FROM_SIGNALS` | Separate EFS kernel conflict; zero productive `src&#47;` callers |

Pins:

- `COMPANION_SHARED_CONTRACT_POSSIBLE=true`
- `EFS_REMAINS_SEPARATE=true`
- `COMMON_UNIFIED_SEMANTICS_DECISION=NOT_TAKEN`
- A single unified semantics decision across all three paths is **not** taken

## Audited paths (closed world)

| path_id | Classification | Declared | Runtime | Root cause (summary) |
|---|---|---|---|---|
| `PATH_EXECUTE_FROM_SIGNALS` | `SEMANTIC_CONFLICT` | Capital-share &#47; pct-named | `QUANTITY_BASE_UNITS` | `max_position_notional_pct` used as absolute units; no equity&#47;price conversion |
| `PATH_SHADOW_COMPANION` | `SEMANTIC_CONFLICT` | `FRACTION_DECIMAL_0_1` | `QUANTITY_BASE_UNITS` | Fraction aliased as `position_size` into `signal_to_orders`; Risk-Veto only |
| `PATH_LIVE_COMPANION` | `SEMANTIC_CONFLICT` | `FRACTION_DECIMAL_0_1` | `QUANTITY_BASE_UNITS` | Same companion handoff; fraction validator + `execute_with_safety` &#47; mode gates |

Shared evidence pins:

- missing Fraction &#47; Capital-Share → Units conversion on all three paths
- no double conversion observed
- no leverage applied in the quantity chain
- Shadow &#47; Live remain companion sizing pass-through (not primary owners)
- EFS remains separate with `external_productive_src_caller_count=0`

## Binding non-claims

- no canonical Risk-Sizing owner assigned
- no canonical Execution-Authority owner assigned
- no intent line chosen between Fraction and Absolute-Units semantics
- Companion is **not** a sixth primary owner
- Order-Handoff ≠ Submission-Authority
- Runtime reachability ≠ activation
- Shadow &#47; Live naming ≠ `LIVE_AUTHORIZED`
- `PERCENT_0_100` must not be equated with `FRACTION_DECIMAL_0_1`
- Leverage is **not** claimed applied in the quantity chain
- no semantics-free owner consolidation
- Final Quantity Provenance is **not** fully resolved
- smoke `quantity == position_size` is runtime evidence only, not semantic proof

## Baseline counts (referenced, unchanged)

Frozen referenced counts remain **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3** and **27 &#47; 13 &#47; 1**, with resolved&#47;unresolved provenance **5 &#47; 3**. This audit does not re-own or alter those contracts.

## Drift guards (fail-closed)

Guards fail on:

- any path classification other than `SEMANTIC_CONFLICT`
- intent-line choice without Operator-GO
- authority or final-provenance escalation from `UNRESOLVED`
- subcontract count change from **2**
- path-id set change from the three frozen IDs
- mutation of frozen baseline counts **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3**, **27 &#47; 13 &#47; 1**, resolved&#47;unresolved **5 &#47; 3**
- productive `src&#47;**` mutation claims
- leverage-applied or double-conversion claims
- companion escalation to primary owner
- unified semantics decision claim
- runtime-bridge &#47; live &#47; orders activation claims
- treating smoke `quantity == position_size` as semantic proof

## Authority &#47; planning

- `canonical_execution_authority_owner = UNRESOLVED`
- `canonical_risk_sizing_authority_owner = UNRESOLVED`
- Leverage: declared &#47; pass-through, **not** applied in quantity chain
- `RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION` is **planning-only**
- `NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED=false`

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- No productive `src&#47;**` mutation in this slice

## Next

Resolution-audit classifications are **frozen**; Final Quantity Provenance remains **unresolved** (`FINAL_QUANTITY_PROVENANCE_RESOLVED=false`). Any productive intent choice (Fraction vs Absolute-Units), math change, rename, validator change, rewire, authority assignment, or federation implementation requires a **separate Operator-GO** (`NEXT_PRODUCTIVE_SEMANTICS_SLICE_AUTHORIZED=false`).
