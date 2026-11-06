# Bounded Real-Money Pilot Entry Contract

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Draft operator-facing entry contract anchor for the first strictly bounded real-money pilot
docs_token: DOCS_TOKEN_BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT

## 1. Goal

This document defines the draft operator-facing contract anchor for entering the first strictly bounded real-money pilot.

Draft-maturity note: This contract is a repo-local **DRAFT** anchor for candidate-scoped review. It does not by itself approve bounded real-money execution, bypass gates, or change runtime, trading, evidence, approval, or live-entry semantics.

It does **not** authorize broad live trading.
It defines the minimal bounded entry posture under explicit operator supervision.

## 2. Entry Posture

The bounded real-money pilot is permitted only under all of the following conditions:

- operator-supervised posture is explicit
- dry validation has completed
- pilot go/no-go result is acceptable
- bounded caps are explicit
- treasury separation is explicit
- ambiguity posture remains `NO_TRADE`
- incident / abort posture is explicit before first real-money step

## 3. Pre-Entry Prerequisites

The operator must confirm all of the following before entry:

1. **Dry Validation Completed**
   - See `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
   - Required sequence:
     - Live Drills
     - Pilot Go/No-Go Eval
     - Execution Session Dry-Run
     - Optional bounded wrapper dry-run

2. **Go/No-Go Acceptable**
   - `scripts&#47;ops&#47;pilot_go_no_go_eval_v1.py`
   - Acceptable result for entry:
     - `GO_FOR_NEXT_PHASE_ONLY`
   - Non-acceptable results:
     - `CONDITIONAL`
     - `NO_GO`

3. **Operator Supervision Explicit**
   - Ops Cockpit `human_supervision_state.status == operator_supervised`

4. **Policy / Operator / Incident Surfaces Acceptable**
   - `policy_state`
   - `operator_state`
   - `incident_state`
   - `dependencies_state`
   - `evidence_state`
   - `stale_state`
   - `session_end_mismatch_state`

5. **Bounded Caps Explicit**
   - `exposure_state.caps_configured` must be present
   - Risk decisions must remain bounded by configured caps

6. **Treasury Separation Explicit**
   - `guard_state.treasury_separation == enforced`
   - See `docs&#47;ops&#47;specs&#47;TREASURY_BALANCE_SEPARATION_SPEC.md`

Pointer note: For the external-metadata-only pointer vocabulary around L3 entry prerequisites, see [MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md](MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md). This note is non-authorizing and does not change gate, approval, runtime, trading, or live-entry semantics.

## 4. First Bounded Real-Money Step

The first bounded real-money step is defined as:

- one strictly operator-supervised pilot session
- bounded by configured caps
- with kill switch posture explicit
- with ambiguity posture remaining `NO_TRADE`
- without broad live enablement claims

This step is **not** equivalent to general live readiness.

## 5. Abort / Rollback / NO_TRADE Criteria

Entry must not occur, or must be aborted immediately, if any of the following are true:

- pilot go/no-go verdict is not `GO_FOR_NEXT_PHASE_ONLY`
- kill switch is active
- policy posture is blocked
- stale state is unresolved
- session-end mismatch is unresolved
- transfer ambiguity is unresolved
- evidence or dependency posture is degraded beyond acceptable pilot tolerance
- operator cannot clearly determine the current bounded posture
- any ambiguity exists about whether trading is allowed

Rule: **ambiguity => `NO_TRADE` / safe stop**

## 6. Where To Look

**Entry boundary note:** See `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md` for the boundary between dry validation and the first bounded real-money step; **operative invocation:** `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`.

**Gap note:** See `docs/ops/specs/BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE.md` for historical gap analysis; **operative procedure:** `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`.

Primary operator evidence:

- Ops Cockpit payload / UI:
  - `policy_state`
  - `operator_state`
  - `run_state`
  - `incident_state`
  - `exposure_state`
  - `evidence_state`
  - `dependencies_state`
  - `stale_state`
  - `session_end_mismatch_state`
  - `human_supervision_state`

Primary docs / scripts:

- `scripts&#47;ops&#47;check_bounded_pilot_readiness.py` — Canonical read-only preflight: bundles live-stage `check_live_readiness` + `pilot_go_no_go_eval_v1`; does not start a session
- `scripts&#47;ops&#47;run_bounded_pilot_session.py` — Pre-Entry-Checks gate; with default args invokes bounded pilot session (see `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`); use `--no-invoke` for gates only
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
- `docs&#47;ops&#47;specs&#47;PILOT_GO_NO_GO_CHECKLIST.md`
- `docs&#47;ops&#47;specs&#47;PILOT_GO_NO_GO_OPERATIONAL_SLICE.md`
- `scripts&#47;ops&#47;pilot_go_no_go_eval_v1.py`
- `docs&#47;ops&#47;specs&#47;TREASURY_BALANCE_SEPARATION_SPEC.md`
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md`
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md`
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md`

## 7. Non-Goals

This document does not:

- grant execution authority
- relax gates
- define broad live rollout
- replace incident runbooks
- replace reconciliation procedures

## 8. Exit Condition For This Contract

This contract remains the operator-facing **DRAFT** reference anchor for the **first strictly bounded real-money pilot**.
Operational steps (dry validation → gates → session handoff) are detailed in  
`docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`; future automation layers may extend but do not replace Entry Contract obligations or abort criteria.
