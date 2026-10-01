---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_CONTRACT_V1
---

# CURRENT MF N≤5 Instrument Runtime Identity Closure Contract V1

OWNER=ops.current_mf_n5_instrument_runtime_identity_closure_v1  
CONTRACT_ID=CURRENT_MF_N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_CONTRACT_V1  
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK  
RUNTIME_AUTHORIZATION_EFFECT=NONE  
N_GT_1_ACTIVATION=OUT_OF_SCOPE  

## Purpose

Close DD-06 D1–D6 capability gaps for instrument-correct MF_N5 lane isolation without
granting Cap23 selection, Cap24 bind-only inversion, MF_N5 trading authority, or POST.

## Derived identity (carry-only)

`OccupiedLaneRuntimeInstrumentIdentityV1` reuses `BoundInstrumentLaneIdentityV1` from
hard-facts closure; selection lineage fields are copied from `BoundInstrumentV1` for audit only.

## Surfaces

| Delta | Owner module |
|-------|----------------|
| D1 per-lane C1 | `c1_fanout_v1` + N1 consumer wiring |
| D2 per-lane position | `position_truth_v1` + `extract_position_truth_v1` |
| D3 ownership | `ownership_v1` |
| D4 lane generation | `lane_generation_v1` |
| D5 lifecycle pins | `lifecycle_v1` + orchestrator membership pin |
| D6 reconciliation admission | `reconciliation_admission_v1` |

## Evidence

`evidence/ops/n5_instrument_runtime_identity_closure_v1/IMPLEMENTATION_EVIDENCE_V1.md`
