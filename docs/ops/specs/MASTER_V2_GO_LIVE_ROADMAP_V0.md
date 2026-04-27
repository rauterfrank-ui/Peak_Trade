---
docs_token: DOCS_TOKEN_MASTER_V2_GO_LIVE_ROADMAP_V0
status: draft
scope: docs-only, non-authorizing Master V2 Go-Live roadmap
last_updated: 2026-04-28
---

# Master V2 Go-Live Roadmap V0

## 1. Executive Summary

This document defines a staged, non-authorizing roadmap from the current Master V2 repository posture toward a future Go-Live process.

It does not authorize live trading. It does not enable live execution. It does not change configs, workflows, registry JSONs, `out&#47;ops` artifacts, strategy logic, risk logic, kill switch behavior, execution gates, paper/test data, or Master V2 / Double Play logic.

The roadmap sequence is:

1. Research / Backtest / Robustness
2. Shadow / Paper Evidence
3. Testnet Evidence
4. Session Review Pack / Source-Bound Review
5. Pre-Live Package / External Decision
6. Bounded Real-Money Pilot
7. Post-Pilot Review / Promotion

Every stage is evidence-gated and fail-closed. Advancement requires explicit operator/external decisions where applicable.

## 2. Purpose and Non-Goals

Purpose:

- give one canonical roadmap for moving toward Go-Live;
- connect existing readiness, evidence, SRP, bounded-pilot, and authority surfaces;
- define stage entry/exit criteria;
- define hard stop / kill criteria;
- keep Master V2 / Double Play protected;
- make operator decision points explicit.

Non-goals:

- No live authorization.
- No live config enablement.
- No bounded-pilot entry approval.
- No strategy readiness claim.
- No autonomy readiness claim.
- No external signoff claim.
- No changes to execution, risk, kill switch, or capital logic.
- No mutation of historical registry or artifact data.
- No automatic promotion across stages.

## 3. Current Posture

Current repo posture is review-oriented and non-authorizing.

Important anchors:

