# RUNBOOK — Pilot Incident: Telemetry Degraded

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Operator response for degraded telemetry or incomplete evidence during bounded pilot activity
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED

## Trigger
- stale evidence freshness
- missing telemetry segments
- system appears healthy while observability is degraded

## Immediate Posture
- treat truth visibility as degraded
- prefer `NO_TRADE` when evidence continuity is insufficient
- do not assume healthy status from partial telemetry

## Operator Steps
1. verify what evidence is missing
2. confirm whether current exposure/order state is still trustworthy
3. if trust boundary is unclear, freeze progression
4. record degraded telemetry interval
5. resume only after evidence continuity is restored

## Evidence
- telemetry gap window
- affected truth sources
- operator classification
- final posture decision
