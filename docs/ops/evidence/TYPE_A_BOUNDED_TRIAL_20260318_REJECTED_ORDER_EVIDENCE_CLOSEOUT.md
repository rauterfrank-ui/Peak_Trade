# TYPE A BOUNDED TRIAL 2026-03-18 REJECTED ORDER EVIDENCE CLOSEOUT

## Status
- Project: Peak_Trade
- Topic: type_a_bounded_trial_closeout
- Branch Baseline: `main`
- Closeout State: **completed**
- Run Type: **A — rejected-order-evidence**
- Purpose: verify bounded-pilot rejected-order evidence with session-scoped execution events

## Objective
Document the completed Type-A bounded-pilot run that produced a live order attempt and a rejected outcome, with execution-event evidence captured in the session-scoped path.

## Run Identity
- `session_id`: `session_20260318_192925_bounded_pilot_08b026`
- `run_id`: `bounded_pilot_ma_crossover_20260318_192926_21d00411`

## Timing
- `started_at`: `2026-03-18T19:29:25`
- `finished_at`: `2026-03-18T19:53:32`

## Execution Summary
- `mode`: `BOUNDED_PILOT`
- `steps`: `25`
- `status`: `completed`
- `num_trades`: `1`
- `num_orders`: `0`
- `fill_rate`: `0.0`

## Strategy / Signal Outcome
A signal transition occurred during the run:
- `0 -> 1`

This produced a bounded-pilot live order attempt.

## Observed Order Attempt
- side: `BUY`
- qty: `0.1`
- symbol: `BTC&#47;EUR`
- order type: `market`

## Exchange Outcome
The order was rejected because live Kraken API credentials were not set.

This outcome is valid for a Type-A rejected-order-evidence run and does not invalidate the evidence objective.

## Execution Event Evidence
Session-scoped execution-event file:
- `out&#47;ops&#47;execution_events&#47;sessions&#47;session_20260318_192925_bounded_pilot_08b026&#47;execution_events.jsonl`

Observed events:
1. `order_submit`
2. `order_reject`

These confirm that the bounded-pilot execution-event path is functioning correctly for rejected-order evidence.

## Session Report
Live-session report:
- `reports&#47;experiments&#47;live_sessions&#47;20260318T192925_live_session_bounded_pilot_session_20260318_192925_bounded_pilot_08b026.json`

## Interpretation
This run confirms:
- bounded-pilot invocation completed successfully
- the execution-event writer captured the rejected-order path
- session-scoped execution-event evidence is present
- the direct Trial-5 gap fix remains effective in a completed bounded-pilot session

## Operator Outcome
Type-A rejected-order-evidence objective achieved.

The run produced the intended evidence without requiring exchange acceptance.

## Related References
- `docs&#47;ops&#47;evidence&#47;TRIAL5_EXEC_EVENTS_POST_FIX_VERIFICATION_CLOSEOUT.md`
- `docs&#47;ops&#47;runbooks&#47;NEXT_BOUNDED_TRIAL_PREFLIGHT_CHECKLIST.md`
- `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`

## Conclusion
The Type-A bounded-pilot rejected-order-evidence run completed successfully on 2026-03-18.

The intended evidence was produced and captured in the session-scoped execution-event path.
