# MASTER V2 — Failure Taxonomy Safe Fallbacks v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-20
owner: Peak_Trade
purpose: Canonical docs-only failure taxonomy and safe-fallback mapping for Master V2
docs_token: DOCS_TOKEN_MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1

## 1) Executive Summary

This specification materializes one compact, canonical failure, fallback, and rollback-semantics view for Master V2.

It is mapping-only and non-authorizing. It improves failure readability and auditability, but it does not grant runtime permission or live authorization.

## 2) Scope and Non-Goals

In scope:

- canonical failure, safe-fallback, and rollback semantics for Master V2 interpretation layers
- failure-class mapping across key Master V2 layers with evidence and clarity labeling
- explicit boundaries to authority, gate status, safety, and provenance surfaces

Out of scope:

- runtime rewiring or implementation changes
- live authorization
- gate closure by assertion

## 3) Canonical Failure Classes

This taxonomy uses these canonical classes:

- input/data-quality failure
- market-eligibility failure
- directional-evaluation ambiguity/failure
- scope/capital-envelope failure
- downstream risk-cap breach
- safety and kill-switch veto
- promotion-blocking failure
- learning/model/policy approval-boundary failure
- evidence/provenance gap
- operator-visibility/audit-surface failure

## 4) Failure Taxonomy Table

| layer | failure class | trigger / condition | detector / observer | blocking / veto point | safe fallback | rollback / safe retreat implication | nearest repo evidence | current clarity |
|---|---|---|---|---|---|---|---|---|
| intake and context | input/data-quality failure | stale, inconsistent, or incomplete input context for interpretation | operator review, documented evidence checks, read-model claim discipline | progression remains blocked when ambiguity persists | conservative no-trade interpretation and hold posture | retain prior bounded posture; do not promote state | [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md), [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md) | partial |
| universe and eligibility | market-eligibility failure | eligibility synthesis lacks clear authority or evidence continuity | eligibility-stage review in authority and dataflow surfaces | governance and risk can block deployability | keep candidate out of deployable path | revert to non-promoted eligibility set | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md) | partial |
| directional core | directional-evaluation ambiguity/failure | unclear directional ownership or semantic collision | authority-map ambiguity checks and vocabulary boundary checks | downstream risk and safety veto can block path | conservative no-trade or non-promotion continuation | stay in current stage; no transition escalation | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | partial |
| scope and capital | scope/capital-envelope failure | scope semantics unclear or collapsed into generic risk limits | scope clarification review and authority-map checks | unclear scope ownership blocks confident promotion | keep deployable scope conservative and bounded | remain in prior promotion stage until clarified | [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | partial |
| risk enforcement | downstream risk-cap breach | cap limits exceeded or enforcement denies progression | risk-cap interpretation and enforcement visibility surfaces | risk limit enforcement blocks downstream actions | enforce bounded no-go for exceeding path | retreat to lower-risk posture and non-promotion state | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | partial to strong |
| safety boundary | safety and kill-switch veto | safety trigger, emergency condition, or fail-closed ambiguity | safety and governance observers; incident runbook posture | primary fail-closed veto boundary | immediate safe stop and no-trade posture | rollback to blocked state and recovery runbook path | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md) | strong |
| promotion progression | promotion-blocking failure | readiness visible but transition permission or authority remains incomplete | promotion-state and gate-status interpretation surfaces | promotion remains blocked despite visible status | remain live-gated or lower stage without authorization escalation | explicit non-promotion continuation | [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md), [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md) | partial |
| learning and policy boundary | learning/model/policy approval-boundary failure | model or policy change lacks consolidated approval chain | learning inventory plus authority gap review | governance and safety veto; approval chain unresolved | keep changes in non-authorizing review posture | no autonomous promotion on unresolved approval path | [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | partial |
| evidence and provenance | evidence/provenance gap | artifact presence without sufficient causal reconstruction | provenance/replayability audit checks | unclear replayability blocks high-confidence progression claims | downgrade to partial/unclear and require evidence strengthening | maintain conservative stage until reconstruction improves | [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | partial |
| operator and audit surfaces | operator-visibility/audit-surface failure | denial states are not clearly visible to operator review | gate-status, promotion-state, and evidence-index review | ambiguous visibility blocks trustworthy transition interpretation | explicit no-go reporting with conservative status | keep prior state and require visibility fix before promotion | [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md), [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md), [EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) | partial |

## 5) Layer-by-Layer Notes

- Intake/data layer: failure detection is mostly interpretation-driven; no single canonical data-failure contract yet.
- Eligibility/directional layers: authority and semantics are visible, but singular authoritative ownership remains partial.
- Scope/risk/safety layers: separation is explicit; safety has the strongest fail-closed clarity.
- Promotion layer: visibility exists, but transition permission and authorization remain intentionally external.
- Learning/policy/provenance layers: rich documentation exists, but consolidated approval and causal replayability stay partial.

## 6) Ambiguity, Confusion, and Interpretation Risk Map

- fail-closed versus strategic no-trade: both can block progression, but fail-closed is a safety veto posture and not equivalent to strategic abstention.
- safety veto versus ordinary risk-cap denial: both block actions, but safety veto is higher-priority emergency boundary.
- rollback/safe retreat versus simple blocking: blocking can be static; rollback implies explicit retreat semantics and recovery posture.
- evidence gap versus runtime failure: missing reconstruction evidence is not automatically a runtime defect.
- operator-readable denial versus hidden failure state: denial that is not clearly surfaced increases review and audit drift.

## 7) Non-Authorizing Constraint

This specification authorizes nothing.

It only makes failure, fallback, and rollback semantics visible for review and audit.

Clarified mapping in this document is not equivalent to runtime materialization.

Live remains separately gated and separately authorized.

## 8) Evidence and Closure Criteria

Confirmed by this specification:

- one dedicated Master V2 failure taxonomy and safe-fallback surface is now materialized.
- failure classes across capital-path and promotion-path layers are explicitly visible.
- boundaries to authority, gate status, safety, and provenance surfaces are explicit.

Still open:

- one consolidated cross-layer failure-event ledger tied to authority outcomes.
- one compact canonical rollback-state contract across all promotion stages.
- stronger linkage from evidence gaps to explicit remediation-class categories.

Potential follow-up slice (separate topic):

- focused failure-event ledger and remediation mapping slice that stays docs-only and non-authorizing.

## 9) Cross-References

- Optional docs-only pointer metadata for externally retained bounded-pilot L5 incident / safe-stop evidence (no payloads in git): [MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md](MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md)
- [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md)
- [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md)
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)
- [AI_AUTONOMY_GO_NO_GO_OVERVIEW.md](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
- [WORKFLOW_OFFICER_FAILURE_TAXONOMY_V0.md](../concepts/WORKFLOW_OFFICER_FAILURE_TAXONOMY_V0.md)
- [EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md)
