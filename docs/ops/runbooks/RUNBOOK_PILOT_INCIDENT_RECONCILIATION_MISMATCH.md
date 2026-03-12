# RUNBOOK — Pilot Incident: Reconciliation Mismatch

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Operator response for mismatch between local state and broker/exchange/evidence state
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH

## Trigger
- order/fill mismatch
- stale position state
- stale balance state
- session-end mismatch
- transfer ambiguity

## Immediate Posture
- `NO_TRADE` until mismatch is classified and bounded
- freeze risk expansion
- escalate if exposure cannot be verified

## Operator Steps
1. identify mismatch domain: orders / fills / positions / balances / transfers
2. gather broker/exchange truth
3. compare against local/evidence truth
4. classify reconciled / partial / ambiguous
5. resume only when ambiguity is removed

## Evidence
- trigger
- truth sources consulted
- mismatch summary
- classification
- final posture
