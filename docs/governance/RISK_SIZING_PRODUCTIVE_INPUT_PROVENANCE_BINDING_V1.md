# Risk / Sizing Productive Input Provenance Binding v1

**Status:** BINDING semantics-free provenance-binding freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1`  
**Machine contract:** [`config/governance/risk_sizing_productive_input_provenance_binding_v1.json`](../../config/governance/risk_sizing_productive_input_provenance_binding_v1.json)  
**Related (unchanged):** [`RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md`](RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md) · [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md) · [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) · [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md)

```
RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1=true
INVENTORY_ONLY=true
PROVENANCE_BINDING_FROZEN=true
CONVERSION_READY=false
CONVERSION_MATH_ADDED=false
PRODUCTIVE_CALLER_REWIRED=false
OWNER_ASSIGNED=false
PRODUCTIVE_DEFAULT_COUNT=0
NO_PRODUCTIVE_DEFAULTS=true
NO_FRACTION_TO_UNITS_CONVERSION=true
NO_QUANTITY_MATH_CHANGE=true
NO_SIZING_MATH_CHANGE=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_REWIRE=true
NO_SIGNAL_TO_ORDERS_MUTATION=true
NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION=true
NO_CRS_MATH_CHANGE=true
NO_LEVERAGE_MULTIPLICATION=true
NO_MARGIN_MODE_MULTIPLICATION=true
NO_START_BALANCE_AS_RUNNING_EQUITY=true
NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true
NO_CMC_MARK_AS_PRICE_AUTHORITY=true
NO_REPLAY_STATE_AS_LIVE_AUTHORITY=true
NO_VENUE_SNAPSHOT_AS_LIVE_AUTHORITY=true
NO_MONITOR_BALANCE_AS_EQUITY_AUTHORITY=true
COMPANION_INTENT=FRACTION_DECIMAL_0_1
COMPANION_PASS_THROUGH_UNCHANGED=true
COMPANION_RUNTIME_CONVERSION_PRESENT=false
SHADOW_LIVE_INPUT_PARITY=PARITY_ON_ABSENCE
EQUITY_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING
PRICE_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING
INSTRUMENT_METADATA_PROVENANCE_STATUS=REQUIRED_INPUT_MISSING
ACCOUNT_BINDING_STATUS=UNRESOLVED
VENUE_BINDING_STATUS=UNRESOLVED
INSTRUMENT_BINDING_STATUS=UNRESOLVED
FRESHNESS_CONTRACT_STATUS=FAIL_CLOSED_MISSING
CRS_CONSUMES_INPUTS_DOES_NOT_OWN_VENUE_ACCOUNT_TRUTH=true
EFS_QUARANTINED=true
RUNTIME_BRIDGE_ACTIVATED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
RUNTIME_SEMANTICS_CHANGED=false
QUANTITY_MATH_CHANGED=false
TRADING_CORE_CHANGED=false
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
CANONICAL_EQUITY_OWNER=UNRESOLVED
CANONICAL_PRICE_OWNER=UNRESOLVED
CANONICAL_INSTRUMENT_METADATA_OWNER=UNRESOLVED
FINAL_QUANTITY_PROVENANCE_RESOLVED=false
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
EXPECTED_CONVERSION_INPUT_FAMILY_COUNT=3
EXPECTED_EQUITY_CANDIDATE_COUNT=4
EXPECTED_PRICE_CANDIDATE_COUNT=4
EXPECTED_INSTRUMENT_METADATA_CANDIDATE_COUNT=4
EXPECTED_AUTHORITATIVE_PRODUCTIVE_SOURCE_COUNT=0
EXPECTED_PRODUCTIVE_DEFAULT_COUNT=0
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false
```

## Purpose

Operator-authorized **semantics-free** freeze that models closed provenance contracts for the three Companion Shadow &#47; Live conversion inputs **without** assigning owners, converting Fraction→Units, or rewiring runtime callers.

Required input families:

1. Account Equity &#47; Available Capital
2. Reference Price
3. Instrument Quantity Metadata (`lot_size` &#47; `quantity_step`, `min_qty`, `min_notional`, `contract_multiplier`, base &#47; quote or instrument dimensions, source-timestamp &#47; freshness)

## A. Per-input provenance record

Each input record pins at least:

| Field | Role |
|---|---|
| `semantic_name` | Declared meaning |
| `dimension_unit` | Declared unit &#47; dimension |
| `producer_source_identity` | Bound producer identity or `NONE_PRODUCTIVE_ON_COMPANION_PATH` |
| `observation_vs_authority` | Observation vs authority classification |
| `environment_scope` | offline &#47; shadow &#47; testnet &#47; live |
| `as_of_source_timestamp` | Source timestamp or `null` when missing |
| `freshness_policy_status` | Freshness status |
| `instrument_account_binding` | Binding status |
| `authority_status` | Authority pin (`UNRESOLVED` unless proven) |
| `provenance_completeness` | Completeness class |
| `fail_closed_reason` | Deterministic reason code |

Frozen Companion statuses:

| Input | Status | Reason |
|---|---|---|
| Equity | `REQUIRED_INPUT_MISSING` | `EQUITY_PROVENANCE_MISSING_ON_COMPANION_PATH` |
| Reference Price | `REQUIRED_INPUT_MISSING` | `REFERENCE_PRICE_PROVENANCE_MISSING_ON_COMPANION_PATH` |
| Instrument Metadata | `REQUIRED_INPUT_MISSING` | `INSTRUMENT_METADATA_PROVENANCE_MISSING_OR_STALE_ON_COMPANION_PATH` |

## B. Aggregated Companion conversion-input binding

Binding id: `COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1`

`conversion_ready=true` is allowed **only** when all of the following hold:

- Equity provenance closed and dimension-clear
- Reference-price provenance closed and instrument-bound
- Instrument metadata complete and freshness-conformant
- All three inputs share the same account &#47; venue &#47; instrument context
- No simulation &#47; default source is used on Shadow &#47; Live

Current pin: **`conversion_ready=false`**.

## C. Fail-closed rules

Missing, multiple, observation-only, stale, mismatched, or non-authoritative sources yield:

- status `UNRESOLVED` or `REQUIRED_INPUT_MISSING`
- `conversion_ready=false`
- deterministic reason code
- **no** fallback and **no** productive default

Explicitly forbidden elevations without a proven authority contract:

- `start_balance` as running equity
- `candle.close` as price authority
- CMC `mark_price` as price authority
- Replay state as live authority
- Venue capability snapshot as live authority
- Portfolio-monitor balance as equity authority

## D. Companion pass-through reality freeze

- Intent remains `FRACTION_DECIMAL_0_1`
- `ExecutionPipeline.signal_to_orders` passes `position_size` unchanged into `OrderRequest.quantity`
- No productive conversion handoff is present
- Shadow and Live keep **parity on absence** of the three conversion inputs (`SHADOW_LIVE_INPUT_PARITY=PARITY_ON_ABSENCE`)

## E. CRS consumer role

CRS (`evaluate_capital_risk_sizing_v1`) **consumes** `account_equity`, `reference_price`, and instrument quantity constraints for offline math. CRS does **not** own venue &#47; account truth and is **not** imported by Companion Shadow &#47; Live quantity generation.

## F. Safety pins

- EFS remains quarantined
- Runtime bridge remains deactivated
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Canonical Execution &#47; Risk-Sizing &#47; Equity &#47; Price &#47; Instrument-Metadata owners remain `UNRESOLVED`
- Baseline OBL_B05 freeze counts **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3** and **27 &#47; 13 &#47; 1**, resolved &#47; unresolved **5 &#47; 3**, semantic-conflict **3** remain unchanged

## Binding non-claims

- no Fraction→Units math
- no Shadow &#47; Live &#47; `signal_to_orders` &#47; `OrderRequest` rewire
- no productive defaults or fallbacks
- no leverage &#47; margin multiplication
- no owner assignment by documentation alone
- no elevation of observation &#47; simulation &#47; offline candidates to canonical authority

## Next

Provenance-binding contracts are **frozen**; conversion remains **not ready** (`CONVERSION_READY=false`). Any productive producer binding, authority assignment, Fraction→Units math, or caller rewire requires a **separate Operator-GO** (`NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false`).
