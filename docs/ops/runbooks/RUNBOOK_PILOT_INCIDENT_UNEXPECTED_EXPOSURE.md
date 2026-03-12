# RUNBOOK — Pilot Incident: Unexpected Exposure

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Operator response for unexpected or out-of-bounds exposure during bounded pilot activity
docs_token: DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE

## Trigger
- exposure exceeds intended cap
- exposure source is unclear
- position state and intended cap diverge

## Immediate Posture
- safe stop / kill-switch posture if needed
- no new risk-taking
- remain blocked until exposure source is understood

## Operator Steps
1. confirm current exposure vs bounded pilot caps
2. verify position truth and recent fills
3. determine whether mismatch is reconciled, partial, or ambiguous
4. if ambiguous, maintain blocked posture
5. record operator escalation and resolution path

## Evidence
- observed exposure
- intended cap
- truth sources
- final classification
- final posture
