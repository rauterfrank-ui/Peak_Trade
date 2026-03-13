# RUNBOOK — Pilot Incident: Restart Mid-Session

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Operator response when process restarts during active orders or open positions; rebuild state and reconcile before any further action
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION

## Trigger
- execution/session process restarted or crashed while orders were active or positions were open
- local ledgers (OrderLedger, PositionLedger) are empty on new process start
- broker/exchange may still have open orders or positions

## Immediate Posture
- `NO_TRADE` until state is rebuilt and reconciled
- freeze risk expansion; do not place new orders until reconciliation is complete
- treat as ambiguous until truth sources confirm coherent state

## Operator Steps
1. detect restart: process restarted; local ledgers empty; check `execution_events.jsonl` and logs for prior activity
2. gather truth sources: broker/exchange order state, positions, fills, balances; local `execution_events.jsonl`; kill switch state (`data&#47;kill_switch&#47;state.json`)
3. reconcile: compare broker truth against evidence trail; identify any orphan orders or stale positions
4. classify: reconciled / partially reconciled / ambiguous / operator escalation required
5. if partial or ambiguous, escalate; do not assume safe to proceed
6. resume only when order/position/balance state is coherent, no unresolved ambiguity, gates valid, evidence recorded

## Evidence
- trigger (restart mid-session)
- truth sources consulted (broker, execution_events.jsonl, kill switch state)
- reconciliation result (reconciled / partial / ambiguous)
- classification
- final posture
- operator escalation if any

## Relationship
- subset of reconciliation mismatch; see `RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH`
- aligns with `RECONCILIATION_FLOW_SPEC` (restart during active session trigger) and `PILOT_EXECUTION_EDGE_CASE_MATRIX` (Session/Recovery: Restart mid-session)
- closes gap in `PILOT_GO_NO_GO_OPERATIONAL_SLICE` row 10 (Restart / Replay)
