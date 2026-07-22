# Evaluate volatility decay breakout development v1

```text
SLICE=EVALUATE_VOLATILITY_DECAY_BREAKOUT_DEVELOPMENT_V1
BASE_SHA=1a86f3b979c523733a39e85490624c0721e366b7
STATUS=FAIL_CLOSED_AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED
DEVELOPMENT_EVALUATION_AUTHORIZED=true
EVALUATION_EXECUTED=false
RUNNER_STARTED=false
DEVELOPMENT_DATASET_LOADED=false
HOLDOUT_ACCESSED=false
RUN_COUNT=0
RUNNER_START_COUNT=0
RUN_BUDGET_CONSUMED=false
RETRY_FORBIDDEN=true
```

## Exact command (single authorized attempt; durable slot not consumed)

```bash
python3 scripts/research/run_evaluate_volatility_decay_breakout_development_v1.py --mode evaluate --authorize-single-development-evaluation VOLATILITY_DECAY_BREAKOUT_NON_BITCOIN_PERPETUALS_V1
```

Authorized single development-evaluation attempt on
`1a86f3b979c523733a39e85490624c0721e366b7` resolved machine-checkable
authorization, then fail-closed before any panel open/dataset load because
`AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED_IN_THIS_SLICE`.

Durable run counters remain `0`. No `summary.json` / `registry.json` /
`run_slot_claim.json` were written. See `fail_closed_report.json`.

---
docs_token: DOCS_TOKEN_EVALUATE_VOLATILITY_DECAY_BREAKOUT_DEVELOPMENT_V1_FAIL_CLOSED_PANEL_BOUNDARY_NOT_MATERIALIZED
STATUS: FAIL_CLOSED_AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED
scope: research, offline-only, fail-closed-evidence
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
