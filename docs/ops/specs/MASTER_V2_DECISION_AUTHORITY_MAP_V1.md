# MASTER V2 — Decision Authority Map v1 (Canonical, Read-Only)

status: ACTIVE
last_updated: 2026-04-21
owner: Peak_Trade
purpose: Canonical docs-only, non-authorizing decision-authority mapping for Master V2 First Live Enablement
docs_token: DOCS_TOKEN_MASTER_V2_DECISION_AUTHORITY_MAP_V1

## 1) Executive Summary

This document materializes a canonical, mapping-only decision-authority view for the Master V2 First Live Enablement path.

It is explicitly non-authorizing: it improves legibility and auditability of authority boundaries, but it does not grant live permissions, close gates, or redefine runtime behavior.

## 2) Scope and Non-Goals

In scope:

- decision-authority mapping for the Master V2 core path from market eligibility through staged execution enablement
- explicit separation of advisory, authoritative, veto, and fail-closed roles
- explicit marking of unclear or missing authority handoffs

Out of scope:

- runtime rewiring or implementation changes
- live authorization decisions
- reuse&#47;rewire inventory updates
- gate closure or gate-status inflation
- creation of new authority domains not backed by repo evidence

## 3) Canonical Decision Stages

The canonical stages for this map are:

1. Universe Selection and Market Eligibility
2. Doubleplay directional evaluation
3. Bull specialist contribution
4. Bear specialist contribution
5. LONG or SHORT or FLAT aggregation and arbitration
6. Scope and Capital Envelope determination
7. downstream Risk and Exposure Cap enforcement
8. Safety and Kill-Switch veto layer
9. staged Execution Enablement and promotion blocking
10. learning, model, and policy change approval boundary

## 4) Decision Authority Table

