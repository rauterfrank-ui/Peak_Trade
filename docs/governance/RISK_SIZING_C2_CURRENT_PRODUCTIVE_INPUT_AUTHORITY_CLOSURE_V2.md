# Risk Sizing C2 Current Productive Input Authority Closure v2

**Status:** BINDING productive-lineage forensic closure slice (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2`  
**Workpackage:** `BOUNDED_WP_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2`  
**Machine contract:** [`config/governance/risk_sizing_c2_current_productive_input_authority_closure_v2.json`](../../config/governance/risk_sizing_c2_current_productive_input_authority_closure_v2.json)

**Bound inputs (not re-adjudicated):** PR #6760 census, PR #6761 domain authority resolution.

```
RISK_SIZING_C2_CURRENT_PRODUCTIVE_INPUT_AUTHORITY_CLOSURE_V2=true
INVENTORY_ONLY=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
C2_STATUS=UNRESOLVED
C2_CLOSURE_RULE_SATISFIED=false
CONVERSION_READY=false
MAP_AUTHORITY=NONE
```

## Purpose

Repo-wide **CURRENT productive** lineage forensics for the three C2 input families, traced to producer → transform → typed handoff → consumer → fail-closed behavior. Separates **productive wiring trace** from **C2 Companion conversion-input authority verdict** (#6761).

## C2 domain verdicts (unchanged from #6761)

| Domain | Verdict |
|--------|---------|
| ACCOUNT_EQUITY_AVAILABLE_CAPITAL | CONFLICTING |
| REFERENCE_PRICE | UNKNOWN |
| INSTRUMENT_QUANTITY_METADATA | UNRESOLVED |

Zero domains `PROVEN_CURRENT`; `C2_STATUS=UNRESOLVED`.

## Explicit non-claims

- no Companion binding or conversion math  
- no owner adjudication or `CONVERSION_READY=true`  
- no elevation of Full-Core observations to C2 authority  
- Map `AUTHORITY=NONE`
