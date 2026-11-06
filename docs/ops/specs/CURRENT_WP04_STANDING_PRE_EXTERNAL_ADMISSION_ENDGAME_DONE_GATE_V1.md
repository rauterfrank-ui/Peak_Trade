# CURRENT-WP-04 — Standing PRE_EXTERNAL Admission and Endgame Done Gate V1

```text
AUTHORITY=NONE
WORK_PACKAGE_ID=current_wp04_standing_pre_external_admission_endgame_done_gate_v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
```

## Purpose

Close EDG-034 / EDG-042 and blueprint §12: regenerate standing PRE_EXTERNAL autonomy
admission with WP-01..03 runtime/scoped semantics, record CI admission snapshot, and
evaluate `CURRENT_N1_ENDGAME_DONE_GATE` (program-level; not POST activation).

## Dependencies

- CURRENT-WP-01 (`n1_standing_pre_external_runtime_supervisor_v1`)
- CURRENT-WP-02 (productive default Cap22 handoff)
- CURRENT-WP-03 (live-scoped golden convergence evidence)

## Entrypoints

- `prove_current_wp04_package_v1`
- `write_standing_pre_external_autonomy_admission_evidence_v1`
- `write_current_wp04_closure_evidence_v1`
- `scripts/ops/write_current_wp04_closure_evidence_v1.py`

## Non-goals

- POST / live venue external effect
- `CONTINUOUS_RUN_AUTHORIZED` pin flip
- MV2 / Double Play trading semantics change