- [First Live Readiness Ladder](./MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md)
- [First Live Readiness Read Model](./MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md)
- [First Live Gate Status Index](./MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md)
- [First Live Gate Status Report Surface](./MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md)
- [Decision Authority Map](./MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [Promotion State Machine](./MASTER_V2_PROMOTION_STATE_MACHINE_V1.md)
- [Provenance / Replayability](./MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md)
- [Paper / Testnet Readiness Gap Map](./MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md)
- [Operator / Audit Flat Path Index](./MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md)

Session Review Pack anchors:

- [Session Review Pack Contract V0](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md)
- [Source-Bound SRP Report Implementation Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_IMPLEMENTATION_PLAN_V0.md)
- [Source-Bound SRP Report CLI Integration Test Plan](./MASTER_V2_SESSION_REVIEW_PACK_SOURCE_BOUND_REPORT_CLI_INTEGRATION_TEST_PLAN_V0.md)

Bounded-pilot anchors:

- [Started Bounded-Pilot Session Review Runbook](../runbooks/RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md)
- [Bounded Pilot Live Entry Runbook](../runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md)

Relevant focused tests include:

- `tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py`
- `tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py`
- `tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py`
- `tests/ops/test_session_review_pack_report_contracts_v0.py`

## 4. Stage 1 — Research / Backtest / Robustness

### Entry Criteria

- Strategy/research changes remain offline and non-authorizing.
- Backtest evidence is reproducible.
- Robustness expectations are documented.
- Fees, slippage, stops, drawdown, and edge cases are considered.

### Exit Criteria

- Backtest / robustness review surfaces are available.
- No live-readiness claim is inferred from backtest results.
- Any strategy candidate is explicitly marked as research/paper/testnet candidate only.

### Hard Stops

- Missing reproducibility inputs.
- Missing fees/slippage assumptions.
- Backtest-only claim framed as live-ready.
- Strategy logic bypasses Master V2 / Double Play boundaries.

## 5. Stage 2 — Shadow / Paper Evidence

### Entry Criteria

- Research candidate has sufficient offline evidence.
- Paper/shadow environment is isolated from live execution.
- Evidence artifacts are generated without live authority.

### Exit Criteria

- Paper/shadow session evidence is present and reviewable.
- Report surfaces can identify sessions, evidence pointers, and gaps.
- Operator review can distinguish completed, failed, aborted, and started sessions.
- No PnL or readiness claim is inferred from presence alone.

### Hard Stops

- Paper artifacts are missing or ambiguous.
- Session status is non-terminal without review posture.
- Evidence paths contain unreviewed local/operator metadata.
- Paper/shadow behavior is conflated with live authority.

## 6. Stage 3 — Testnet Evidence

### Entry Criteria

- Paper/shadow evidence is reviewable.
- Risk / KillSwitch / Execution gate boundaries are still intact.
- Testnet scope is explicit and non-live.

### Exit Criteria

- Testnet sessions are reviewable.
- Testnet behavior is distinguishable from paper/shadow and live.
- Failures, rejects, and missing event pointers remain visible.
- No automatic promotion from testnet to live exists.

### Hard Stops

- Testnet evidence is incomplete.
- Testnet uses unreviewed production/live credentials.
- Missing event pointers are silently repaired.
- Testnet outcome is treated as live authorization.

## 7. Stage 4 — Session Review Pack / Source-Bound Review

### Entry Criteria

- Static SRP V0 remains stable.
- Source-bound SRP planning and synthetic tests exist.
- Explicit session selection is required for future source-bound review.
- Registry / Evidence linkage semantics are documented.

### Exit Criteria

- Selected session can be reviewed with a source-bound review pack when implemented.
- Missing and present event pointers are preserved explicitly.
- Static SRP V0 remains template-like.
- Authority flags remain false/non-authorizing.

### Hard Stops

- Source selection is implicit or automatic.
- Static SRP V0 is silently changed.
- Registry JSONs or `out&#47;ops` artifacts are mutated.
- Source-bound review implies closeout approval, gate passage, or live authorization.

## 8. Stage 5 — Pre-Live Package / External Decision

### Entry Criteria

- Readiness ladder and gate status surfaces are updated/reviewed.
- SRP/source-bound review is available or explicitly deferred.
- Evidence package is coherent and traceable.
- Known blockers and gaps are visible.

### Exit Criteria

- Operator/external decision authority is explicit.
- Go / No-Go posture is recorded outside implementation code.
- Preconditions for bounded pilot are satisfied or blocked.
- No in-repo document claims final external authority unless actually granted by the proper external process.

### Hard Stops

- Missing external authority.
- Missing risk/capital/kill switch confirmation.
- Missing evidence package.
- Ambiguous owner for Go/No-Go decision.
- Any claim that repo docs alone approve live trading.

## 9. Stage 6 — Bounded Real-Money Pilot

### Entry Criteria

- Explicit bounded-pilot authority exists.
- Live gates remain fail-closed unless deliberately armed.
- Scope, capital slot, kill switch, and stop criteria are explicit.
- Operator preflight and closeout process are known.
- No historical started/open session ambiguity is ignored.

### Exit Criteria

- Pilot session is closed or reviewed according to bounded-pilot process.
- Execution events, registry records, evidence, and closeout posture are reviewable.
- Incident/abort conditions are documented.
- No promotion is automatic.

### Hard Stops

- KillSwitch uncertainty.
- Capital/scope uncertainty.
- Missing preflight packet.
- Missing closeout process.
- Unexpected live exposure.
- Evidence artifact ambiguity.
- Any divergence from Master V2 / Double Play authority boundaries.

## 10. Stage 7 — Post-Pilot Review / Promotion

### Entry Criteria

- Bounded pilot produced reviewable evidence.
- Session Review Pack / source-bound review can inspect selected session(s).
- Closeout and lifecycle reports are available.
- Operator notes are complete.

### Exit Criteria

- Promotion decision is explicit.
- Risk/Capital/Scope review is complete.
- Evidence gaps are either closed or accepted by the proper authority.
- Next stage is bounded and documented.

### Hard Stops

- PnL-only promotion.
- Unreviewed execution anomalies.
- Missing event streams.
- Missing closeout.
- Missing authority decision.
- Any automatic expansion of live scope.

## 11. Cross-Stage Evidence Requirements

Every stage should preserve:

| Evidence class | Required property |
|---|---|
| Registry/session record | Traceable, reviewable, non-mutated. |
| Execution/event pointer | Present/missing state explicit. |
| Backtest/paper/testnet artifact | Reproducible and attributable. |
| Readiness/gate report | Non-authorizing unless external authority is explicit. |
| Operator note | Clear owner and decision context. |
| Risk/KillSwitch evidence | Fail-closed posture visible. |
| Source-bound SRP | Explicit selected source only. |

## 12. Operator Decision Points

Operator decisions are required before:

1. moving from research/backtest to paper/shadow;
2. moving from paper/shadow to testnet;
3. treating testnet evidence as pre-live package input;
4. selecting a session for source-bound SRP review;
5. submitting pre-live evidence for external decision;
6. entering bounded real-money pilot;
7. promoting or expanding after pilot.

Each decision must remain separable from code implementation.

## 13. Authority Boundaries

| Surface | May do | Must not do |
|---|---|---|
| Roadmap | Sequence the path to Go-Live. | Authorize live trading. |
| Readiness Ladder | Describe readiness posture. | Grant external authority. |
| SRP | Provide review packet structure. | Approve closeout or live. |
| Source-bound SRP | Review explicitly selected session. | Auto-select or promote. |
| Bounded-pilot runbook | Guide operator process. | Bypass gates. |
| Evidence index | Navigate evidence. | Prove strategy readiness alone. |
| Tests | Pin expected behavior. | Authorize runtime behavior. |
| Operator | Decide within documented authority. | Override hard risk stops. |

## 14. Kill Criteria / Hard Stops

Stop the Go-Live progression immediately if any of these occur:

- live gates are unclear;
- kill switch behavior is uncertain;
- capital/scope limits are ambiguous;
- Master V2 / Double Play boundaries are bypassed;
- source selection is implicit;
- registry or event artifacts are mutated to make evidence look cleaner;
- missing evidence is treated as passed;
- paper/testnet output is treated as live approval;
- external authority is missing;
- operator cannot explain current state from repo surfaces.

## 15. What This Roadmap Does Not Authorize

This roadmap does not authorize:

- enabling live trading;
- arming live mode;
- placing orders;
- bypassing dry-run gates;
- increasing capital;
- selecting live strategy candidates;
- accepting missing evidence;
- closing started sessions;
- modifying historical artifacts;
- overriding KillSwitch / Risk / Execution gates;
- claiming first-live readiness;
- claiming external signoff.

## 16. Suggested Follow-Up Documents

If continued, use this order:

1. `MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md`
2. `RUNBOOK_MASTER_V2_FIRST_LIVE_PILOT_SEQUENCE_V0.md`
3. `MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md`

These follow-ups should remain docs-only unless a separate scoped implementation mandate exists.

## 17. Validation Notes

Validate this roadmap with:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
uv run pytest tests/ops/test_session_review_pack_source_bound_cli_shape_v0.py tests/ops/test_session_review_pack_source_bound_temp_resolver_v0.py tests/ops/test_session_review_pack_source_bound_payload_builder_v0.py tests/ops/test_session_review_pack_report_contracts_v0.py -q
```

Optional: extend validation with any additional SRP and bounded-pilot characterization tests in `tests/ops/` as the repo evolves.
