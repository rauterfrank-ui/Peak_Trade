# Bollinger/MR midband exit-efficiency — DEVELOPMENT evaluation v3 (terminal)

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V3
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL
scope: research, offline-only, non-authorizing, terminal-closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Terminal closeout of the sole authorized DEVELOPMENT_ONLY
> evaluation slot for hypothesis
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`.
> Economic `FAIL` under preregistered acceptance criteria
> (`identical_arms_no_exit_divergence`). No rerun under this preregistration.
> No holdout access. No Economic/Promotion gate open. No Master-V2 / Double-Play /
> risk / sizing / execution mutation. V1 and V2 remain terminal and were not rerun.
> No V4 auto-created.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;FAIL`

- `EVALUATION_RUN_COUNT=1` (slot consumed; was 0→1 exactly once)
- `EVALUATION_STARTED=true`
- `EVALUATION_COMPLETED=true`
- `RESULT_CLASS=FAIL`
- `ECONOMIC_VERDICT=FAIL`
- `REASON=identical_arms_no_exit_divergence`
- `ACCEPTANCE_CRITERIA_MET=false`
- `PASS=false`
- `FAIL=true`
- `RERUN_ALLOWED=false`
- `BASELINE_MEMBERS_COMPLETED=46&#47;46`
- `TREATMENT_MEMBERS_COMPLETED=46&#47;46`
- `HOLDOUT_DATA_ACCESSED=false`
- `V1_RERUN=false`
- `V2_RERUN=false`
- `V2_PARTIAL_RESULTS_REUSED=false`
- Observability binding used:
  `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Falsy-zero hygiene binding used:
  `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE`

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
- Predecessor (terminal, not rerun):
  `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
- Contract: `config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v3.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v3/`

## Terminal note (exact)

The sole authorized V3 development evaluation completed on the sealed DEVELOPMENT
panel (46&#47;46 baseline and treatment members). Treatment metrics were identical to
baseline; midband exit gate forced zero exits; `exit_divergence_observed=false`.
Under frozen `EXIT_DIVERGENCE_REQUIRED=true`, the preregistered decision class is
`FAIL` &#47; `identical_arms_no_exit_divergence`. Acceptance criteria were not met.
The slot is consumed; no rerun, holdout, or post-hoc retuning is permitted under
this preregistration. No V4 is auto-created.

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
2. No V1, V2, or V3 rerun.
3. No holdout after FAIL. No retuning after FAIL.
