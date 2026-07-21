# Bollinger/MR midband exit-efficiency — DEVELOPMENT evaluation v1 (terminal)

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V1
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Terminal closeout of the sole authorized DEVELOPMENT_ONLY
> evaluation slot. No economic PASS/FAIL. No rerun under this preregistration.
> No holdout access. No Economic/Promotion gate open. No Master-V2 / Double-Play /
> risk / sizing / execution mutation.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INCONCLUSIVE_INFRASTRUCTURE_FAILURE`

- `EVALUATION_RUN_COUNT=1` (slot consumed)
- `EVALUATION_STARTED=true`
- `EVALUATION_COMPLETED=false`
- `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
- `ECONOMIC_VERDICT=NOT_EVALUATED`
- `PASS=false`
- `FAIL=false`
- `RERUN_ALLOWED=false`
- `BASELINE_MEMBERS_COMPLETED=2&#47;46`
- `TREATMENT_MEMBERS_COMPLETED=0&#47;46`
- `HOLDOUT_DATA_ACCESSED=false`
- `PROCESS_DEATH_ROOT_CAUSE=UNKNOWN`

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
- Contract: `config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v1/`

## Terminal note (exact)

The sole authorized development evaluation started and died after baseline member 2/46.
No economic result was produced. The slot is consumed and no rerun is permitted under
this preregistration.

## Gates

- Economic offline gate closed
- Promotion closed
- Holdout untouched
- No runtime / orders
- Pass criteria unchanged / unused for economic decision
- Cost model canonical 1.0x unchanged

## Next separate action (not authorized here)

1. Fix generic runner lifecycle / observability cause and verify synthetically
2. Only then consider a separate V2 preregistration with a new hypothesis ID and run count 0
