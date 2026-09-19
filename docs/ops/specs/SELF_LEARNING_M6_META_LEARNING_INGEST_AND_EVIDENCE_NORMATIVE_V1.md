---
docs_token: DOCS_TOKEN_SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_NORMATIVE_V1
status: active
scope: M6 meta-learning ingest from M5 optimization experiment evidence; evidence only
capability: SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Self-Learning M6 — Meta-Learning Ingest and Evidence V1

```text
WORKPACKAGE_ID=SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_V1
META_EVIDENCE_AUTHORITY=NONE
LEARNING_STATE_MUTATION_AUTHORIZED=false
CANONICAL_META_LEARNING_V1_EXECUTOR=NOT_INVOKED_IN_M6
```

## Flow

```text
ACCEPTED_OFFLINE_EVIDENCE_INPUT (M5)
  → META_LEARNING_INGEST_V1
  → META_LEARNING_EVIDENCE_V1
```

Owners:

- `src/learning/deterministic_decision_outcome_v0/meta_learning_evidence_v1.py`
- `src/learning/deterministic_decision_outcome_v0/meta_learning_ingest_v1.py`

Bounded reuse: `canonical_meta_learning_v1` constants/lineage refs only — not the Phase-11 analyzer executor.

## Non-goals

M7–M9, learning_state mutation, search execution, promotion, trading
