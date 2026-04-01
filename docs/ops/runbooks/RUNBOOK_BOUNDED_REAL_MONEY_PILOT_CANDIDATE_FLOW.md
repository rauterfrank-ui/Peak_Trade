# RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW

status: DRAFT
last_updated: 2026-04-01
owner: Peak_Trade
purpose: Canonical first-session sequence for the first strictly bounded real-money pilot candidate flow
docs_token: DOCS_TOKEN_RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW

## 1. Goal

This runbook defines the canonical operator sequence for the **first strictly bounded real-money pilot candidate session**.

It does **not** authorize broad live trading.
It defines one tightly bounded, explicitly operator-supervised first-session flow.

## 2. Preconditions

All of the following must already be true before this runbook is used:

- Dry validation completed
  - `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
- Entry contract accepted
  - `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- Pilot go/no-go verdict acceptable
  - `scripts/ops/pilot_go_no_go_eval_v1.py`
  - expected verdict: `GO_FOR_NEXT_PHASE_ONLY`
- Ops Cockpit reviewed
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

## 3. Candidate Session Posture

The first bounded real-money pilot candidate session must remain:

- operator-supervised
- strictly bounded by configured caps
- ambiguity-intolerant
- kill-switch aware
- treasury-separated
- evidence-first

Rule: **ambiguity => `NO_TRADE` / safe stop**

## 4. Step Sequence

### Step 1 — Confirm Entry Preconditions
Confirm that:
- dry validation is complete
- go/no-go verdict is `GO_FOR_NEXT_PHASE_ONLY`
- `human_supervision_state.status == operator_supervised`
- no unresolved stale state exists
- no unresolved session-end mismatch exists
- no unresolved transfer ambiguity exists
- kill switch is not active
- bounded caps are present
- treasury separation is explicit

### Step 2 — Confirm First-Session Bounds
Confirm the first candidate session is explicitly bounded:
- smallest acceptable pilot scope only
- no broad rollout interpretation
- no informal cap widening
- no relaxed operator posture
- no hidden dependency on missing evidence

### Step 3 — Start the First Candidate Session
Run the first bounded real-money candidate session only under explicit operator observation.

**Concrete entry (current repo):** follow **`docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`** — typically  
`python3 scripts/ops/run_bounded_pilot_session.py` after all gates GREEN (or `python3 scripts/run_execution_session.py --mode bounded_pilot` only if the same preconditions are already verified).

During start:
- keep the Ops Cockpit visible
- keep incident posture visible
- keep kill-switch posture visible
- keep bounded caps visible

### Step 4 — Observe During Session
During the candidate session, continuously watch:
- `policy_state`
- `operator_state`
- `incident_state`
- `dependencies_state`
- `evidence_state`
- `exposure_state`
- `stale_state`

Any operator uncertainty is treated as `NO_TRADE`.

### Step 5 — Abort Immediately If Any Abort Criterion Appears
Abort immediately if any of the following occurs:
- kill switch becomes active
- policy posture becomes blocked
- dependency posture degrades beyond acceptable bounded pilot tolerance
- stale state becomes unresolved
- unexpected exposure appears
- transfer ambiguity appears
- restart mid-session occurs without coherent restart handling
- session-end mismatch becomes evident
- operator can no longer clearly determine allowed posture

### Step 6 — Close Out and Reconcile
After the candidate session:
- perform the required closeout and reconciliation steps
- review any mismatch or ambiguity before any next session is considered
- do not interpret one successful candidate session as broad live readiness

## 5. Required Evidence

The operator should preserve evidence for:
- pilot go/no-go result
- relevant Ops Cockpit state at session start
- session-level notes / decision rationale
- incident/mismatch notes, if any
- session closeout outcome
- reconciliation outcome

## 6. Related Runbooks / Specs

- `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md` (**bounded pilot live entry — Ist-Stand**)
- `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md` (dry vs first real-money step)
- `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`
- `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md`
- `docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md`

## 7. Non-Goals

This runbook does not:
- authorize broad live trading
- replace go/no-go evaluation
- replace dry validation
- replace incident runbooks
- remove operator supervision
