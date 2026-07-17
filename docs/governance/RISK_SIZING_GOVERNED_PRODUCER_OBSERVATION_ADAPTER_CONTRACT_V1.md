# Risk / Sizing Governed Producer Observation Adapter Contract v1

**Status:** BINDING semantics-free producer &#47; observation adapter contract freeze (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1`  
**Machine contract:** [`config/governance/risk_sizing_governed_producer_observation_adapter_contract_v1.json`](../../config/governance/risk_sizing_governed_producer_observation_adapter_contract_v1.json)  
**Prior authority-decision verdict:** `AUTHORITY_DECISION_CONTRACT_FROZEN_OWNERS_UNRESOLVED_CHAINS_OPEN_CONVERSION_NOT_READY`  
**Related (unchanged):** [`RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md`](RISK_SIZING_PRODUCTIVE_INPUT_PROVENANCE_BINDING_V1.md) · [`RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md`](RISK_SIZING_AUTHORITY_DECISION_CONTRACT_FREEZE_V1.md) · [`RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md`](RISK_SIZING_COMPANION_INTENT_FREEZE_AND_EFS_QUARANTINE_V1.md) · [`RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md`](RISK_SIZING_FINAL_QUANTITY_PROVENANCE_RESOLUTION_AUDIT_V1.md) · [`RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md`](RISK_SIZING_UNRESOLVED_FINAL_QUANTITY_PROVENANCE_CONTRACT_V0.md) · [`RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md`](RISK_SIZING_OUTPUT_CONSUMPTION_OVERWRITE_CONTRACT_V0.md) · [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) · [`RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md`](RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md) · [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md)

