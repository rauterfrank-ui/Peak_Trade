# RUNBOOK — Pilot Incident: Session End Mismatch

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Operator response when local closeout state differs from broker reality at session end; unresolved mismatch blocks next session progression
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH

## Trigger
- session ended but local registry/closeout state differs from broker positions or balances
- reconciliation at session end reports partial or ambiguous
- next session cannot proceed until closeout is reconciled

## Immediate Posture
- block next session until mismatch is classified and resolved
- `NO_TRADE` until closeout state is reconciled
- freeze risk expansion; do not start new session on unresolved closeout

## Operator Steps
1. identify mismatch domain: positions / balances / cash vs local closeout view
2. gather broker/exchange truth (positions, balances, fill history)
3. compare against local session registry and evidence trail
4. classify reconciled / partial / ambiguous
5. if partial or ambiguous, escalate; do not assume safe to proceed
6. resume only when closeout is reconciled and evidence is recorded

## Evidence
- trigger (session end)
- truth sources consulted (broker positions, balances, local registry)
- mismatch summary
- classification
- final posture
- operator escalation if any

## Relationship
- subset of reconciliation mismatch; see `RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH`
- aligns with `RECONCILIATION_FLOW_SPEC` Session End and `PILOT_EXECUTION_EDGE_CASE_MATRIX` Session end mismatch
