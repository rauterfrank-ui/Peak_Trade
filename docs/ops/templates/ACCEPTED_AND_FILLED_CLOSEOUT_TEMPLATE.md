# ACCEPTED AND FILLED CLOSEOUT TEMPLATE

## Status
- Project: Peak_Trade
- Topic: <topic_name>
- Branch Baseline: `main`
- Closeout State: <completed|draft>
- Purpose: document an accepted-and-filled bounded / acceptance-oriented run

## Operator Path
- runbook: `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- launcher path: `<launcher_or_direct_path>`

## Run Identity
- `session_id`: `<session_id>`
- `run_id`: `<run_id>`

## Timing
- `started_at`: `<started_at>`
- `finished_at`: `<finished_at>`

## Run Configuration
- `mode`: `<mode>`
- `strategy`: `<strategy>`
- `steps`: `<steps>`
- `position_fraction`: `<position_fraction>`
- `status`: `<status>`

## Outcome Class
- `accepted-and-filled`

## Execution Summary
- `num_orders`: `<num_orders>`
- `num_trades`: `<num_trades>`
- `fill_rate`: `<fill_rate>`

## Execution Event Evidence
Session-scoped execution-event file:
- `<execution_event_path>`

Observed events:
1. `order_submit`
   - `ts`: `<timestamp>`
   - `symbol`: `<symbol>`
   - `side`: `<side>`
   - `qty`: `<qty>`
   - `client_order_id`: `<client_order_id>`

2. `fill`
   - `ts`: `<timestamp>`
   - `symbol`: `<symbol>`
   - `side`: `<side>`
   - `qty`: `<qty>`
   - `price`: `<price>`
   - `txid`: `<txid_if_available>`

## Live-Session Report
- `<live_session_report_path>`

## Acceptance Evidence Standard Check
Required artifacts present:
1. session-scoped execution-event file
2. live-session report
3. closeout document
4. next-step handoff where needed

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
<what this run proves, and what it does not prove>

## Next-Step Recommendation
<recommended next step>
