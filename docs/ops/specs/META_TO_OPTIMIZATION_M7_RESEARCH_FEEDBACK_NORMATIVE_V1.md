---
docs_token: DOCS_TOKEN_META_TO_OPTIMIZATION_M7_RESEARCH_FEEDBACK_NORMATIVE_V1
status: active
scope: M7 meta-to-optimization bounded research feedback; no search execution
capability: META_TO_OPTIMIZATION_M7_RESEARCH_FEEDBACK_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-11-22
---

# Meta → Optimization M7 — Bounded Research Feedback V1

```text
WORKPACKAGE_ID=META_TO_OPTIMIZATION_M7_RESEARCH_FEEDBACK_V1
SELF_LEARNING_UNIVERSE != OPTIMIZATION_UNIVERSE
SEARCH_EXECUTION_AUTHORIZED=false
PROPOSAL_NOT_AUTHORITY=true
```

## Flow

```text
META_LEARNING_EVIDENCE_V1
  → META_TO_OPTIMIZATION_FEEDBACK_INPUT_V1
  → BOUNDED_RESEARCH_FEEDBACK_DECISION_V1
```

Owner: `src/experiments/canonical_meta_to_optimization_feedback_v1.py`

Research dispositions are not trading, promotion, or envelope authority.
UNKNOWN M6 fields must not be synthesized; fail-closed where required.

## Non-goals

M8 replay, M9 surfaces, productive search, execution, learning_state mutation

## Transported M7 admitted at standalone cycle entries — 2026-11-22

At `56ce133616863371ab14cbfa0bab0638e8c9f9ff`, the native, MI-crossing
and federated multi-cycle orchestrators already compare an explicit prior M7
packet with the complete return of the preceding cycle. That original-source
join remains in place. Their separately callable single-cycle entries checked
only its schema before extracting applicable dispositions and search outcome.

The M7 owner now provides a shared transported-packet validator. It reuses its
original item/decision constructors, identity and result-digest formulas to
check declared classification tokens, parent/item witness, complete transport
digest and fixed top-level/item research-only declarations. JSON booleans and
numbers remain distinct. The three existing cycle entries call this owner before
their original M4, MI orchestrator or federated return-join consumer. A malformed
packet raises the existing cycle error with PRIOR_FEEDBACK_INVALID; the earlier
stale-schema rejection retains its precedence. No existing producer output is
rewritten or normalized.

Original Mapping/JSON packets, typed no-action packets with absent source,
unavailable M6 values and extra opaque annotations remain representable. A
supplied annotation is covered by the transport digest and is not interpreted
as a new effect claim. The validator does not rederive the research payload,
search choice, budget or pattern assessment without the source M6 record.
Self-consistency does not prove original source authenticity or that the packet
is the actual previous cycle's return; only the multi-cycle orchestrator has
that original available for its existing complete join.

The carried cycle_n_plus_1_input_semantics records research provenance. It does
not rewrite the caller's next experiment request or start a search, training,
trading selection or productive apply. Native plane identity, MI lineage and
federated surface execution identity retain their separate meanings. The
federated path still does not invoke M4. M6 remains a mechanical projection,
UNKNOWN_UNAVAILABLE remains unavailable, and source-ID count is not statistical
confidence. Numerical learning, economics and autonomous operation are separate
claims.

Verification: `tests/experiments/test_m7_single_cycle_feedback_admission_v1.py`.
The original-owner baseline has 39 unblocked counterexamples and six passing
preservation cases. Nine controlled original consumer results accept malformed
prior packets while completing the existing synthetic cycle; they do not grant
productive rights. Native/MI examples carry changed applicable item flags. The
federated source has no source experiment IDs: its first prioritization item stays
FAIL_CLOSED and is filtered out of carried applicable dispositions, even when its
envelope is malformed. This original filter is preserved.
Three complete native/MI/federated two-cycle/replay packets and
two synthetic source LearningState ledger files remain byte-identical. Additional
controls cover original missing/stale-source no-action and opaque annotations.
These are network-denied, temporary fixture checks, not operating sessions or a
new M7 persistence owner.
