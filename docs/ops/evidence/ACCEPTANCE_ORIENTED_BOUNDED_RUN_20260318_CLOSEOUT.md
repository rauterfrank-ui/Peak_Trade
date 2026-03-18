# ACCEPTANCE ORIENTED BOUNDED RUN 2026-03-18 CLOSEOUT

## Status
- Project: Peak_Trade
- Topic: acceptance_run_closeout
- Branch Baseline: `main`
- Closeout State: **completed**
- Run Type: **B — acceptance-oriented**
- Purpose: verify actual exchange acceptance and fill under bounded-pilot conditions

## Objective
Document the completed acceptance-oriented bounded-pilot run that reached real exchange processing and produced a successful fill after conservative sizing adjustment.

## Run Identity
- `session_id`: `session_20260318_215745_bounded_pilot_d6e3f1`
- `run_id`: refer to session report

## Timing
- `started_at`: `2026-03-18T21:57:45`
- `finished_at`: `2026-03-18T22:21:52`

## Execution Summary
- `mode`: `BOUNDED_PILOT`
- `status`: `completed`
- `steps`: `25`
- `position_fraction`: `0.0005`
- `num_orders`: `1`
- `num_trades`: `1`
- `fill_rate`: `1.0`

## Acceptance Outcome
The bounded-pilot run produced a real order submission that was accepted and filled.

Observed early evidence:
1. `order_submit`
   - around `2026-03-18T21:58:47`
   - side: `BUY`
   - symbol: `BTC&#47;EUR`
   - qty: `0.0005`

2. `fill`
   - around `2026-03-18T21:58:49`
   - qty: `0.0005`
   - fill price: `62207.0`

## Execution Event Evidence
Session-scoped execution-event file:
- `out&#47;ops&#47;execution_events&#47;sessions&#47;session_20260318_215745_bounded_pilot_d6e3f1&#47;execution_events.jsonl`

Expected evidence class:
- `order_submit`
- `fill`

This confirms the bounded-pilot path can now produce not only rejected-order evidence, but also actual accepted-and-filled exchange evidence when sizing is conservative enough.

## Session Report
Live-session report:
- `reports&#47;experiments&#47;live_sessions&#47;20260318T215745_live_session_bounded_pilot_session_20260318_215745_bounded_pilot_d6e3f1.json`

Verified report fields:
- `status = completed`
- `steps = 25`
- `position_fraction = 0.0005`
- `num_orders = 1`
- `num_trades = 1`
- `fill_rate = 1.0`

## Why This Run Succeeded
Earlier acceptance-oriented attempts failed because effective order size was too large relative to available EUR balance.

The bounded-pilot wrapper now supports a conservative position-fraction override, and this run used:
- `position_fraction = 0.0005`

That reduced notional size enough to allow exchange acceptance and fill under the bounded-pilot constraints.

## Interpretation
This run proves:
- valid exchange credentials were present in the actual execution environment
- bounded-pilot invocation reached real exchange acceptance
- execution-event evidence captured the accepted path
- the reduced size control is effective for constrained-balance acceptance verification

## Operator Outcome
Acceptance-oriented bounded run objective achieved.

The system now has documented evidence for:
- rejected-order evidence path
- accepted-and-filled bounded-pilot path

## Related References
- `docs&#47;ops&#47;evidence&#47;TRIAL5_EXEC_EVENTS_POST_FIX_VERIFICATION_CLOSEOUT.md`
- `docs&#47;ops&#47;evidence&#47;TYPE_A_BOUNDED_TRIAL_20260318_REJECTED_ORDER_EVIDENCE_CLOSEOUT.md`
- `docs&#47;ops&#47;runbooks&#47;NEXT_BOUNDED_TRIAL_PREFLIGHT_CHECKLIST.md`
- `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`

## Conclusion
The acceptance-oriented bounded-pilot run on 2026-03-18 completed successfully and produced a real filled order under bounded conditions.

This is a stronger evidence milestone than rejected-order-only runs because it confirms actual exchange acceptance and fill with session-scoped execution-event evidence.
