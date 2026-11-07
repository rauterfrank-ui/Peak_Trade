---
docs_token: DOCS_TOKEN_CURRENT_WP04_STANDING_PRE_EXTERNAL_ADMISSION_ENDGAME_DONE_GATE_V1
status: partial_runtime_admission_not_proven
authority: NONE
runtime_authorization_effect: NONE
---

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

## Current admission limits

The standing proof consumes the original boundary evidence from its own
reference session. A successful LONG/SHORT in another scenario or a historical
entry label cannot make a current HOLD session PRE_EXTERNAL. The optional
pre_external_reached input can restrict an observed result; it cannot supply a
missing result. EXIT_PATH_VALID requires a current original S5 exit with an
integrity-checked reduce-only envelope rather than a constant true flag.

Observation recovery is not complete runtime-owner recovery. Bilateral
PRE_EXTERNAL reachability therefore does not establish unified_restart_safe,
RESTART_RECOVERY_CLOSED or the full mechanical done gate. The updated integration
case verifies both actual bilateral entry reachability and refusal of the
unproven full admission. The original financial, safety and permit owners retain
their authority. The [current evidence](../evidence/WP03_CURRENT_CONSUMER_PROOF_2026_11_07.md)
separates the observed boundary from full runtime readiness and venue execution.
- `scripts/ops/write_current_wp04_closure_evidence_v1.py`

## Non-goals

- POST / live venue external effect
- `CONTINUOUS_RUN_AUTHORIZED` pin flip
- MV2 / Double Play trading semantics change
