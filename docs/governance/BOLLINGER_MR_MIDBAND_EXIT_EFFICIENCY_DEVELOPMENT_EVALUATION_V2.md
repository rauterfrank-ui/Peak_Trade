# Bollinger/MR midband exit-efficiency — DEVELOPMENT evaluation v2 (terminal)

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V2
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Terminal closeout of the sole authorized DEVELOPMENT_ONLY
> evaluation slot for hypothesis
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`.
> No economic PASS/FAIL. No rerun under this preregistration. No holdout access.
> No Economic/Promotion gate open. No Master-V2 / Double-Play / risk / sizing /
> execution mutation. V1 remains terminal and was not rerun.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INCONCLUSIVE_INFRASTRUCTURE_FAILURE`

- `EVALUATION_RUN_COUNT=1` (slot consumed; was 0→1 exactly once)
- `EVALUATION_STARTED=true`
- `EVALUATION_COMPLETED=false`
- `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
- `ECONOMIC_VERDICT=NOT_EVALUATED`
- `PASS=false`
- `FAIL=false`
- `RERUN_ALLOWED=false`
- `BASELINE_MEMBERS_COMPLETED=0&#47;46`
- `TREATMENT_MEMBERS_COMPLETED=0&#47;46`
- `HOLDOUT_DATA_ACCESSED=false`
- `V1_RERUN=false`
- `V1_PARTIAL_RESULTS_REUSED=false`
- `PROCESS_DEATH_ROOT_CAUSE=PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL`
- Observability binding used:
  `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
- Predecessor (terminal, not rerun):
  `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
- Contract: `config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v2.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v2/`

## Terminal note (exact)

The sole authorized V2 development evaluation started (lifecycle attached; PID
recorded) and aborted in pre-measurement with `WORKER_EXCEPTION` /
`CONTRACT_EVALUATION_RUN_COUNT_NOT_ZERO`. Root cause:
`PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL` — `int(evaluation_run_count or -1)`
treated legitimate run_count `0` as missing. No panel member backtest ran. No
economic result was produced. The slot is consumed and no rerun is permitted
under this preregistration. The falsy-zero sentinel is corrected in
`panel_runner_v2.py` as hygiene only; that fix does **not** authorize a second
run under V2.

## Gates

- Economic offline gate closed
- Promotion closed
- Holdout untouched
- No runtime / orders
- Pass criteria unchanged / unused for economic decision
- Cost model canonical 1.0x unchanged

## Next separate action (not authorized here)

1. Any further midband exit-efficiency measurement requires a new hypothesis ID
   (e.g. V3) under a separate Operator-GO after the premeasurement gate fix is
   present in the evaluation package.
2. No V1 or V2 rerun.
