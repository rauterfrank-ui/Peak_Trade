# Risk Sizing Bypass Fate Provenance Binding V1

**Status:** BINDING bypass fate provenance pins (S1 KEEP_PARALLEL implementation)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_PROVENANCE_BINDING_V1`  
**Workpackage:** `WP_B05_KEEP_PARALLEL_FATE_IMPLEMENTATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json`](../../config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json)

```
RISK_SIZING_BYPASS_FATE_PROVENANCE_BINDING_V1=true
IMPLEMENTATION_SLICE=S1
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
RUNTIME_MUTATION_EXECUTED=false
KEEP_PARALLEL_IMPLEMENTATION_BINDING_COUNT=2
FATE_IMPLEMENTATION_EXECUTED=false
CONVERSION_READY=false
C2_INPUT_AUTHORITIES=UNRESOLVED
```

## Scope (S1)

Provenance/admissibility governance pins for:

- `BYPASS_CORE_POSITION_SIZER` — `KEEP_PARALLEL_NON_CANONICAL`
- `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` — `KEEP_PARALLEL_NON_CANONICAL`

No runtime rewire, no consolidation, no canonical owner promotion.
