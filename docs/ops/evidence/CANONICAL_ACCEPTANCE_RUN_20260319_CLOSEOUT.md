# CANONICAL ACCEPTANCE RUN 2026-03-19 CLOSEOUT

## Status
- Project: Peak_Trade
- Topic: acceptance_run_via_canonical_runbook_closeout
- Branch Baseline: `main`
- Closeout State: **completed**
- Purpose: document the first acceptance-oriented bounded run executed through the canonical operator path and evaluated against the acceptance evidence standard

## Operator Path
Canonical runbook:
- `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`

Launcher path used:
- `scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py`

## Run Identity
- `session_id`: `session_20260319_154236_bounded_pilot_cb1e82`
- `run_id`: `bounded_pilot_ma_crossover_20260319_154236_aca306ad`

## Timing
- `started_at`: `2026-03-19T15:42:35`
- `finished_at`: `2026-03-19T16:06:41`

## Run Configuration
- `mode`: `bounded_pilot`
- `strategy`: `ma_crossover`
- `steps`: `25`
- `position_fraction`: `0.0005`
- `status`: `completed`

## Outcome Class
- `accepted-and-filled`

## Execution Summary
- `num_orders`: `1`
- `num_trades`: `1`
- `fill_rate`: `1.0`

## Execution Event Evidence
Session-scoped execution-event file:
- `out&#47;ops&#47;execution_events&#47;sessions&#47;session_20260319_154236_bounded_pilot_cb1e82&#47;execution_events.jsonl`

Observed events:
1. `order_submit`
   - `ts`: `2026-03-19T15:43:38`
   - side: `BUY`
   - symbol: `BTC&#47;EUR`
   - qty: `0.0005`

2. `fill`
   - `ts`: `2026-03-19T15:43:39`
   - qty: `0.0005`
   - price: `59930.1`

## Live-Session Report
- `reports&#47;experiments&#47;live_sessions&#47;20260319T154235_live_session_bounded_pilot_session_20260319_154236_bounded_pilot_cb1e82.json`

## Acceptance Evidence Standard Check
Required artifacts present:
1. session-scoped execution-event file
2. live-session report
3. closeout document
4. next-step handoff

Required closeout fields present:
- `session_id`
- `run_id`
- `mode`
- `strategy`
- `started_at`
- `finished_at`
- `steps`
- `position_fraction`
- `status`
- execution-event path
- live-session report path
- outcome class
- operator interpretation
- next-step recommendation

## Operator Interpretation
This run satisfies the canonical acceptance path:
- preflight and launcher path were used
- session-scoped evidence was preserved
- the run reached accepted-and-filled outcome
- the evidence package matches the acceptance evidence standard

## Next-Step Recommendation
- use this run as the canonical accepted-and-filled evidence example for future acceptance-oriented bounded runs
- continue strengthening operator packaging around the canonical launcher + evidence standard
