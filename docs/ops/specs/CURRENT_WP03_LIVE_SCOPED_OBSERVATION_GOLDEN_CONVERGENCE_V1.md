# CURRENT-WP-03 — Live-Scoped Observation Golden Convergence V1

```text
AUTHORITY=NONE
WORK_PACKAGE_ID=current_wp03_live_scoped_observation_golden_convergence_v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
```

## Purpose

Close BLK-10/BLK-11: full `GOLDEN_TRACE_KEYS` runtime projection from the standing
N=1 supervisor path; bilateral LONG/SHORT/HOLD; ≥2 contiguous C1 confirmation epochs
under scoped read-only inject transport (not live venue POST).

## Dependencies

- CURRENT-WP-01 (`n1_standing_pre_external_runtime_supervisor_v1`)
- CURRENT-WP-02 (productive default Cap22 handoff when enabled on supervisor config)

## Entrypoints

- `project_supervisor_golden_trace_v1`
- `prove_wp03_golden_convergence_v1`
- `write_current_wp03_closure_evidence_v1`
