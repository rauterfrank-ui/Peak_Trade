---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_EVALUATION_V1
STATUS: EVALUATION_WIRING_ONLY_NO_EXECUTION
scope: research, offline-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger/MR midband exit reentry-cooldown — Holdout evaluation wiring v1

Implements the declared evaluation surfaces for successor
`BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1`.

## Lifecycle authority

Canonical lane vocabulary remains
`CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1`
(`OPEN_BACKLOG`, `POST_TERMINAL_OPERATOR_DECISION_REQUIRED`,
`AWAITING_EXPLICIT_SUCCESSOR_HYPOTHESIS`, `LANE_CLOSED_NO_FURTHER_RESEARCH`).

Exit lane SSOT status stays `OPEN_BACKLOG` with successor
`DEFINITION_ONLY_HOLDOUT_PREREGISTERED`. The operator-facing label
`AWAITING_HOLDOUT_EXECUTION_OPERATOR_GO` is not a lane-state vocabulary member;
readiness for the single holdout run is the separate execution GO + bound
authorization env fields.

## Explicit non-actions in this wiring slice

No holdout data access. No runner execution. No run-slot consumption.
No economic-gate open. No promotion/runtime/orders. No V7/V8 terminal mutation.
No Entry-lane reopen.

## Next

`SEPARATE_EXPLICIT_GO_REQUIRED_FOR_SINGLE_HOLDOUT_EXECUTION`
