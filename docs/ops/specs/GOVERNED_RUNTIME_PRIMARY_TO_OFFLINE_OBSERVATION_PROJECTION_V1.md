# Governed Runtime Primary → Offline Observation Projection v1

```text
WORKPACKAGE_ID=GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1
PROJECTION_AUTHORITY=NONE
PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION=false
P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY=false
RUNTIME_APPLY_STARTED=false
EXTERNAL_EFFECT=false
```

Owner:

- `src/governance/governed_runtime_primary_to_offline_observation_projection_v1.py`

Purpose:

Mechanically project **preexisting durable validated** Paper / Shadow / Testnet primary
evidence into the existing offline observation / research evidence plane. This is a
**projection / normalization boundary** only.

This component is **not** a runtime executor, primary evidence producer, trading/risk/
promotion/apply owner, or Testnet/Live runner.

## Direction

```text
PREEXISTING DURABLE PRIMARY EVIDENCE (PAPER | SHADOW | TESTNET)
  → validate_durable_primary_evidence_root (scripts.ops.primary_evidence_retention_v0)
  → canonical runtime-primary identity / provenance binding
  → GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1
  → OfflineExperimentObservationsV1 + identity-bound offline observation binding
  → runtime_observation_feedback_v1 (runtime_to_learning_input_v1 ingress)
  → existing M4–M8 research return loop (fixture-bounded proof)
```

Reuse:

- `scripts/ops/primary_evidence_retention_v0.py`
- `src/experiments/canonical_identity_bound_offline_observation_binding_v1.py`
- `src/meta/learning_loop/runtime_observation_feedback_v1.py`
- `src/experiments/canonical_m4_m8_evidence_return_loop_v1.py`

Field-level adjudication:

- `config/governance/governed_runtime_primary_to_offline_observation_projection_v1_field_mapping_ledger_v1.json`

## Fail closed

Reject projection when source archive is missing, under `/tmp`, fails durable validation,
manifest verify fails, unsupported mode, mode mismatch, missing mandatory run/session
identity, instrument, observation time, or config identity where required by source mode.

Do not fabricate missing downstream fields. Do not mutate primary evidence archives.

## M10 / P5 isolation

Primary runtime evidence and this projection output do **not** authorize M10 promotion,
runtime apply, or P5 productive ingress. P5 bridges remain separate optional downstream
producers only.
