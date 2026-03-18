# NEXT BOUNDED TRIAL PREFLIGHT CHECKLIST

## Status
- Project: Peak_Trade
- Topic: next_bounded_trial_preflight_checklist
- Scope: read-only preflight before the next bounded trial or acceptance-oriented run
- Baseline expectation: `main` clean and synchronized
- Non-goal: no runtime mutation is performed by this checklist itself

## Purpose
This checklist defines the minimum read-only preflight needed before starting the next bounded-pilot run after the Trial-5 execution-events fix and post-fix closeout.

It is intended to preserve paper-test stability, ensure a quiet runtime surface, and make the intended run goal explicit before any operator starts a new bounded trial or acceptance-oriented step.

## Preconditions
- repository baseline is clean
- no unintended runtime processes are active
- supervisor remains stopped unless explicitly and intentionally started
- operator is prepared to review bounded-pilot prerequisites before execution

## Verified Starting Point
- Trial-5 execution-events fix is merged on `main`
- Trial-5 post-fix closeout is documented
- verified evidence exists for rejected-order execution-event writing

Reference evidence:
- `docs&#47;ops&#47;evidence&#47;TRIAL5_EXEC_EVENTS_POST_FIX_VERIFICATION_CLOSEOUT.md`

Verified session evidence:
- `out&#47;ops&#47;execution_events&#47;sessions&#47;session_20260318_164528_bounded_pilot_9c239f&#47;execution_events.jsonl`

## Preflight Checklist

### 1. Repository Baseline
Confirm:
- branch is `main`
- `main` is synchronized with `origin&#47;main`
- working tree is clean

Expected outcome:
- no uncommitted changes
- no untracked operational files that could confuse runtime interpretation

### 2. Runtime Quiet Check
Confirm:
- no bounded-pilot process is already running
- no leftover execution session is still active
- no unintended paper/shadow/testnet/live-track process is active

Expected outcome:
- no active `run_bounded_pilot_session`
- no active `run_execution_session`
- no unintended supervisor activity

### 3. Supervisor State
Confirm:
- online readiness supervisor is stopped unless explicitly required

Expected outcome:
- supervisor remains stopped for the cleanest bounded-trial preflight surface
- no background readiness loop is writing unrelated artifacts during the run

### 4. Execution-Event Evidence Mode
Confirm:
- execution-event evidence is enabled when the upcoming run expects execution-event capture

Expected outcome:
- `PT_EXEC_EVENTS_ENABLED=true` is intentionally set for runs where execution-event evidence is required

Clarification:
- if the run is only conceptual/read-only, do not set runtime flags
- if the run is an actual bounded-pilot execution run, explicitly confirm the intended evidence mode before launch

### 5. Run Goal Declaration
The operator must explicitly classify the next run as one of the following:

#### A. Rejected-Order Evidence Run
Use when the purpose is:
- confirming the bounded-pilot flow still produces execution-event evidence
- confirming rejected order attempts are captured
- not expecting exchange acceptance

Expected characteristics:
- bounded-pilot path exercised
- `order_submit` and `order_reject` evidence expected if an order attempt occurs
- missing or intentionally absent live credentials may still be acceptable depending on the operator goal

#### B. Acceptance-Oriented Run
Use when the purpose is:
- verifying actual exchange acceptance behavior
- validating that a real, acceptable order reaches exchange acceptance under bounded conditions

Additional prerequisites:
- valid Kraken credentials available in the intended execution environment
- explicit operator approval for an acceptance-oriented run
- bounded scope and evidence capture confirmed
- intention to test a genuinely acceptable order is documented before start

### 6. Entry Contract Confirmation
Confirm the bounded real-money pilot entry-contract prerequisites before any run:

Reference:
- `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`

Minimum confirmations:
- Dry Validation confirmed
- Go/No-Go status confirmed
- human supervision state confirmed
- evidence state reviewed
- exposure caps configured
- treasury separation enforced
- kill-switch state reviewed

### 7. Go/No-Go Confirmation
Confirm:
- Go/No-Go remains valid for the intended next phase
- no new blocker has emerged since the last verified closeout

Reference intent:
- bounded-pilot run should not proceed on stale or assumed Go/No-Go state

### 8. Ops Cockpit Review
Confirm via operator review:
- evidence state reviewed
- dependencies state reviewed
- telemetry state reviewed
- no obvious degraded operational state is visible before the next run

### 9. Invocation Path Awareness
Confirm the operator understands the invocation surface and bounded-pilot routing:

Reference:
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`
- `scripts&#47;ops&#47;run_bounded_pilot_session.py`

Expected understanding:
- bounded-pilot run goes through the controlled invocation path
- execution-event evidence expectations depend on actual order attempts occurring
- acceptance-oriented evidence requires valid acceptance conditions, not just signal generation

### 10. Evidence Expectation Before Run
Before starting, explicitly record what evidence is expected.

For rejected-order evidence runs:
- possible `order_submit`
- possible `order_reject`
- session-scoped execution-event file if an order attempt occurs

For acceptance-oriented runs:
- possible `order_submit`
- possible acceptance / acknowledgment / fill evidence depending on exact path and market behavior
- session-scoped execution-event file expected if the run reaches order attempt

### 11. Paper-Test Safety Guard
Confirm:
- this preflight did not alter paper-test artifacts
- this preflight did not start unrelated services
- this preflight did not mutate CI/workflow/governance state

## Recommended Operator Decision Block
Before launch, fill in this mini decision block:

- Intended Run Type:
  - rejected-order evidence
  - acceptance-oriented

- Entry Contract Confirmed:
  - yes / no

- Go/No-Go Confirmed:
  - yes / no

- Dry Validation Confirmed:
  - yes / no

- Ops Cockpit Reviewed:
  - yes / no

- Supervisor Stopped:
  - yes / no

- PT_EXEC_EVENTS_ENABLED needed:
  - yes / no

- Operator Approval to Start:
  - yes / no

## References
- `docs&#47;ops&#47;evidence&#47;TRIAL5_EXEC_EVENTS_POST_FIX_VERIFICATION_CLOSEOUT.md`
- `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`
- `scripts&#47;ops&#47;run_bounded_pilot_session.py`

## Conclusion
This checklist provides a conservative read-only preflight for the next bounded trial or acceptance-oriented run.

It is designed to keep the repository and paper-test environment stable while forcing explicit operator confirmation of:
- runtime quiet state
- run intent
- entry prerequisites
- evidence expectations
