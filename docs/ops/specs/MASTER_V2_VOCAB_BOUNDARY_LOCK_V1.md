# MASTER V2 — Vocabulary Boundary Lock v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-19
owner: Peak_Trade
purpose: Canonical docs-only, mapping-only vocabulary and boundary lock for Master V2 semantic separation
docs_token: DOCS_TOKEN_MASTER_V2_VOCAB_BOUNDARY_LOCK_V1

## 1) Title / Status / Purpose

This specification materializes one dedicated Master V2 vocabulary/boundary lock artifact.

It is compact, canonical, mapping-only, and non-authorizing. It clarifies term boundaries across existing Master V2 surfaces and nearby repository terminology without introducing runtime semantics, permissions, or policy changes.

## 2) Scope and Non-Goals

In scope:

- canonical Master V2 term-boundary locking for high-confusion semantic pairs
- explicit non-equality and interpretation guardrails
- repo-anchored nearest-evidence mapping for vocabulary distinctions
- conservative clarity labeling (`repo-evidenced`, `documented`, `unverified`, `not-claimed`)

Out of scope:

- runtime rewiring or implementation changes
- live authorization, gate closure, enablement, or policy relaxation
- new control logic, new risk semantics, or new authority chains
- replacing or rewriting existing canonical Master V2 specs

## 3) Canonical Vocabulary Boundary Table

| canonical term | repo aliases / near-synonyms | confusion risk | preferred distinction | nearest repo evidence | current clarity |
|---|---|---|---|---|---|
| Universe Selection | market scan, screening utilities, ranking scripts, Top-N helpers | Universe definition is collapsed into generic scan tooling language | Universe Selection is the boundary-setting stage; generic scan/screen/ranking utilities are implementation-adjacent contributors, not the canonical universe-boundary term | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md) | repo-evidenced |
| Doubleplay directional evaluation | regime detection, regime switching, strategy switching | Doubleplay business-core semantics are merged with generic switching terms | Doubleplay directional evaluation is a distinct stage; regime detection/switching are adjacent but non-equivalent semantics | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | repo-evidenced |
| Bull/Bear specialist contribution | generic strategy selection, generic strategy router | Specialist contribution lanes are mistaken for final strategy or execution authority | Bull/Bear specialists are contribution lanes into arbitration; they are not equivalent to generic strategy selection authority | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | documented |
| Scope / Capital Envelope | risk limits, exposure caps, order-size caps, leverage caps | Upstream scope semantics are collapsed into downstream limit enforcement terms | Scope/Capital Envelope is upstream capital-path scoping; downstream risk caps enforce hard limits on candidate actions and are not equivalent | [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | repo-evidenced |
| strategic switch-gate | safety gate, kill-switch, fail-closed veto | strategic switching gate is misread as safety veto or final trade authority | strategic switch-gate governs strategy switching boundaries; safety/kill-switch is a higher-priority fail-closed veto layer with different authority semantics | [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | repo-evidenced |
| advisory AI / AI orchestration | execution decider, final trading authority, runtime authorizer | advisory/model-orchestration outputs are interpreted as authoritative execution decisions | advisory AI provides analysis/orchestration support only; authoritative execution decisions and live permission remain external | [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md), [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md) | repo-evidenced |
| gate status visibility | transition permission, promotion command, live authorization | status/read-model/report visibility is treated as permission to transition | Gate status visibility is interpretation/reporting state; transition permission and live authorization require external authority and remain separate | [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md), [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md), [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md) | repo-evidenced |
| replayability evidence | true causal reconstruction, end-to-end deterministic replay | evidence pointer presence is over-read as full causal replay completeness | replayability evidence improves provenance visibility; true causal reconstruction remains a stricter, often partial, cross-surface capability | [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md), [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md), [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md) | repo-evidenced |

## 4) Forbidden Equalities / Do-Not-Collapse List

The following equalities are explicitly forbidden for Master V2 interpretation:

- `Universe Selection != generic scan or screening utilities`
- `Doubleplay directional evaluation != generic regime switching`
- `Bull/Bear specialist contribution != generic strategy selection authority`
- `Scope / Capital Envelope != downstream Risk or Exposure Caps`
- `strategic switch-gate != safety or kill-switch veto`
- `advisory AI != authoritative execution decision`
- `gate status visibility != transition permission`
- `replayability evidence != true causal reconstruction`

Additional guardrails:

- `mapped`, `partial`, or `verified` interpretation wording is never equal to live authorization
- evidence-pointer presence is never equal to closure proof
- authority naming in docs is never equal to granted authority

## 5) Interpretation Locks for Master-V2

Interpretation locks that remain binding across Master V2 specs:

- use canonical term names from this file and linked canonical artifacts; avoid parallel terminology where a canonical term already exists
- keep advisory vs authoritative vs veto semantics explicitly separated
- keep strategic switching semantics separated from safety fail-closed semantics
- keep scope/capital semantics separated from downstream hard-cap enforcement semantics
- treat gate/report/read-model outputs as visibility surfaces only, not permission surfaces
- phrase provenance/replay statements conservatively; do not upgrade partial evidence to full causal reconstruction
- if evidence is incomplete, claims must be downgraded to `documented`, `unverified`, or `not-claimed`
- preserve the non-authorizing posture: this artifact cannot close gates, grant live permissions, or alter runtime behavior

## 6) Nearest Existing Repo Artifacts / Cross-References

Primary Master V2 anchors:

- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md](MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md)
- [MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md](MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [MASTER_V2_PROMOTION_STATE_MACHINE_V1.md](MASTER_V2_PROMOTION_STATE_MACHINE_V1.md)
- [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md)
- [MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md](MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
- [MASTER_V2_DATAFLOW_MAP_V1.md](MASTER_V2_DATAFLOW_MAP_V1.md)
- [MASTER_V2_GATE_FILL_VOCABULARY_BOUNDARY_LOCK_V1.md](MASTER_V2_GATE_FILL_VOCABULARY_BOUNDARY_LOCK_V1.md)
- [CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md](CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md)

## 7) Operator Notes

- This document is docs-only, mapping-only, and non-authorizing.
- Use it as a review boundary lock when assessing Master V2 terminology in specs, runbooks, and PR text.
- If wording implies permission, closure, or runtime behavior, treat that as boundary drift and require correction.
- Prefer canonical terms from this file; do not normalize by introducing additional near-synonyms.
- When evidence anchors are weak, preserve conservative clarity labels and avoid semantic inflation.