| stage | primary input | advisory producers | aggregator / transformer | authoritative decider | veto / fail-closed layer | output | current repo evidence | confidence | ambiguity / gap |
|---|---|---|---|---|---|---|---|---|---|
| Universe Selection and Market Eligibility | market scan data, top-N ranking signals | scan and ranking components | market eligibility synthesis before directional path | partial: eligibility authority appears distributed across selection and gating layers | risk and governance gates can block eligibility from becoming deployable | candidate market set | `scripts/scan_markets.py`; `run_market_scan.py`; `src/experiments/topn_promotion.py`; `docs/ops/specs/MASTER_V2_DATAFLOW_MAP_V1.md` | partial | single canonical authoritative decider is not fully consolidated |
| Doubleplay directional evaluation | eligible market set plus directional context | directional signal producers and strategy inputs | Doubleplay core evaluation path | partial: directional authority is intended in Doubleplay but not fully pinned to one canonical runtime authority artifact | downstream risk and safety can veto execution regardless of direction output | directional recommendation context | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `docs/roadmap/PeakTrade_LevelUp_Roadmap_Evidence.md`; `docs/ops/specs/MASTER_V2_DATAFLOW_MAP_V1.md` | partial | boundary with regime switching remains a high confusion risk |
| Bull specialist contribution | bull-side strategy evidence and directional features | bull specialist analytics | contribution shaping for directional arbitration | advisory role evidenced; final authority not assigned to this lane | strategic and safety veto layers can block downstream action | bull-side contribution signal | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` | partial | runtime authoritative ownership for lane output is unclear |
| Bear specialist contribution | bear-side strategy evidence and directional features | bear specialist analytics | contribution shaping for directional arbitration | advisory role evidenced; final authority not assigned to this lane | strategic and safety veto layers can block downstream action | bear-side contribution signal | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `PeakTrade_LevelUp_Roadmap_Evidence_20260211_doubleplay_leverage50.md` | partial | runtime authoritative ownership for lane output is unclear |
| LONG or SHORT or FLAT aggregation and arbitration | bull and bear contributions plus switching constraints | lane specialists and switch inputs | arbitration across directional candidates | partial: arbitration authority appears intended in Doubleplay and switch-gate area | safety and governance remain higher-priority veto domains for live path | directional state proposal | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `docs/ops/specs/MASTER_V2_DATAFLOW_MAP_V1.md` | partial | explicit canonical arbitration authority node is missing |
| Scope and Capital Envelope determination | equity context, policy envelopes, deployment constraints | portfolio and risk advisory inputs | envelope calculation and allocation gating | unclear: Scope and Capital Envelope authority is conceptually distinct but not consolidated | risk caps and safety layers can veto downstream deployment | deployable scope proposal | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `docs/ops/specs/MASTER_V2_DATAFLOW_MAP_V1.md` | unclear | high ambiguity versus risk-cap semantics |
| downstream Risk and Exposure Cap enforcement | deployable scope proposal and position intents | risk metrics producers | hard-limit checks and cap enforcement transforms | partial: risk enforcement authority is evidenced as limit-enforcing, not final business decision authority | safety and governance can still veto execution path | risk-constrained execution eligibility | `src/live/risk_limits.py`; `src/live/safety.py`; `src/live/live_gates.py`; `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md` | partial | exact handoff from business decider to cap enforcer is only partially mapped |
| Safety and Kill-Switch veto layer | execution-intent path and safety state | monitoring and safety signals | fail-closed safety gate evaluation | authoritative for veto intent (block capability), not business strategy authority | primary fail-closed veto | blocked or allowed continuation signal | `src/live/safety.py`; `src/live/live_gates.py`; `docs/risk/KILL_SWITCH_RUNBOOK.md`; `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md` | repo-evidenced | ordering between strategic switch and safety veto is frequently misread by reviewers |
| staged Execution Enablement and promotion blocking | readiness evidence, gate states, governance constraints | operator and review artifacts | promotion-state interpretation and gating | partial: readiness interpretation is canonical, but live authorization remains separate and external | governance and safety veto precedence | promotion eligibility status, not live authorization | `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`; `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md`; `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md` | partial | explicit authority actor for final live authorization remains outside this map |
| learning, model, and policy change approval boundary | model and policy change proposals plus evidence packs | AI and model orchestration components | review and approval preparation | missing: consolidated authoritative approver map is not yet canonicalized in one artifact | governance and safety veto constraints still apply | approval-boundary posture and unresolved authority gaps | `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`; `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`; `docs/ops/specs/MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md` | missing | authoritative approval chain is not yet canonically unified |

## 5) Advisory vs Authoritative vs Veto Rules

Canonical role definitions for this map:

- advisory: produces recommendations, diagnostics, or candidate signals; cannot by itself authorize capital-path execution
- authoritative: designated decision role for a stage output; must be explicitly evidenced to be claimed
- veto: can block downstream progression regardless of advisory or authoritative recommendations
- fail-closed: veto behavior that defaults to blocked when conditions are unclear, unsafe, or unresolved

Boundary lock:

- Safety and Kill-Switch veto is a safety boundary and has fail-closed semantics
- strategic switch-gate behavior is not equivalent to safety veto and is not itself final trade authority

## 6) Stage-by-Stage Mapping Notes

- Universe Selection and Market Eligibility: advisory-heavy evidence exists; final singular authority remains partial.
- Doubleplay directional evaluation: intended business core is clear; explicit canonical authority node remains partial.
- Bull and Bear specialist contributions: both are mapped as contributors, not final authorizers.
- LONG or SHORT or FLAT aggregation and arbitration: aggregation exists conceptually; explicit authoritative arbitration owner remains partial.
- Scope and Capital Envelope determination: distinction from risk caps is canonical; ownership remains unclear in one consolidated authority artifact.
- downstream Risk and Exposure Cap enforcement: enforcement role is strongly evidenced; not equivalent to business decision authority.
- Safety and Kill-Switch veto layer: strongest veto evidence; fail-closed semantics are explicit.
- staged Execution Enablement and promotion blocking: readiness visibility is mapped; final live authorization authority remains external.
- learning, model, and policy change approval boundary: advisory/orchestration signals exist; canonical authoritative approval chain is missing.

## 7) Ambiguity / Confusion / Interpretation Risk Map

- Doubleplay vs regime switching: frequent semantic collision; maintain strict non-equality.
- Scope and Capital Envelope vs risk caps: maintain separate authority semantics; do not collapse.
- strategic switch-gate vs safety gates: strategic control is not safety fail-closed veto.
- advisory AI and models vs authoritative execution decisions: orchestration is not execution authority.
- promotion authority vs runtime trading authority: readiness or promotion visibility is not live authorization.

## 8) Non-Authorizing Constraint

This spec authorizes nothing.

It only makes authority structure visible for review and audit. Live remains separately gated and separately authorized by sources outside this map.

## 9) Evidence and Closure Criteria

Confirmed by this spec:

- authority-related signals and boundaries are present across canonical Master V2 surfaces
- safety veto and fail-closed semantics are the most explicit authority boundary currently evidenced

Still open:

- canonical consolidation of authoritative decision ownership for several stages
- canonical, single-surface authority chain for learning/model/policy change approval

Next closure candidate (separate slice, not part of this document):

- a focused authority-gap closure slice that only resolves explicitly marked `partial`, `unclear`, and `missing` authority nodes without mixing runtime implementation.

## 10) Cross-References

- `docs/ops/specs/MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md` (G10 handoff legibility note: §4.6)
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md`
- `docs/ops/specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`
- `docs/ops/specs/MASTER_V2_DATAFLOW_MAP_V1.md`
- `docs/ops/specs/MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md`
- `docs/ops/specs/MASTER_V2_GATE_FILL_VOCABULARY_BOUNDARY_LOCK_V1.md`
- `docs/ops/specs/CANONICAL_VOCAB_AUTHORITY_PROVENANCE_V0.md`
- `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`
