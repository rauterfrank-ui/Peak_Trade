---
docs_token: DOCS_TOKEN_GOVERNED_F1_M9_SCOPED_OWNER_APPLY_EXECUTION_REAL_MECHANICAL_CONTINUATION_V1
status: active
scope: Real P4 boundary + canonical F1/M9 scoped Owner Apply execution proof
workpackage_id: GOVERNED_F1_M9_SCOPED_OWNER_APPLY_EXECUTION_REAL_MECHANICAL_CONTINUATION_V1
last_updated: 2026-09-27
---

# Governed F1/M9 Scoped Owner Apply Execution Real Mechanical Continuation V1

```text
WORKPACKAGE_ID=GOVERNED_F1_M9_SCOPED_OWNER_APPLY_EXECUTION_REAL_MECHANICAL_CONTINUATION_V1
F1_M9_SCOPED_OWNER_APPLY_EXECUTION_AUTHORIZED=true
REAL_P4_TO_F1_M9_JOIN_NOT_CANONICAL=true
RUNTIME_APPLY_STARTED=false
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
EXTERNAL_EFFECT=false
```

Owner WP:
`config/governance/governed_f1_m9_scoped_owner_apply_execution_wp_v1_owner_decision_v1.json`

Decision:
`config/governance/governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1_decision_v1.json`

## Planes (no merge)

| Plane | Evidence | Apply owner |
|-------|----------|-------------|
| Real-P4 seam materialization (#6885) | `governed_runtime_apply_materialization_record_v1` | `GOVERNED_RUNTIME_APPLY_MATERIALIZATION_V1` |
| F1/M9 per-ingress Apply | `governed_productive_configuration_v1` + Owner Apply record | `f1_m9_scoped_owner_apply_authority_v1` |

Cross-plane join is **fail-closed** (`real_p4_to_f1_m9_apply_lineage_join_v1`).

## Direction

```text
run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1 (real)
  → evaluate_real_p4_to_f1_m9_apply_join_v1 (DENY)
  → evaluate_f1_m9_productive_apply_execution_boundary_v1 (EXECUTION_PROOF)
  → runtime_applied=true on configuration (scoped); STOP before Productive Activation
```

## Value authority

Owner explicit ingress binds `candidate_parameter_value_digest`. Threshold hot-path
ratification remains separate (`VALUE_RATIFICATION_REQUIRED_FOR_THRESHOLD_HOT_PATH=true`).

## Non-implications

- No Real-P4 → F1/M9 automatic join
- No threshold hot-path numeric ratification
- No Component B / venue POST / credentials / permits

## Verification

- `tests/governance/test_governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1.py`
- `tests/governance/test_real_p4_to_f1_m9_apply_lineage_join_v1.py`
