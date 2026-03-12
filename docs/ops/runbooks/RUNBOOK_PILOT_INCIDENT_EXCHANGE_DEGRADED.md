# RUNBOOK — Pilot Incident: Exchange Degraded

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Operator response for degraded exchange/broker behavior during bounded pilot activity
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED

## Trigger
- timeouts increase
- rejects spike
- rate-limit/degraded signals appear
- order/ack state becomes unreliable

## Immediate Posture
- prefer `NO_TRADE` / safe stop
- do not expand risk while exchange truth is unreliable
- escalate if exposure state is unclear

## Operator Steps
1. confirm current gate posture and kill-switch visibility
2. stop any new risk-increasing action
3. inspect order / fill / position truth sources
4. classify as degraded-but-reconcilable vs ambiguous
5. if ambiguous, remain blocked until reconciled

## Evidence
- degraded signal
- affected orders / fills / positions
- reconciliation notes
- final posture decision
