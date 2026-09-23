# Risk Sizing Bypass Fate Provenance Binding V1

**Status:** BINDING bypass fate provenance pins (S1 KEEP_PARALLEL + S2 GOVERNANCE_EXCLUDE)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_PROVENANCE_BINDING_V1`  
**Workpackages:** `WP_B05_KEEP_PARALLEL_FATE_IMPLEMENTATION_V1`, `WP_B05_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json`](../../config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json)

```
RISK_SIZING_BYPASS_FATE_PROVENANCE_BINDING_V1=true
IMPLEMENTATION_SLICE=S1_AND_S2
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
RUNTIME_MUTATION_EXECUTED=false
KEEP_PARALLEL_IMPLEMENTATION_BINDING_COUNT=2
GOVERNANCE_EXCLUDE_IMPLEMENTATION_BINDING_COUNT=2
BYPASS_FATE_PROVENANCE_BINDING_COMPLETE_COUNT=4
FATE_IMPLEMENTATION_EXECUTED=false
CONVERSION_READY=false
C2_INPUT_AUTHORITIES=UNRESOLVED
```

## Scope (S1)

Provenance/admissibility governance pins for:

- `BYPASS_CORE_POSITION_SIZER` — `KEEP_PARALLEL_NON_CANONICAL`
- `BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS` — `KEEP_PARALLEL_NON_CANONICAL`

## Scope (S2)

Governance exclude-from-system-evidence provenance pins for:

- `BYPASS_CLASSIC_BACKTEST_DEFAULT` — `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` (companion `EDGE_FEEDBACK_CALC_POSITION_SIZE` shares exclusion class)
- `BYPASS_LIVE_SHADOW_POSITION_FRACTION` — `GOVERNANCE_EXCLUDE_FROM_SYSTEM_EVIDENCE` (companion live session edge not conflated; fraction→units unresolved)

No runtime rewire, no consolidation, no canonical owner promotion.
