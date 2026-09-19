---
docs_token: DOCS_TOKEN_OPTIMIZATION_TO_SELF_LEARNING_RETURN_LOOP_NORMATIVE_V1
status: active
scope: M5 typed optimization experiment evidence return boundary to self-learning input ACK only
capability: OPTIMIZATION_TO_SELF_LEARNING_M5_RETURN_LOOP_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Optimization → Self-Learning Return Loop V1 (M5)

```text
WORKPACKAGE_ID=OPTIMIZATION_TO_SELF_LEARNING_M5_RETURN_LOOP_V1
SELF_LEARNING_UNIVERSE != OPTIMIZATION_UNIVERSE
LEARNING_STATE_MUTATION_AUTHORIZED=false
META_LEARNING_INGEST_AUTHORIZED=false
RETURN_ACK=ACCEPTED_OFFLINE_EVIDENCE_INPUT_ONLY
```

## Flow

```text
M4_EXPERIMENT_PLANE_RESULT
  → OPTIMIZATION_EXPERIMENT_EVIDENCE_V1
  → SELF_LEARNING_RETURN_INPUT_VALIDATION
  → ACCEPTED_OFFLINE_EVIDENCE_INPUT (no state mutation)
```

Owners:

- `src/experiments/canonical_optimization_experiment_evidence_v1.py`
- `src/experiments/canonical_self_learning_optimization_return_input_v1.py`

Evidence transfer is not authority, promotion, or shared universe state.

## Non-goals

M6–M9, learning_state mutation, search feedback, promotion, execution
