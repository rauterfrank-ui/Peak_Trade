# Governed Runtime Learning Input → Optimization Universe Learning Input Binding V1

```text
WORKPACKAGE_ID=GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1
BINDING_AUTHORITY=NONE
PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY=false
CANONICAL_LEARNING_INPUT_IMPLIES_PRODUCTIVE_ACTIVATION=false
RUNTIME_APPLY_STARTED=false
EXTERNAL_EFFECT=false
DDO_FIXTURE_REQUIRED_FOR_REAL_PATH=false
```

Owner:

- `src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py`

Purpose:

Mechanically bind **validated** `runtime_to_learning_input_v1` (G2 learning ingress) into
`learning_evidence_record_v1` and feed the **existing** canonical optimization-universe
learning-input validator. This closes the mechanical join without DDO fixture state on the
real runtime-derived path.

This component is **not** a runtime executor, DDO ledger owner, optimization search owner,
promotion/apply owner, or Testnet/Live runner.

## Direction

```text
GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1 (PROJECTED)
  → runtime_to_learning_input_v1 (LEARNING_INPUT_VALID)
  → GOVERNED_RUNTIME_LEARNING_INPUT_TO_OPTIMIZATION_UNIVERSE_LEARNING_INPUT_BINDING_V1
  → learning_evidence_record_v1 (runtime-derived projection)
  → validate_canonical_optimization_universe_learning_input_v1
  → (stop — offline research input ack only)
```

Reuse:

- `src/meta/learning_loop/runtime_observation_feedback_v1.py` (producer contract)
- `src/experiments/canonical_optimization_universe_learning_input_v1.py` (canonical consumer)
- `src/learning/deterministic_decision_outcome_v0/learning_evidence_record_v1.py` (evidence shape)

Field-level adjudication:

- `config/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1_field_mapping_ledger_v1.json`

## Fail closed

Reject binding when runtime learning input is invalid, digest/integrity mismatch, provenance
alignment fails, projection digest missing, DDO fixture state is supplied to the binder,
forbidden productive/search/envelope flags are set, or canonical optimization input rejects.

Do not fabricate missing provenance. Do not fall back to DDO fixture state.

## M10 / apply isolation

Canonical optimization learning input construction does **not** authorize runtime apply,
productive activation, or external effects. M4–M8 full return loop may remain fixture-bounded
separately.
