# Risk Sizing Bypass Fate Provenance Binding V1

**Status:** BINDING bypass fate provenance pins (S1–S3; all five bypass IDs)  
**Date:** 2026-09-23  
**Obligation:** `OBL_B05_BYPASS_FATE_PROVENANCE_BINDING_V1`  
**Workpackages:** `WP_B05_KEEP_PARALLEL_FATE_IMPLEMENTATION_V1`, `WP_B05_GOVERNANCE_EXCLUDE_FATE_IMPLEMENTATION_V1`, `WP_B05_RESEARCH_OR_OFFLINE_SCOPE_FATE_IMPLEMENTATION_V1`, `BOUNDED_WP_B05_BYPASS_FATE_IMPLEMENTATION_CLOSEOUT_V1`  
**Machine contract:** [`config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json`](../../config/governance/risk_sizing_bypass_fate_provenance_binding_v1.json)

```
RISK_SIZING_BYPASS_FATE_PROVENANCE_BINDING_V1=true
IMPLEMENTATION_SLICE=S1_AND_S2_AND_S3
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
RUNTIME_MUTATION_EXECUTED=false
KEEP_PARALLEL_IMPLEMENTATION_BINDING_COUNT=2
GOVERNANCE_EXCLUDE_IMPLEMENTATION_BINDING_COUNT=2
RESEARCH_OR_OFFLINE_SCOPE_IMPLEMENTATION_BINDING_COUNT=1
BYPASS_FATE_PROVENANCE_BINDING_COMPLETE_COUNT=5
FATE_IMPLEMENTATION_EXECUTED=true
B05_FATE_PHASE_STATUS=CLOSED
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

## Scope (S3)

Research/offline scope-only provenance pins for:

- `BYPASS_OFFLINE_EVAL_SIZING_CONTRACT` — `RESEARCH_OR_OFFLINE_SCOPE_ONLY` (host scope `offline_economic_evaluation`; companion `EDGE_FEEDBACK_OFFLINE_EVAL_SIZING` shares scope-only class; `OFFLINE_OR_SIMULATION_IS_NOT_AUTHORITY` preserved)

No runtime rewire, no consolidation, no canonical owner promotion.
