---
docs_token: DOCS_TOKEN_GOVERNED_F1_M9_SCOPED_OWNER_PRODUCTIVE_RUNTIME_APPLY_START_REAL_MECHANICAL_CONTINUATION_V1
status: active
scope: F1/M9 governed productive runtime apply start (600s post-#6887 lineage; no activation)
workpackage_id: GOVERNED_F1_M9_SCOPED_OWNER_PRODUCTIVE_RUNTIME_APPLY_START_REAL_MECHANICAL_CONTINUATION_V1
last_updated: 2026-09-27
---

# Governed F1/M9 Scoped Owner Productive Runtime Apply Start Real Mechanical Continuation V1

```text
WORKPACKAGE_ID=GOVERNED_F1_M9_SCOPED_OWNER_PRODUCTIVE_RUNTIME_APPLY_START_REAL_MECHANICAL_CONTINUATION_V1
GOVERNED_PRODUCTIVE_RUNTIME_APPLY_START_AUTHORIZED=true
RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS=600
REAL_P4_TO_F1_M9_JOIN_NOT_CANONICAL=true
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
EXTERNAL_EFFECT=false
```

Owner WP:
`config/governance/governed_f1_m9_scoped_owner_productive_runtime_apply_start_wp_v1_owner_decision_v1.json`

Decision:
`config/governance/governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1_decision_v1.json`

## Authority lineage (CURRENT)

Post-#6887 threshold ratification binds Owner Apply digest **3f089595…** (ratification
authorizer chain). Older handoff-only digest **c0eb6c20…** remains valid for bounded
handoff proofs but is **SUPERSEDED** for this runtime-apply-start Owner GO.

## Chain

```text
POST-6887 threshold ratification proven
  → Owner runtime-apply-start WP (600 SECONDS lineage)
  → canonical post-real campaign ingress (ratification authorizer identity)
  → digest-bound Owner Apply record (3f089595…)
  → AUTHORIZED_PRODUCTIVE_APPLY (durable ledger)
  → configuration.runtime_applied (derived; no naked boolean flip)
  → RUNTIME_APPLY_STARTED derived from successful apply execution
  → threshold value re-adjudication (e556ea63… durable record)
  → authorized productive parameter seam + presence-gate transport
  → bounded threshold enforcement readiness (#6802 decision; no global ENFORCEMENT_ENABLED)
  → STOP before Productive Activation / orchestrator consumer wiring
```

## Non-implications

- No Productive Activation
- No Real-P4 ↔ F1/M9 join
- No venue POST / credentials / permits / continuous run
- No global `ENFORCEMENT_ENABLED=true` or `PRODUCTIVE_NUMERIC_VALUES_SET>0`

## Verification

- `tests/governance/test_governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1.py`
- `tests/governance/test_f1_m9_productive_runtime_apply_start_owner_binding_v1.py`
