# Bollinger/MR midband exit-efficiency — DEVELOPMENT evaluation v4 (terminal)

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V4
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INFRASTRUCTURE_FAILURE
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Terminal closeout of the sole authorized DEVELOPMENT_ONLY
> evaluation slot for hypothesis
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`.
> `RESULT_CLASS=INFRASTRUCTURE_FAILURE` after incomplete panel run (baseline 1/46;
> process died without economic closeout). No rerun under this preregistration.
> No holdout access. No Economic/Promotion gate open. No Master-V2 / Double-Play /
> risk / sizing / execution mutation. V1, V2, and V3 remain terminal and were not
> rerun. No economic PASS/FAIL claim from this incomplete run.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INFRASTRUCTURE_FAILURE`

- `EVALUATION_RUN_COUNT=1` (slot consumed; was 0→1 exactly once)
- `EVALUATION_STARTED=true`
- `EVALUATION_COMPLETED=false`
- `RESULT_CLASS=INFRASTRUCTURE_FAILURE`
- `DIAGNOSTIC_CLASS=PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
- `ECONOMIC_VERDICT=NOT_EVALUATED`
- `REASON=incomplete_panel_run_process_died_after_baseline_member_1_of_46`
- `ACCEPTANCE_CRITERIA_MET=false`
- `PASS=false`
- `FAIL=false`
- `RERUN_ALLOWED=false`
- `BASELINE_MEMBERS_COMPLETED=1&#47;46`
- `TREATMENT_MEMBERS_COMPLETED=0&#47;46`
- `MEASUREMENT_VALIDITY_PREFLIGHT=PASS`
- `HOLDOUT_DATA_ACCESSED=false`
- `V1_RERUN=false`
- `V2_RERUN=false`
- `V3_RERUN=false`
- Observability binding used:
  `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Falsy-zero hygiene binding used:
  `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE`
- Binding fix binding used:
  `MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX`

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
- Predecessor (terminal FAIL, not rerun):
  `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
- Contract: `config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v4.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v4&#47;`

## Terminal note (exact)

The sole authorized V4 development evaluation slot was claimed atomically, then
the runner started exactly once. Measurement-validity preflight passed. The panel
backtest began and completed baseline member 1&#47;46 (`1INCH-USDT-SWAP`). The process
then died without writing lifecycle terminal diagnostics. Under the one-shot rule
the slot remains consumed; the terminal class is `INFRASTRUCTURE_FAILURE` with
economic verdict `NOT_EVALUATED`. No auto-rerun, holdout, or post-hoc retuning is
permitted under this preregistration.

## Gates

- Economic offline gate closed
- Promotion closed
- Holdout untouched
- No runtime / orders
- Pass criteria unchanged
- Cost model canonical 1.0x unchanged

## Next separate action (not authorized here)

1. Any further midband exit-efficiency measurement requires a new hypothesis ID
   under a separate Operator-GO.
2. No V1, V2, V3, or V4 rerun.
3. No economic PASS&#47;FAIL claim from this incomplete run.
