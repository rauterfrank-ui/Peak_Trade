# Risk Sizing C2 Blocking Authorities + Canonical Sizing Owner Resolution v1

**Status:** BINDING upstream blocker adjudication (docs + static contract only)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1`  
**Workpackage:** `BOUNDED_WP_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1`  
**Machine contract:** [`config/governance/risk_sizing_c2_blocking_authorities_and_canonical_sizing_owner_resolution_v1.json`](../../config/governance/risk_sizing_c2_blocking_authorities_and_canonical_sizing_owner_resolution_v1.json)

**Bound start state:** PR #6761, #6762, #6760 — not re-derived from plausibility.

```
RISK_SIZING_C2_BLOCKING_AUTHORITIES_AND_CANONICAL_SIZING_OWNER_RESOLUTION_V1=true
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
C2_STATUS=UNRESOLVED
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CONVERSION_READY=false
CONVERSION_EXECUTED=false
MAP_AUTHORITY=NONE
```

## Upstream blocker verdicts (unchanged C2 input statuses)

| Blocker | C2 input verdict | Authority resolved |
|---------|------------------|-------------------|
| A Account equity | CONFLICTING | false |
| B Reference price | UNKNOWN | false |
| C Instrument quantity metadata | UNRESOLVED | false |
| D Canonical sizing owner | UNRESOLVED (repo-wide) | false |

`C2_CLOSURE_RULE_SATISFIED=false`. No conversion, consolidation, or Q4 adjudication in this WP.
