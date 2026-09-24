---
docs_token: DOCS_TOKEN_FEDERATED_SURFACE_OPTIMIZATION_EXPERIMENT_EVIDENCE_PROJECTION_NORMATIVE_V1
status: active
scope: Evidence-only projection from authorized surface-native execution to shared M5 record shape
capability: FEDERATED_SURFACE_OPTIMIZATION_EXPERIMENT_EVIDENCE_PROJECTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# Federated Surface → Optimization Experiment Evidence Projection V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
WORKPACKAGE_ID=FEDERATED_SURFACE_OPTIMIZATION_EXPERIMENT_EVIDENCE_PROJECTION_V1
ARCHITECTURE_VERDICT=FEDERATED_EXECUTORS_SHARED_EVIDENCE_PLANE_REQUIRED
LEARNING_PRODUCTIVE_AUTHORITY=NONE
OPTIMIZATION_PRODUCTIVE_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
PROPOSAL_NOT_AUTHORITY=true
M4_RE_EXECUTION_FORBIDDEN=true
```

Owner: `src/experiments/canonical_federated_surface_optimization_experiment_evidence_projection_v1.py`

Decision: `config/governance/federated_surface_optimization_experiment_evidence_projection_v1_decision_v1.json`

## Purpose

Project **native authorized surface execution** artifacts into a **shared**
`canonical_optimization_experiment_evidence_v1` record shape for downstream
readers, without:

- re-running F1/F2 executors through M4 synthetic plane,
- equating `surface_execution_identity` with M4 `plane_identity`,
- equating F1 `execution_id` or F2 grid-point identity with `candidate_experiment_id`,
- synthesizing missing Search/Challenger/OOS/Robustness semantics.

## Identity (adjudicated)

| Field | Semantics |
| --- | --- |
| `surface_execution_identity` | SHA256 join root for federated projection only |
| `plane_identity` | **M4 plane only** — federated records **must omit** this field |
| `candidate_experiment_id` | Only when explicitly supplied in projection request (never inferred from F1 `execution_id`) |

## Authorized surfaces (CURRENT)

TEST_READY parameter-influence surfaces **F1** and **F2** only (`list_test_ready_surface_ids_v1`).

## Evidence slices

All seven M5 slice keys are present. Default slice body is
`SURFACE_NATIVE_REF_ONLY` with `semantic_status=NOT_MAPPED_FROM_SURFACE_EXECUTOR`
unless the caller supplies `explicit_slice_bindings` for that slice (refs/digests only).

## Out of scope

M10 ingress projection, M8 replay, F1 execution_id↔experiment_id mapping, F2 challenger,
M9-S1, productive apply/promotion, MV2/DP mutation.