```
RISK_SIZING_GOVERNED_PRODUCER_OBSERVATION_ADAPTER_CONTRACT_V1=true
INVENTORY_ONLY=true
PRODUCER_OBSERVATION_ADAPTER_CONTRACT_FROZEN=true
ACCOUNT_EQUITY_ADAPTER_CONTRACT_FROZEN=true
REFERENCE_PRICE_ADAPTER_CONTRACT_FROZEN=true
INSTRUMENT_METADATA_ADAPTER_CONTRACT_FROZEN=true
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
NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION=true
NO_FILL_PRICE_AS_REFERENCE_PRICE_AUTHORITY=true
NO_CANDLE_CLOSE_AS_PRICE_AUTHORITY=true
NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT=true
NO_OFFLINE_OR_SIMULATION_AS_PRODUCTIVE_OBSERVATION=true
OBSERVATION_IS_NOT_AUTHORITY=true
TRANSPORT_IS_NOT_AUTHORITY=true
NORMALIZATION_IS_NOT_AUTHORITY=true
OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY=true
OBSERVATION_IS_AUTHORITY=false
TRANSPORT_IS_AUTHORITY=false
NORMALIZATION_IS_AUTHORITY=false
AUTHORITY_BINDING_IMPLEMENTED=false
PRODUCTIVE_ADAPTER_IMPLEMENTED=false
PRODUCTIVE_PRODUCER_SELECTED=false
COMPANION_REACHABLE=false
CONVERSION_CONSUMER_BOUND=false
PARTIAL_DATA_POLICY=FAIL_CLOSED
AMBIGUOUS_DIMENSION_POLICY=FAIL_CLOSED
STALE_DATA_POLICY=FAIL_CLOSED
SHADOW_BINDING_REQUIRES_SEPARATE_GO=true
LIVE_BINDING_REQUIRES_SEPARATE_GO=true
NETWORK_ACCESS_REQUIRES_SEPARATE_GO=true
EXCHANGE_ACCESS_REQUIRES_SEPARATE_GO=true
PRODUCER_IMPLEMENTATION_REQUIRES_SEPARATE_GO=true
FRACTION_TO_UNITS_REQUIRES_SEPARATE_GO=true
ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED
ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false
REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED
REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false
INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED
INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false
EXPECTED_INPUT_DOMAIN_COUNT=3
EXPECTED_ADAPTER_LAYER_COUNT=5
EXPECTED_ALLOWED_ADAPTER_ROLE_COUNT=3
EXPECTED_FORBIDDEN_ADAPTER_ROLE_COUNT=2
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
AUTHORITY_DECISION_CONTRACT_REMAINS_FROZEN=true
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

Operator-authorized **semantics-free** freeze that declares admissible future Producer &#47; Observation Adapter roles, input &#47; output contracts, provenance, freshness, and failure states for the three Companion Fraction→Units conversion input domains — **without** implementing a productive adapter, selecting a producer &#47; exchange, assigning &#47; activating authority, fetching data, rewiring callers, or converting quantities.

Input domains (exactly three):

1. `account_equity`
2. `reference_price`
3. `instrument_metadata`

## Adapter layer separation

Exactly five declared layers; only the first three are allowed contract roles in this slice:

| Layer | Authority? | This slice |
| --- | --- | --- |
| `RAW_TRANSPORT` | no | allowed role; not implemented |
| `OBSERVATION_ADAPTER` | no | allowed role; not implemented |
| `NORMALIZATION_ADAPTER` | no | allowed role; not implemented |
| `AUTHORITY_BINDING` | yes (future) | forbidden; `NOT_IMPLEMENTED` &#47; `UNRESOLVED` |
| `CONVERSION_CONSUMER` | no | forbidden; unbound |

Pins:

- `OBSERVATION_IS_AUTHORITY=false`
- `TRANSPORT_IS_AUTHORITY=false`
- `NORMALIZATION_IS_AUTHORITY=false`
- `AUTHORITY_BINDING_IMPLEMENTED=false`
- `PRODUCTIVE_ADAPTER_IMPLEMENTED=false`
- `PRODUCTIVE_PRODUCER_SELECTED=false`
- `COMPANION_REACHABLE=false`
- `CONVERSION_CONSUMER_BOUND=false`

## A. Account Equity adapter contract

- no silent selection among free &#47; total &#47; cash &#47; balance &#47; margin equity
- raw balance fields must be preserved
- normalized dimension must be explicitly named
- required: `account_id` &#47; `account_scope`, `venue`, `currency`, `observed_at` &#47; `as_of`, provenance
- missing, partial, or contradictory balance data → `FAIL_CLOSED`
- `start_balance` and simulated &#47; offline values forbidden
- Observation must not be used as running-equity Authority

Pins:

- `ACCOUNT_EQUITY_ADAPTER_CONTRACT_FROZEN=true`
- `ACCOUNT_EQUITY_AUTHORITY_OWNER=UNRESOLVED`
- `ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=false`

## B. Reference Price adapter contract

- `price_type` must be explicit; allowed observation types include at least `mark`, `index`, `last`, `candle_close`
- fill &#47; execution price is forbidden as an upstream Reference-Price Observation
- required: `instrument_id`, `venue`, `market_type`, `observed_at` &#47; `as_of`, provenance
- staleness and time-axis mismatch must be classified explicitly
- no implicit substitution among mark &#47; index &#47; last &#47; candle_close
- Observation must not be used as Sizing &#47; Conversion Authority

Pins:

- `REFERENCE_PRICE_ADAPTER_CONTRACT_FROZEN=true`
- `REFERENCE_PRICE_AUTHORITY_OWNER=UNRESOLVED`
- `REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false`
- `NO_FILL_PRICE_AS_REFERENCE_PRICE_OBSERVATION=true`

## C. Instrument Metadata adapter contract

- keep raw data and normalized fields separate
- minimum fields: `instrument_id`, `venue`, `market_type`, `base_asset`, `quote_asset`, `contract_type`, `contract_multiplier` &#47; `ctVal`, `quantity_step` &#47; `lot_size`, `min_quantity`, `min_notional`, `price_tick`, `observed_at` &#47; `as_of`, provenance
- unknown fields must not be replaced with neutral-looking defaults
- universal `multiplier=1` default remains forbidden
- partial metadata must carry completeness &#47; failure status
- Snapshot &#47; Research &#47; Config remains non-authoritative

Pins:

- `INSTRUMENT_METADATA_ADAPTER_CONTRACT_FROZEN=true`
- `INSTRUMENT_METADATA_AUTHORITY_OWNER=UNRESOLVED`
- `INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false`
- `NO_UNIVERSAL_MULTIPLIER_ONE_DEFAULT=true`

## D. Cross-cutting fail-closed policies

- `PARTIAL_DATA_POLICY=FAIL_CLOSED`
- `AMBIGUOUS_DIMENSION_POLICY=FAIL_CLOSED`
- `STALE_DATA_POLICY=FAIL_CLOSED`
- `conversion_ready=false`
- `productive_semantics_change_authorized=false`
- `authority_activation_authorized=false`
- `network_access_requires_separate_go=true`
- `exchange_access_requires_separate_go=true`
- `producer_implementation_requires_separate_go=true`
- `shadow_binding_requires_separate_go=true`
- `live_binding_requires_separate_go=true`
- `fraction_to_units_requires_separate_go=true`

## E. Consistency with prior OBL_B05 contracts

The provenance-binding contract remains authoritative for Companion input absence and continues to pin `CONVERSION_READY=false`.

The authority-decision contract remains frozen with all three owners `UNRESOLVED` and all three chains open. This adapter contract does **not** close any authority chain and does **not** authorize productive semantics change.

Baseline OBL_B05 freeze counts **5 &#47; 8 &#47; 2 &#47; 5 &#47; 2 &#47; 3** and **27 &#47; 13 &#47; 1**, resolved &#47; unresolved **5 &#47; 3**, semantic-conflict **3**, conversion-input families **3** remain unchanged.

## Binding non-claims

- no productive adapter implementation
- no producer &#47; exchange selection
- no Owner assignment or Owner activation
- no Fetch &#47; Network &#47; Exchange access
- no Companion binding or rewire
- no Fraction→Units math or Quantity &#47; OrderRequest change
- no CMC authority activation
- no Default elevation
- no Testnet &#47; Live &#47; Orders activation
- no change to enabled &#47; armed &#47; confirm-token &#47; dry-run gates
- no `src&#47;` mutation

## Next

Producer &#47; Observation Adapter contracts are **frozen**; productive adapters remain **unimplemented**, authority owners remain **UNRESOLVED**, chains remain **open**, and conversion remains **not ready**. Any productive producer implementation, network &#47; exchange access, Shadow-only binding, Fraction→Units math, or Live binding requires a **separate Operator-GO** (`NEXT_PRODUCTIVE_CONVERSION_SLICE_AUTHORIZED=false`).
