# Risk / Sizing B05 Full-Core Governed Authority-Chain Closure v1

**Status:** BINDING B05 Full-Core authority-chain closure (witness + governance ratification)  
**Obligation:** `OBL_B05_FULL_CORE_GOVERNED_AUTHORITY_CHAIN_CLOSURE_V1`  
**Machine contract:** [`config/governance/risk_sizing_b05_full_core_governed_authority_chain_closure_v1.json`](../../config/governance/risk_sizing_b05_full_core_governed_authority_chain_closure_v1.json)

```
OWNER_GO=OWNER_GO_B05_FULL_CORE_GOVERNED_AUTHORITY_CHAIN_CLOSURE_V1
OWNER_GO_STATUS=CONSUMED
SCOPE_TRACK=FULL_CORE
B05_FULL_CORE_AUTHORITY_CHAIN_VERDICT=CLOSED
AUTHORITY_BINDING_IMPLEMENTED=true
AUTHORITY_BINDING_SCOPE=FULL_CORE_ENTER_LIVE_29P_CAPITAL_PATH_ONLY
OBSERVATION_IS_NOT_AUTHORITY=true
TRANSPORT_IS_NOT_AUTHORITY=true
CONVERSION_READY=false
COMPANION_C2_STATUS=UNRESOLVED
COMPANION_C2_TOUCHED=false
FRACTION_TO_UNITS_TOUCHED=false
AUTHORITY_ACTIVATION_AUTHORIZED=false
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false
```

## Account Equity (Full-Core)

```
ACCOUNT_EQUITY_AUTHORITY_OWNER=ops.governed_productive_account_equity_authority_producer_v1
ACCOUNT_EQUITY_GOVERNED_PRODUCER_CREATED=true
ACCOUNT_EQUITY_AUTHORITY_BINDING_IMPLEMENTED=true
ACCOUNT_EQUITY_AUTHORITY_CHAIN_CLOSED=true
```

## Reference Price (Full-Core)

```
REFERENCE_PRICE_AUTHORITY_OWNER=ops.governed_productive_reference_price_authority_producer_v1
REFERENCE_PRICE_SEMANTICS_CLASS_RATIFIED=mark_price
REFERENCE_PRICE_GOVERNED_PRODUCER_CREATED=true
REFERENCE_PRICE_AUTHORITY_BINDING_IMPLEMENTED=true
REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=true
```

## Instrument Metadata (Full-Core)

```
INSTRUMENT_METADATA_AUTHORITY_OWNER=ops.governed_productive_instrument_metadata_authority_producer_v1
INSTRUMENT_METADATA_GOVERNED_PRODUCER_CREATED=true
INSTRUMENT_METADATA_AUTHORITY_BINDING_IMPLEMENTED=true
INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=true
```

## Non-claims

- Companion C2 remains **UNRESOLVED**; no Companion rewire.
- No Fraction→Units conversion.
- Observation/transport/normalization are **not** authority.
- No Live/POST/Permit authorization.
