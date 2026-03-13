# RUNBOOK — Pilot Incident: Transfer Ambiguity

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Operator response when asset transfer status is unclear; unresolved transfer ambiguity blocks new dependent action
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY

## Trigger
- asset transfer (withdraw, deposit, internal transfer) status unclear
- transfer initiated but completion unknown
- transfer history or audit trail incomplete

## Immediate Posture
- freeze risk-taking until transfer status is resolved
- `NO_TRADE` until transfer ambiguity is classified and bounded
- do not start new dependent action on unresolved transfer state

## Operator Steps
1. identify transfer domain: withdraw / deposit / internal transfer
2. gather broker/exchange transfer history and status
3. compare against local evidence trail and intent
4. classify reconciled / partial / ambiguous
5. if partial or ambiguous, escalate; do not assume transfer completed
6. resume only when transfer state is reconciled and evidence is recorded

## Evidence
- trigger (transfer ambiguity)
- truth sources consulted (broker transfer history, local logs)
- transfer summary and status
- classification
- final posture
- operator escalation if any

## Relationship
- subset of reconciliation mismatch; see `RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH`
- aligns with `RECONCILIATION_FLOW_SPEC` Transfers and `PILOT_EXECUTION_EDGE_CASE_MATRIX` Transfer ambiguity
- treasury separation: bot key blocks transfer execution; this runbook covers status tracking when transfers occur (manual or external)
