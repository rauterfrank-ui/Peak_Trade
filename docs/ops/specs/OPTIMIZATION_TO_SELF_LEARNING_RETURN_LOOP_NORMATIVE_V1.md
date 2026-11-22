---
docs_token: DOCS_TOKEN_OPTIMIZATION_TO_SELF_LEARNING_RETURN_LOOP_NORMATIVE_V1
status: active
scope: M5 typed optimization experiment evidence return boundary to self-learning input ACK only
capability: OPTIMIZATION_TO_SELF_LEARNING_M5_RETURN_LOOP_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-22
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

## Retained M5 reproducibility scopes at admission — 2026-11-22

At `3442fe87753f922a588b03497e2bead204d89809`, M5 already has a complete
transport content_hash and the native plane/record identity check. Native ACK,
federated return join, M6 ingest, research routing and P5/D26 readers are connected.
The shared validator checked only the reproducibility_digest format. A fresh
transport hash could therefore carry a stale or contradictory reproduction claim.

The validator now reconstructs each original producer's retained digest body.
Native M5 binds plane_identity, learning_evidence_digest, the search slice's
search_identity, candidate_ref, all evidence_slices and version_bindings. A valid
projected MI lineage digest adds the original optional mi_enriched_lineage_digest
key. Its value is retained in the economic slice. No null/default MI binding is
inserted. The federated body instead binds surface_execution_identity, surface_id,
surface_execution_digest, surface_native_evidence_digest, envelope_identity,
evidence_slices and version_bindings, using retained provenance fields. It neither
creates a plane identity nor infers an experiment ID from an executor identity.

An absent/malformed reconstruction input or a mismatching digest rejects through
the existing M5 error type before return acceptance, M6 projection or downstream
envelope creation. Earlier schema, authority, slice, transport and native identity
error precedence remains. Both original producers, ID/digest formulas and valid
record bytes stay unchanged. This checks the original scopes; it does not replace
them with a hash of the whole serialized record. Unscoped top-level annotations
remain allowed under the separate full transport hash.

Verification: `tests/experiments/test_m5_reproducibility_admission_v1.py`.
The original-owner baseline contains 72 unblocked paths and 12 passing controls
across native, MI-enriched, F1 and F2 projections. Twelve recorded old-consumer
examples produce matching original ACK/join packets, complete M6 ingest and reach
Optimization research despite the contradiction. None grants productive authority.
Twelve complete valid M5/return/M6/router packets and six synthetic source
LearningState ledger files remain byte-identical, including JSON round trips and
unscoped annotations. The existing federated plane-ID negative test now refreshes
only its test transport hash so its original forbidden-plane expectation reaches
that gate. The stale-hash failure is reproduced with the old validator; the
corrected fixture also passes against that same old validator.

The gate does not independently authenticate the M4 plane, F1/F2 artifacts,
research measurements, source chronology, failure semantics or numerical quality.
Self-consistent altered records are not certified as original sources. Economic
lineage stays opaque, reference-only federated slices stay NOT_MAPPED, and M6 is
still mechanical evidence processing with UNKNOWN_UNAVAILABLE values. Its own
source-scoped digest remains a separate contract; a complete M6-body seal is not
invented. No new writer, training, search, promotion, trading or operating session
is introduced. BTC, financial rules and productive authority stay unchanged.
