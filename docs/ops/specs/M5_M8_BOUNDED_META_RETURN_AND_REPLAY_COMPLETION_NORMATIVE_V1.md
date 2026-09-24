---
docs_token: DOCS_TOKEN_M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_NORMATIVE_V1
status: active
scope: Federated M5→M6 return join and bounded M6→M7→M8 offline replay without M4 re-execution
capability: M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-24
---

# M5–M8 Bounded Meta Return and Replay Completion V1

```text
WORKPACKAGE_ID=M5_M8_BOUNDED_META_RETURN_AND_REPLAY_COMPLETION_V1
M4_RE_EXECUTION_FORBIDDEN=true
JOIN_KEY=SURFACE_EXECUTION_IDENTITY
JOIN_CARDINALITY=ONE_TO_ONE_FAIL_CLOSED
META_EVIDENCE_AUTHORITY=NONE
SEARCH_EXECUTION_AUTHORIZED=false
LEARNING_STATE_MUTATION_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Purpose

Close the federated evidence loop opened by
`FEDERATED_SURFACE_OPTIMIZATION_EXPERIMENT_EVIDENCE_PROJECTION_V1` (#6792):

```text
Federated M5 record (surface_execution_identity, no plane_identity)
  → M5→M6 typed return join
  → M6 meta-learning evidence (evidence-only)
  → M7 bounded research feedback
  → M8 multi-cycle offline replay (fixture-bounded, no M4 plane)
```

## Owners

| Stage | Module |
| --- | --- |
| G1 M5→M6 join | `src/experiments/canonical_federated_m5_m6_return_join_v1.py` |
| G2 M6 federated meta evidence | `src/experiments/canonical_meta_learning_ingest_v1.py` |
| G3 M7 | `src/experiments/canonical_meta_to_optimization_feedback_v1.py` (reuse) |
| G4 M8 federated replay | `src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py` |

Decision: `config/governance/m5_m8_bounded_meta_return_and_replay_completion_v1_decision_v1.json`

## Identity (adjudicated)

| Field | Federated M5→M6 join |
| --- | --- |
| `surface_execution_identity` | Sole authorized join key; 1:1 with one M5 record per join request |
| `plane_identity` | **Forbidden** on federated records; must not be coalesced with surface identity |
| `candidate_experiment_id` | Optional; never inferred from F1 `execution_id` |

## Non-goals

M4 plane re-execution, M9/M10/M11, promotion, trading/selection authority,
productive parameter mutation, external API/order effects.
