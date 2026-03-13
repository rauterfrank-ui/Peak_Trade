# Bounded Real-Money Pilot Entry Contract

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Canonical operator-facing entry contract for the first strictly bounded real-money pilot
docs_token: DOCS_TOKEN_BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT

## 1. Goal

This document defines the single operator-facing contract for entering the first strictly bounded real-money pilot.

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
   - See `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
   - Required sequence:
     - Live Drills
     - Pilot Go/No-Go Eval
     - Execution Session Dry-Run
     - Optional bounded wrapper dry-run

2. **Go/No-Go Acceptable**
   - `scripts/ops/pilot_go_no_go_eval_v1.py`
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
   - See `docs/ops/specs/TREASURY_BALANCE_SEPARATION_SPEC.md`

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

**Entry boundary note:** See `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md` for where the flow ends today and how the first real-money step is invoked (operator-driven until a bounded-pilot entry path exists).

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

- `scripts/ops/run_bounded_pilot_session.py` — Pre-Entry-Checks gate (no live start)
- `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
- `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md`
- `docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md`
- `scripts/ops/pilot_go_no_go_eval_v1.py`
- `docs/ops/specs/TREASURY_BALANCE_SEPARATION_SPEC.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md`

## 7. Non-Goals

This document does not:

- grant execution authority
- relax gates
- define broad live rollout
- replace incident runbooks
- replace reconciliation procedures

## 8. Exit Condition For This Contract

This contract remains valid until a more advanced bounded-pilot automation layer exists.
Until then, this document is the canonical operator entry reference for the first strictly bounded real-money pilot.
