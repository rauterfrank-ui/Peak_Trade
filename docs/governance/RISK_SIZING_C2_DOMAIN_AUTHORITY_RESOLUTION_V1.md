# Risk Sizing C2 Domain Authority Resolution v1

**Status:** BINDING forensic domain authority resolution (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_C2_DOMAIN_AUTHORITY_RESOLUTION_V1`  
**Workpackage:** `BOUNDED_WP_C2_DOMAIN_AUTHORITY_RESOLUTION_V1`  
**Machine contract:** [`config/governance/risk_sizing_c2_domain_authority_resolution_v1.json`](../../config/governance/risk_sizing_c2_domain_authority_resolution_v1.json)  
**Prior census (bindend):** [`RISK_SIZING_C2_INPUT_AUTHORITY_CLOSURE_V1.md`](RISK_SIZING_C2_INPUT_AUTHORITY_CLOSURE_V1.md) / PR #6760

```
RISK_SIZING_C2_DOMAIN_AUTHORITY_RESOLUTION_V1=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
C2_REQUIRED_INPUT_COUNT=3
C2_INPUT_SET_COMPLETE_PROVEN=true
C2_STATUS=UNRESOLVED
C2_CLOSURE_RULE_SATISFIED=false
CONVERSION_READY=false
B05_FATE_PHASE_STATUS=CLOSED
FATE_IMPLEMENTATION_EXECUTED=true
```

## Scope

Forensic resolution of the three `#6760` C2 required input domains through CURRENT Runbook, governance contracts, and code — **Companion Shadow/Live conversion-input authority only**. No fourth domain. No owner adjudication. No conversion math. No Companion runtime rewire.

## Domain verdict summary (CURRENT main @ c0995309)

| Input | Initial | Final | C2 binding implemented |
|-------|---------|-------|------------------------|
| `ACCOUNT_EQUITY_AVAILABLE_CAPITAL` | CONFLICTING | CONFLICTING | false |
| `REFERENCE_PRICE` | UNKNOWN | UNKNOWN | false |
| `INSTRUMENT_QUANTITY_METADATA` | UNRESOLVED | UNRESOLVED | false |

`C2_STATUS` remains `UNRESOLVED`: zero domains `PROVEN_CURRENT` on the Companion path.

## Explicit non-claims

- no Fraction→Units conversion  
- no `CONVERSION_READY=true`  
- no repo-wide `CANONICAL_RISK_SIZING_OWNER`  
- no elevation of Full-Core 29P equity/mark/instrument observations to Companion C2 authority  
- Map `AUTHORITY=NONE`
