# Risk / Sizing Authority Decision Contract Freeze v1

**Status:** BINDING semantics-free authority-decision contract freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_AUTHORITY_DECISION_CONTRACT_FREEZE_V1`  
**Machine contract:** [`config/governance/risk_sizing_authority_decision_contract_freeze_v1.json`](../../config/governance/risk_sizing_authority_decision_contract_freeze_v1.json)  
**Prior audit verdict:** `NO_CLOSED_PRODUCTIVE_AUTHORITY_CHAIN_FOR_ANY_OF_THREE_INPUTS_AUTHORITY_DECISION_REQUIRED`  
**Related (unchanged):** [`RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md`](RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md) · [`RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md`](RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md) · [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md) · [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) · [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md)

```
RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1=true
INVENTORY_ONLY=true
AUTHORITY_DECISION_CONTRACT_FROZEN=true
CONVERSION_READY=false
PRODUCTIVE_SEMANTICS_CHANGE_AUTHORIZED=false
AUTHORITY_ACTIVATION_AUTHORIZED=false
OWNER_ASSIGNED=false
OWNER_ACTIVATED=false
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_ACTIVATION=true
NO_FRACTION_TO_UNITS_CONVERSION=true
NO_QUANTITY_MATH_CHANGE=true
NO_SIZING_MATH_CHANGE=true
NO_REWIRE=true
NO_COMPANION_BINDING=true
NO_FETCH=true
NO_NETWORK_ACCESS=true
NO_EXCHANGE_ACCESS=true
NO_SIGNAL_TO_ORDERS_MUTATION=true
NO_SHADOW_LIVE_ORDER_GENERATION_MUTATION=true
NO_CRS_MATH_CHANGE=true
NO_CMC_AUTHORITY_ACTIVATION=true
NO_DEFAULT_ELEVATION=true
NO_START_BALANCE_AS_RUNNING_EQUITY=true
NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY=true
NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true
NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT=true
OBSERVATION_IS_NOT_AUTHORITY=true
TRANSPORT_IS_NOT_AUTHORITY=true
OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY=true
SHADOW_BINDING_REQUIRES_SEPARATE_GO=true
LIVE_BINDING_REQUIRES_SEPARATE_GO=true
NETWORK_ACCESS_REQUIRES_SEPARATE_GO=true
EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO=true
FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO=true
ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED
ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false
REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED
REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false
INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED
INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false
EXPECTED_INPUT_DOMAIN_COUNT=3
EXPECTED_AUTHORITY_OWNER_ASSIGNED_COUNT=0
EXPECTED_AUTHORITY_CHAIN_CLOSED_COUNT=0
EXPECTED_PRODUCTIVE_PRODUCER_COUNT=0
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
PROVENANCE_BINDING_REMAINS_CONVERSION_NOT_READY=true
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
EXPECTED_CONVERSION_INPUT_FAMILY_COUNT=3
NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false
```

## Purpose

Operator-authorized **semantics-free** freeze that declares which fachliche Dimension, Provenance, Freshness, and Producer class would be **admissible in principle** for the three Companion Fraction→Units conversion input domains — **without** assigning or activating any productive authority owner, fetching data, rewiring callers, or converting quantities.

Input domains (exactly three):

1. Account Equity
2. Reference Price
3. Instrument Metadata

## A. Account Equity

**Allowed dimension:** `RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING` (capital-currency scalar for the bound account &#47; venue).

Must **not** be mixed with:

- free balance
- cash balance
- balance total &#47; wallet balance
- margin equity without an explicit equity authority contract
- initial &#47; start balance
- simulated &#47; offline equity

**Forbidden elevations:**

- `start_balance` as running equity
- offline &#47; backtest defaults and state files
- exchange &#47; portfolio-monitor values (remain Observation &#47; Transport without Authority)

Pins:

- `ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED`
- `ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false`

## B. Reference Price

**Allowed dimension:** `INSTRUMENT_VENUE_TIME_BOUND_CONVERSION_REFERENCE_PRICE` with required bindings for instrument, venue, as-of time, and an explicit `price_semantics_class`.

The following must remain **distinct** (no implicit synonymization):

- `candle.close`
- ticker last
- mark price
- index price
- fill &#47; execution price

**Forbidden elevations:**

- `candle.close` remains Observation and must not silently activate as a Quantity input
- fill &#47; execution price as upstream conversion reference-price authority
- CMC `is_authority=false` and other non-authoritizing sources

Pins:

- `REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED`
- `REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false`

## C. Instrument Metadata

**Required metadata fields &#47; dimensions (minimum):**

- `instrument_id`, `venue`, `market_type`, `base_asset`, `quote_asset`
- `contract_type` &#47; linear-inverse, `contract_multiplier` &#47; `ctVal`
- `quantity_step` &#47; `lot_size`, `min_quantity`, `min_notional`
- `price_tick` when required for normalization
- `observed_at` &#47; `as_of`, freshness &#47; TTL, provenance

**Forbidden elevations:**

- partial offline, config, snapshot, or research data
- `multiplier=1` as a universal silent default

Pins:

- no productive producer present
- `INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED`
- `INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false`

## D. Cross-cutting fail-closed pins

- `observation_is_not_authority=true`
- `transport_is_not_authority=true`
- `offline_or_simulation_is_not_authority=true`
- `shadow_binding_requires_separate_go=true`
- `live_binding_requires_separate_go=true`
- `network_access_requires_separate_go=true`
- `exchange_access_requires_separate_go=true`
- `fraction_to_units_requires_separate_go=true`
- `conversion_ready=false`
- `productive_semantics_change_authorized=false`
- `authority_activation_authorized=false`

## E. Consistency with provenance binding

The prior provenance-binding contract remains authoritative for Companion input absence and continues to pin `CONVERSION_READY=false`. This freeze does **not** close any authority chain and does **not** authorize productive semantics change.

Baseline OBL_B05 freeze counts **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3** and **27 &#47; 13 &#47; 1**, resolved &#47; unresolved **5 &#47; 3**, semantic-conflict **3**, conversion-input families **3** remain unchanged.

## Binding non-claims

- no Owner assignment or Owner activation
- no Fetch &#47; Network &#47; Exchange access
- no Companion binding or rewire
- no Fraction→Units math or Quantity &#47; OrderRequest change
- no CMC authority activation
- no Default elevation
- no Testnet &#47; Live &#47; Orders activation
- no change to enabled &#47; armed &#47; confirm-token &#47; dry-run gates

## Next

Authority-decision contracts are **frozen**; chains remain **open** and conversion remains **not ready**. Any producer adapter, freshness &#47; context binding, Shadow-only binding, Fraction→Units math, or Live binding requires a **separate Operator-GO** (`NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false`).
