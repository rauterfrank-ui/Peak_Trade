---
docs_token: DOCS_TOKEN_SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_NORMATIVE_V1
status: active
scope: M6 meta-learning ingest from M5 optimization experiment evidence; evidence only
capability: SELF_LEARNING_M6_META_LEARNING_INGEST_AND_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-22
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
- `src/experiments/canonical_meta_learning_ingest_v1.py`

Bounded reuse: `canonical_meta_learning_v1` constants/lineage refs only — not the Phase-11 analyzer executor.

## Non-goals

M7–M9, learning_state mutation, search execution, promotion, trading

## Native typed M6 admission — 2026-11-22

At baseline `a3338b44d8ded26029a6888545c1717b20cc3fde`, ordinary/federated
M6 producers, the typed router and separate bounded Optimization/Learning
research consumers are connected. The producer emits this M6 domain,
SELF_LEARNING_UNIVERSE/META_LEARNING_EVIDENCE labels and evidence-only processing
claims. These are already present in the original frozen construction. Native
validation previously required a domain field without checking its value, treated
bool as an integer support count and checked only three literal True flags.

The existing validator now requires the original M6 domain and a nonnegative
integer support_count that is not bool. The original length agreement with
source_experiment_ids remains. Optional universe/evidence labels, when supplied,
must match the producer's types and values. Supplied processing/external-effect
claims must be actual False booleans; proposal_not_authority must be actual True.
The original three forbidden-True error codes remain. Missing or null optional
metadata remains missing/null; no default label or effect claim is inserted.

These flags describe M6's own evidence processing. They do not assert that the
upstream synthetic M4 research never searched or evaluated. M6 remains a
mechanical projection, with the numerical analyzer not invoked and unavailable
features/uncertainty retained as UNKNOWN_UNAVAILABLE. The support count is a
declared source-ID count, not independent sample size or statistical confidence.

Verification: `tests/learning/test_meta_learning_typed_admission_v1.py`.
The original-source baseline contains 36 unblocked paths across native validation,
both direct research consumers and routing, plus nine passing preservation cases.
Three native-owner records with controlled changed declarations reach both routes
and both bounded research decisions under unchanged M6 IDs/digests. Productive
effect remains false/zero at those consumers; no real authority grant is claimed.
Six complete valid M6/admission/routing/replay packets and six synthetic source
ledger files remain byte-identical. Optional absence/nulls, annotations, unknown
values and UNKNOWN/MIXED no-feedback routing retain their meanings.

The reproducibility digest retains its original source scope. Its producer uses
original search/integrity/lineage fields that the reduced M6 record does not
retain completely. This gate neither invents a replacement digest nor certifies
all serialized M6 content. Original producers, IDs, routing classes, consumer
decisions, numeric methods, units, writers and productive authority are unchanged.
The gate establishes declared namespace/type/evidence-only coherence, not source
authenticity, correct optimization findings, numerical learning, account PnL or
whole-system operation. No historical record is rewritten or retroactively
source-certified. All evidence is synthetic, temporary and network-denied.
