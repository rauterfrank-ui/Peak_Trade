# Pilot Execution Edge-Case Matrix

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical edge-case matrix for limited pilot-ready execution hardening
docs_token: DOCS_TOKEN_PILOT_EXECUTION_EDGE_CASE_MATRIX

## Intent
This document enumerates the highest-load-bearing execution edge cases that must be understood and bounded before a tightly capped, operator-supervised pilot with real funds could be considered.

## Severity Legend
- Critical: unresolved ambiguity must block pilot progression
- High: requires explicit mitigation and operator handling
- Medium: requires bounded handling and evidence
- Low: monitor and document

## Edge-Case Matrix

| Domain | Edge Case | Example Failure Mode | Risk | Expected Safe Behavior | Required Evidence / Control |
|---|---|---|---|---|---|
| Broker/API | Order ack timeout | order submitted but acknowledgement unclear | Critical | treat as ambiguous, no blind re-submit, reconcile first | audit trail, idempotency/reconciliation strategy |
| Broker/API | Reject | order rejected by exchange/broker | High | no retry without explicit rule, surface reason | reject capture, operator visibility |
| Broker/API | Duplicate submission | duplicate order due to retry/restart | Critical | prevent duplicate effect, reconcile before retry | idempotency key or equivalent guard |
| Broker/API | Cancel/replace inconsistency | cancel accepted late, replace overlaps | Critical | freeze follow-up action until state is reconciled | order state reconciliation |
| Broker/API | Rate-limit/degraded exchange | delayed or partial API behavior | High | degrade to NO_TRADE / safe stop when state is unreliable | dependency degradation signal |
| Fill/Execution | Partial fill | order partially fills then stalls | High | recompute exposure, avoid assuming full fill | fill-aware position accounting |
| Fill/Execution | Stale order state | local view differs from broker | Critical | do not continue based on stale assumptions | explicit stale-state detection |
| Fill/Execution | Stale position state | exposure unknown after restart/failure | Critical | block further execution until reconciled | position reconciliation evidence |
| Fill/Execution | Fee/slippage underestimation | strategy assumes unrealistic execution cost | High | bounded assumptions, conservative caps | realistic fee/slippage model |
| Session/Recovery | Restart mid-session | process restarts during active orders | Critical | rebuild state before any further action | restart/recovery runbook |
| Session/Recovery | Replay ambiguity | replay duplicates prior effect | Critical | replay must be idempotent or blocked | replay safety rules |
| Session/Recovery | Session end mismatch | local closeout differs from broker reality | High | unresolved mismatch => blocked next session | end-of-session reconciliation |
| Balance/Treasury | Treasury/trading separation unclear | wrong balance basis used for execution | Critical | pilot blocked until separation is explicit | canonical balance model |
| Balance/Treasury | Stale balance | balance snapshot out of date | High | no new action on stale funds view | freshness / stale-balance checks |
| Reconciliation | Unexpected exposure | exposure exceeds intended bounds | Critical | safe stop / kill-switch / escalation | bounded pilot caps + incident path |
| Reconciliation | Transfer ambiguity | asset transfer status unclear | High | freeze risk-taking until resolved | transfer auditability |
| Incident | Telemetry degraded | signals incomplete while system appears healthy | High | operator warning, prefer NO_TRADE on ambiguity | evidence freshness + degraded mode |
| Incident | Kill-switch active | safety override engaged | Critical | no trade action, surface blocked state | explicit kill-switch visibility |

## Cross-Cutting Rules
- ambiguity must resolve to `NO_TRADE` or safe stop
- pilot-ready does not imply autonomy
- unresolved treasury/balance/position ambiguity blocks progression
- degraded dependencies must be visible to the operator
- reconciliation must dominate convenience

## Relationship to Other Planned Outputs
- this matrix should feed a future pilot go/no-go checklist
- this matrix should inform future incident runbooks
- this matrix should inform a future reconciliation flow spec
