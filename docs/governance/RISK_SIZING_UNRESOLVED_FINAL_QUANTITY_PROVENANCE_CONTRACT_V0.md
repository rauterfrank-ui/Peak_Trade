# Risk / Sizing Unresolved Final Quantity Provenance Contract v0

**Status:** BINDING inventory &#47; unresolved-path freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATHS_CONTRACT_V0`  
**Machine contract:** [`config/governance/risk_sizing_unresolved_final_quantity_provenance_contract_v0.json`](../../config/governance/risk_sizing_unresolved_final_quantity_provenance_contract_v0.json)  
**Related (unchanged):** [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md) · [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md)

```
RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0=true
INVENTORY_ONLY=true
FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATHS_FROZEN=true
FINAL_QUANTITY_PROVENANCE_RESOLVED=false
NO_SIZING_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_UNITS_DIMENSIONS_SEMANTICS_CHANGE=true
NO_TOPOLOGY_SEMANTICS_CHANGE=true
NO_CONSUMPTION_OVERWRITE_SEMANTICS_CHANGE=true
NO_REWIRE=true
NO_DELEGATION=true
NO_DECOMMISSION=true
NO_FEDERATION_IMPLEMENTED=true
CONSOLIDATION_STATUS=NOT_STARTED
RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION
SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true
SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false
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
EXPECTED_UNRESOLVED_PATH_COUNT=3
EXPECTED_NEW_DIRECT_CALLER_COUNT=0
LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain
```

## Purpose

Closed-world documentation and static freeze of the **three remaining unresolved Final Quantity Provenance paths**:

1. `PATH_EXECUTE_FROM_SIGNALS` — `ExecutionPipeline.execute_from_signals`
2. `PATH_SHADOW_COMPANION` — Shadow `position_fraction` → `signal_to_orders`
3. `PATH_LIVE_COMPANION` — Live-session companion `position_fraction` → `signal_to_orders` → `execute_with_safety`

This slice does **not**:

- resolve dimensions or assign a canonical Risk &#47; Sizing / Execution authority owner
- change sizing formulas, capital allocation, position-sizing semantics, or execution semantics
- mutate inventory &#47; topology &#47; units &#47; consumption-overwrite contracts
- implement federation, delegation, consolidation, or rewire
- activate runtime bridge, live, shadow, testnet, or orders

## Unresolved paths (closed world)

| path_id | Entrypoint | Companion role | Submission class | Why unresolved |
|---|---|---|---|---|
| `PATH_EXECUTE_FROM_SIGNALS` | `ExecutionPipeline.execute_from_signals` | not companion | `DIRECT_ORDER_PATH_WHEN_INVOKED` | `max_position_notional_pct` name&#47;doc vs absolute-units usage |
| `PATH_SHADOW_COMPANION` | `ShadowPaperSession.step_once` | companion, not primary | `SHADOW_ORDER_HANDOFF` | declared fraction passed as absolute units |
| `PATH_LIVE_COMPANION` | `LiveSessionRunner.step_once` | companion, not primary | `LIVE_SESSION_HANDOFF_STILL_GATED` | same fraction ambiguity; gated `execute_with_safety` |

Frozen referenced counts remain **5 / 8 / 2 / 5 / 2 / 3** and **27 / 13 / 1**, with resolved&#47;unresolved provenance **5 / 3**.

## Binding non-claims

- no canonical Risk-Sizing owner assigned
- no canonical Execution-Authority owner assigned
- Companion is **not** a sixth primary owner
- Order-Handoff ≠ Submission-Authority
- Runtime reachability ≠ activation
- Shadow &#47; Live naming ≠ `LIVE_AUTHORIZED`
- Wrap &#47; Delegate ≠ authority
- `PERCENT_0_100` must not be equated with `FRACTION_DECIMAL_0_1`
- Leverage is **not** claimed applied in the quantity chain
- no semantics-free owner consolidation
- Final Quantity Provenance is **not** fully resolved

## Drift guards (fail-closed)

Guards fail on:

- new direct productive caller of any of the three paths
- removed &#47; reordered transform step
- new clamp &#47; cap &#47; veto &#47; abs &#47; sign &#47; round &#47; cast without contract update
- new order &#47; submission handoff
- `submission_blocked` → submit-capable escalation
- companion escalation to primary owner
- authority or final-provenance escalation from `UNRESOLVED`
- runtime-bridge / live / orders activation claims
- leverage-applied claim
- silent change of unresolved path count **3**
- mutation of frozen counts **5 / 8 / 2 / 5 / 2 / 3**, **27 / 13 / 1**, resolved&#47;unresolved **5 / 3**

## Authority &#47; leverage &#47; planning

- `canonical_execution_authority_owner = UNRESOLVED`
- `canonical_risk_sizing_authority_owner = UNRESOLVED`
- Leverage: declared &#47; pass-through, **not** applied in quantity chain
- `RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION` is **planning-only**
- `SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true` does **not** authorize owner consolidation

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- No productive `src&#47;**` mutation in this slice

## Next

Unresolved Final Quantity Provenance paths are **frozen** but **not resolved** (`FINAL_QUANTITY_PROVENANCE_RESOLVED=false`). The semantics-free resolution-audit classification freeze lives separately in [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md) (`OBL_B05_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_CONTRACT_V1`) and does **not** resolve provenance or choose an intent line. Dimension normalization, authority assignment, rewire, decommission, and federation remain Operator-GO gated (`NEXT_SLICE_REQUIRES_OPERATOR_GO=true`).
