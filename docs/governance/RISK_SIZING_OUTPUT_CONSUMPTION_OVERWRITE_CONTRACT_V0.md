# Risk / Sizing Output Consumption / Overwrite Contract v0

**Status:** BINDING inventory &#47; output-consumption &#47; overwrite freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0`  
**Machine contract:** [`config/governance/risk_sizing_output_consumption_overwrite_contract_v0.json`](../../config/governance/risk_sizing_output_consumption_overwrite_contract_v0.json)  
**Related (unchanged):** [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md)

```
RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0=true
INVENTORY_ONLY=true
OUTPUT_CONSUMPTION_OVERWRITE_FROZEN=true
OUTPUT_CONSUMPTION_OVERWRITE_RESOLVED=false
NO_SIZING_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_UNITS_DIMENSIONS_SEMANTICS_CHANGE=true
NO_TOPOLOGY_SEMANTICS_CHANGE=true
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
LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain
```

## Precision clarification (historical wording)

A prior read-only consolidation audit closing block used `SEMANTICS_FREE_IMPLEMENTATION_AVAILABLE=true`.

**Correct meaning (binding for this and future slices):**

- `SEMANTICS_FREE_CONTRACT_SLICE_AVAILABLE=true` — only the next governance &#47; contract slice is semantics-free implementable.
- `SEMANTICS_FREE_OWNER_CONSOLIDATION_AVAILABLE=false` — owner consolidation, rewire, federation implementation, authority assignment, and math &#47; units normalization are **not** semantics-free.

Do **not** interpret the historical marker as permission to consolidate owners without separate Operator-GO and semantic decisions. Historical chat &#47; audit evidence is not rewritten; this contract documents the clarification explicitly.

## Purpose

Closed-world freeze of how productive callers **consume, overwrite, veto, wrap, pass through, intent-only, evidence-only, hand off, ignore, or ambiguously use** Risk &#47; Sizing owner outputs.

This slice does **not**:

- assign `CANONICAL_RISK_SIZING_OWNER` or execution authority
- change sizing formulas, defaults, percent &#47; decimal conventions, leverage application, or caller behavior
- mutate owner &#47; bypass allowlists or topology &#47; units contracts
- implement federation, delegation, or consolidation
- activate runtime bridge, live, shadow, testnet, or orders

## Consumption classes (closed catalog)

| Class | Meaning |
|---|---|
| `FINAL_CONSUMER` | Terminal consumer of owner output (e.g. `Trade.size`) |
| `ABSOLUTE_VALUE_TRANSFORM` | Signed → unsigned magnitude (`abs`) |
| `ZERO_OR_VETO_OVERRIDE` | Force zero &#47; reject &#47; block (no silent resize) |
| `CAP_OVERRIDE` | Cap magnitude (overwrite) |
| `WRAP_DELEGATE` | Owner wraps another owner; **not** equal-rank authority |
| `PASS_THROUGH_ONLY` | Adapter &#47; declared pass-through; not a sixth owner |
| `INTENT_ONLY` | Consumes into plan &#47; intent only |
| `EVIDENCE_ONLY` | Evidence &#47; provenance refs only |
| `SUBMISSION_BLOCKED` | Submission remains blocked |
| `DIRECT_ORDER_HANDOFF` | Near order construction &#47; execution path |
| `IGNORED_OUTPUT` | Owner output ignored (productive count currently 0; catalog sentinel pinned) |
| `AMBIGUOUS_CONSUMPTION` | Dimension &#47; ownership ambiguous; must not silently resolve |

## Expected counts

| Surface | Count |
|---|---|
| Primary owners (referenced) | 5 |
| Topology productive direct edges (referenced) | 8 |
| Companion edges (referenced) | 2 |
| Direct sizing bypasses (referenced) | 5 |
| Topology pass-through edges (referenced) | 2 |
| Topology ambiguous edges (referenced) | 3 |
| Consumption edges | 27 |
| Overwrite edges (`is_overwrite=true`) | 13 |
| Wrap &#47; delegate edges | 1 |
| Final quantity provenance resolved paths | 5 |
| Final quantity provenance unresolved paths | 3 |

## Final quantity provenance

**Resolved paths (5):**

1. Engine core-sizer → Trade
2. Engine offline-eval → Trade
3. Engine classic `calc_position_size` → Trade
4. Feedback adapter mirrors engine (no new authority)
5. CRS MV2 intent bridge (`final_quantity` → intent; submission blocked)

**Unresolved paths (3):**

1. `execute_from_signals` (`max_position_notional_pct` ambiguous)
2. Shadow companion `position_fraction` → absolute units
3. Live companion `position_fraction` → absolute units

## Authority &#47; leverage &#47; planning

- `canonical_execution_authority_owner = UNRESOLVED`
- `canonical_risk_sizing_authority_owner = UNRESOLVED`
- Leverage: declared &#47; pass-through, **not** applied in quantity chain
- `PERCENT_0_100` must not be equated with `FRACTION_DECIMAL_0_1`
- `RECOMMENDED_CONSOLIDATION_MODEL=CONTRACTUAL_FEDERATION` is **planning-only**
- Wrap &#47; delegate must not be equated with equal-rank authority
- Companion edges must not be counted as a sixth primary owner

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- Owner count 5 and bypass count 5 remain unchanged
- Topology and units contracts remain separate and unchanged in semantics
- No productive `src&#47;**` mutation in this slice

## Next

Consumption &#47; overwrite topology is **frozen** but **not resolved** (`OUTPUT_CONSUMPTION_OVERWRITE_RESOLVED=false`). The three unresolved Final Quantity Provenance paths are frozen separately in [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) (`OBL_B05_FINAL_QUANTITY_PROVENANCE_UNRESOLVED_PATHS_CONTRACT_V0`). Federation, authority assignment, rewire, decommission, and percent &#47; leverage normalization remain Operator-GO gated (`NEXT_SLICE_REQUIRES_OPERATOR_GO=true`).
