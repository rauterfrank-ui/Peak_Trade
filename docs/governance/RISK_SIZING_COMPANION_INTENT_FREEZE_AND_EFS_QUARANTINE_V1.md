# Risk / Sizing Companion Intent Freeze and EFS Quarantine v1

**Status:** BINDING companion-intent freeze + separate EFS quarantine (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1`  
**Machine contract:** [`config/governance/risk_sizing_companion_intent_freeze_and_efs_quarantine_v1.json`](../../config/governance/risk_sizing_companion_intent_freeze_and_efs_quarantine_v1.json)  
**Related (unchanged):** [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md) · [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) · [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md)

```
RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1=true
INVENTORY_ONLY=true
COMPANION_INTENT_FROZEN=true
COMPANION_SHARED_CONTRACT=true
COMPANION_DECLARED_INTENT=FRACTION_DECIMAL_0_1
COMPANION_RUNTIME_CONVERSION_PRESENT=false
COMPANION_RUNTIME_PASS_THROUGH_TO_QUANTITY_CONSUMER=true
COMPANION_MUST_NOT_REINTERPRET_AS_ABSOLUTE_UNITS=true
EFS_QUARANTINED=true
EFS_DEPRECATED=true
EFS_REMAINS_SEPARATE=true
EFS_NEW_PRODUCTIVE_SRC_CALLER_GUARD=true
FINAL_QUANTITY_PROVENANCE_RESOLVED=false
NO_SIZING_MATH_CHANGE=true
NO_FRACTION_TO_UNITS_CONVERSION=true
NO_QUANTITY_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_UNITS_DIMENSIONS_SEMANTICS_CHANGE=true
NO_TOPOLOGY_SEMANTICS_CHANGE=true
NO_CONSUMPTION_OVERWRITE_SEMANTICS_CHANGE=true
NO_RESOLUTION_AUDIT_SEMANTICS_CHANGE=true
NO_REWIRE=true
NO_DELEGATION=true
NO_EFS_REMOVAL=true
NO_SIGNAL_TO_ORDERS_MUTATION=true
NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION=true
NO_CRS_MATH_CHANGE=true
NO_NEW_PRIMARY_AUTHORITY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
RUNTIME_SEMANTICS_CHANGED=false
QUANTITY_MATH_CHANGED=false
TRADING_CORE_CHANGED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EQUITY_OWNER=UNRESOLVED
CANONICAL_PRICE_OWNER=UNRESOLVED
CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED
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
EXPECTED_COMPANION_CONFLICT_PATH_COUNT=2
EXPECTED_EFS_CONFLICT_PATH_COUNT=1
EXPECTED_EFS_PRODUCTIVE_SRC_CALLER_COUNT=0
EXPECTED_EFS_SCRIPT_OR_OFFLINE_CALLER_COUNT=2
EXPECTED_EFS_QUARANTINE_CONTRACT_COUNT=1
COMMON_UNIFIED_SEMANTICS_DECISION=NOT_TAKEN
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false
```

## Purpose

Operator-authorized freeze that:

1. Pins the **shared Companion intent** for Shadow + Live to declared `FRACTION_DECIMAL_0_1`.
2. Marks `execute_from_signals` (**EFS**) as **deprecated &#47; quarantined** separately, with a fail-closed guard against new productive `src&#47;` callers.
3. Leaves Execution &#47; Risk-Sizing authority, Equity, Price, Instrument-Metadata, and Final Quantity provenance **explicitly UNRESOLVED**.

This slice does **not**:

- convert Fraction → Units
- change quantity math, CRS math, or `signal_to_orders`
- mutate Shadow &#47; Live order generation
- remove EFS or change EFS numeric runtime semantics
- assign any canonical authority owner
- create a shared semantics authority between Companion and EFS
- activate runtime bridge, live, testnet, or orders
- claim that Fraction is already correctly converted to Units

## A. Companion shared intent freeze

| Field | Pin |
|---|---|
| Subcontract | `COMPANION_INTENT_FRACTION_DECIMAL_0_1` |
| Paths | `PATH_SHADOW_COMPANION`, `PATH_LIVE_COMPANION` |
| Topology edges | `COMPANION_SHADOW_POSITION_FRACTION`, `COMPANION_LIVE_SESSION_POSITION_FRACTION` |
| Declared intent | `FRACTION_DECIMAL_0_1` |
| Runtime conversion present | **false** |
| Runtime behavior | Pass-through of declared fraction into `signal_to_orders` (documented absolute units) |

**Runtime contradiction (explicit):** declared `FRACTION_DECIMAL_0_1` is currently passed numerically unchanged as `position_size` into `ExecutionPipeline.signal_to_orders`. Conversion is **missing**. This freeze does **not** claim conversion is present or correct.

**Anti-reinterpretation:** Docs, CLI flags, profiles, and config that declare Companion `position_fraction` as capital-share &#47; `FRACTION_DECIMAL_0_1` must **not** be silently reinterpreted as absolute Units without a separate Operator-GO.

Companion remains a sizing pass-through and is **not** a sixth primary owner.

## B. EFS quarantine (separate)

| Field | Pin |
|---|---|
| Subcontract | `EFS_DEPRECATED_QUARANTINED_PATH` |
| Path | `PATH_EXECUTE_FROM_SIGNALS` |
| Status | `DEPRECATED_QUARANTINED` |
| Productive `src&#47;` callers | **0** |
| Script &#47; offline allowlist count | **2** |

Allowlisted script &#47; offline callers (not productive `src&#47;` callers):

- `scripts&#47;run_offline_realtime_ma_crossover.py`
- `scripts&#47;run_shadow_execution.py`

**Guard:** any new productive `src&#47;**` caller of `execute_from_signals` must CI-fail.

This slice does **not** delete EFS, change its numeric semantics, or fold it into the Companion intent authority. EFS remains a separate subcontract.

## C. Authority pins (remain UNRESOLVED)

```
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EQUITY_OWNER=UNRESOLVED
CANONICAL_PRICE_OWNER=UNRESOLVED
CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED
FINAL_QUANTITY_PROVENANCE_RESOLVED=false
```

No candidate may be implicitly elevated to owner by wording or tests in this slice.

## Baseline counts (referenced, unchanged)

Frozen referenced counts remain **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3** and **27 &#47; 13 &#47; 1**, with resolved&#47;unresolved provenance **5 &#47; 3** and semantic-conflict paths **3** (Companion **2** + EFS **1**).

The new quarantine contract counts **separately** (`EXPECTED_EFS_QUARANTINE_CONTRACT_COUNT=1`) and does **not** mutate those freeze numbers.

## Drift guards (fail-closed)

Guards fail on:

- Companion intent other than `FRACTION_DECIMAL_0_1`
- silent Companion reinterpretation as absolute Units in docs &#47; CLI &#47; profiles &#47; config
- claiming Companion conversion is already present
- Companion escalation to primary owner
- EFS not quarantined &#47; deprecated
- folding EFS into Companion semantics authority
- new productive `src&#47;` EFS callers
- EFS script-allowlist drift
- EFS removal or numeric-change claims in this slice
- authority &#47; equity &#47; price &#47; instrument-metadata &#47; final-quantity owner assignment
- mutation of frozen baseline counts
- Fraction→Units conversion, quantity math, `signal_to_orders`, CRS-math, or rewire claims
- runtime-bridge &#47; live &#47; orders activation claims

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- No productive `src&#47;**` mutation in this slice

## Next

Companion declared intent is **frozen**; EFS is **quarantined**. Final Quantity Provenance remains **unresolved**. Any Fraction→Units conversion, quantity math, rename&#47;validator productive change, rewire, authority assignment, EFS deletion, or shared Companion+EFS semantics authority requires a **separate Operator-GO** (`NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false`).
