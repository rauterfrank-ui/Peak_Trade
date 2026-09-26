# Governed Runtime G2 → M4–M8 Real Mechanical Continuation V1

```text
WORKPACKAGE_ID=GOVERNED_RUNTIME_G2_TO_M4_M8_REAL_MECHANICAL_CONTINUATION_V1
CONTINUATION_AUTHORITY=NONE
PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY=false
CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION=false
RUNTIME_APPLY_STARTED=false
REAL_RUNTIME_MATERIALIZATION_PERFORMED=false
EXTERNAL_EFFECT=false
G2_REAL_SOURCE_USED=true
DDO_FIXTURE_LEARNING_STATE_USED_ON_REAL_PATH=false
```

Owner:

- `src/governance/governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1.py`

Purpose:

Continue the proven G2 real mechanical path (#6880) into the **existing**
`run_m4_m8_evidence_return_loop_v1` orchestrator using runtime-derived
`learning_evidence_record_v1` only. DDO fixture learning state is not used on
this path.

## Direction

```text
GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1 (PROJECTED)
  → runtime_to_learning_input_v1
  → GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1
  → learning_evidence_record_v1 (runtime-derived)
  → validate_canonical_optimization_universe_learning_input_v1
  → bounded offline M4 plane request (synthetic offline research envelope)
  → run_m4_m8_evidence_return_loop_v1
  → M4–M8 cycle output (authority=NONE)
```

Reuse:

- `src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py`
- `src/experiments/canonical_m4_m8_evidence_return_loop_v1.py`
- `src/experiments/canonical_optimization_universe_experiment_plane_v1.py`

DDO `export_learning_evidence_from_state_v1` + test `_learning_state` remain
valid **fixture harness only** for isolated unit tests; they are forbidden inputs
on the real continuation request surface.

## Fail closed

Reject when G2 projection/binding fails, learning evidence is not from the G2
binding producer, DDO fixture state is supplied, canonical optimization input
rejects, plane build fails, or M4–M8 loop does not complete.

## Non-implications

Successful M4–M8 evidence return does not authorize runtime apply, productive
configuration, activation, deployment, or external effects.
