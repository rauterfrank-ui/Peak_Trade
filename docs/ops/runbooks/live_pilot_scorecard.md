# Live Pilot Scorecard

Operational readiness gate for a **minimal-notional** live pilot (operational guidance, not financial advice).

## Inputs

- stability_gate.json
- live_readiness_scorecard.json
- shadow_testnet_scorecard.json
- execution_evidence.json

## Decision

- READY_FOR_LIVE_PILOT | CONTINUE_TESTNET | NO_GO

## Defaults (conservative)

- min_sample_size = 100
- max_anomalies = 0
- any execution errors => NO_GO

## Workflow

- .github/workflows/prbi-live-pilot-scorecard.yml

## Caps / Rollback

- Minimal notional: start with smallest position sizes; strict caps.
- Kill-switch must be reachable and tested.
- Rollback: stop orders, cancel open, reconcile state, collect evidence.
