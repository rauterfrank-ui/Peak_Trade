# ACCEPTANCE EVIDENCE STANDARD

## Purpose
Define the minimum evidence package and closeout fields required for acceptance-oriented bounded runs.

## Scope
Applies to bounded/acceptance-oriented runs that reach:
- order submission only
- rejected exchange outcome
- accepted-and-filled exchange outcome

## Evidence Classes

### A. Rejected-Order Evidence
Minimum required:
- `session_id`
- `run_id`
- bounded mode and strategy
- session-scoped execution-event path
- `order_submit`
- `order_reject`
- rejection reason
- live-session report path
- operator verdict

### B. Accepted-and-Filled Evidence
Minimum required:
- `session_id`
- `run_id`
- bounded mode and strategy
- `position_fraction`
- `steps`
- session-scoped execution-event path
- `order_submit`
- `fill`
- symbol
- qty
- fill price
- txid if available
- live-session report path
- final report status
- `num_orders`
- `num_trades`
- `fill_rate`
- operator verdict

## Required Artifacts
1. Session-scoped execution-event file
2. Live-session report
3. Closeout document on `main`
4. Handoff for next decision if the run changes the evidence position

## Required Closeout Fields
- `session_id`
- `run_id`
- `mode`
- `strategy`
- `started_at`
- `finished_at`
- `steps`
- `position_fraction` where relevant
- `status`
- execution-event path
- live-session report path
- outcome class:
  - no-order
  - rejected-order
  - accepted-and-filled
- operator interpretation
- next-step recommendation

## Optional but Strongly Preferred
- txid
- exact order side
- exact quantity
- exact price
- evidence of reproducibility when not first-of-kind

## Canonical Current Examples
Rejected-order evidence:
- `docs&#47;ops&#47;evidence&#47;TYPE_A_BOUNDED_TRIAL_20260318_REJECTED_ORDER_EVIDENCE_CLOSEOUT.md`

Accepted-and-filled evidence:
- `docs&#47;ops&#47;evidence&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_20260318_CLOSEOUT.md`
- `docs&#47;ops&#47;evidence&#47;LOCAL_SECRET_LAUNCHER_BOUNDED_RUN_20260319_CLOSEOUT.md`

## Non-Goals
- no weakening of gates
- no replacement of Entry Contract / Go-No-Go
- no secret-handling policy changes

## Acceptance Standard Decision Rule
A run counts as acceptance evidence only if:
- it reaches real exchange processing
- session-scoped evidence exists
- live-session report exists
- outcome is either rejected with exchange-side reason or accepted-and-filled

## Recommended Document Pair
For each acceptance-oriented run class:
- one closeout document under `docs&#47;ops&#47;evidence&#47;`
- one next-step handoff under `docs&#47;ops&#47;reviews&#47;`
