# Live Readiness Phase Tracker

Purpose: Track readiness milestones from research/shadow through governed live trading with explicit gates and operator-verifiable evidence.

## Status Model
- NOT_STARTED
- IN_PROGRESS
- READY_FOR_REVIEW
- APPROVED
- BLOCKED

## Phase Gates (High-Level)
| Phase | Goal | Gate | Evidence |
|------:|------|------|----------|
| P0 | Offline research validated | Deterministic runs, tests pass | Reports + test output |
| P1 | Shadow mode stability | Shadow runbooks + quality reports | Ops run logs + artifacts |
| P2 | Paper trading (if used) | Risk controls + monitoring | Metrics + runbook evidence |
| P3 | Live readiness review | Governance sign-off, safety checks | Go/No-Go evidence |
| P4 | Controlled live | Manual-only, bounded exposure | Risk logs + audit |
| P5 | Expanded live | Stability over time | Weekly health evidence |

## Operator Verification
- CI gates green on relevant PRs
- Risk controls enforced and auditable
- Runbooks updated and discoverable via ops index
