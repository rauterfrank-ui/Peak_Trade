# Bollinger/MR midband exit-efficiency — DEVELOPMENT evaluation v4

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V4
STATUS: AWAITING_EVALUATION_EXECUTION
scope: research, offline-only, non-authorizing, evaluation-surface
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Evaluation surface for the sole authorized DEVELOPMENT_ONLY
> run of hypothesis
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`.
> This stub precedes the one-shot run. No evaluation executed in this slice.
> No holdout access. No Economic/Promotion gate open. No Master-V2 / Double-Play /
> risk / sizing / execution mutation. V1, V2, and V3 remain terminal and are not
> rerun.

## Status

`AWAITING_EVALUATION_EXECUTION`

- `EVALUATION_RUN_COUNT=0` (authorized later: exactly one run `0→1`)
- `EVALUATION_STARTED=false`
- `EVALUATION_COMPLETED=false`
- `RESULT_CLASS=NOT_EVALUATED`
- `ECONOMIC_VERDICT=NOT_EVALUATED`
- Evidence directory is created only by a future authorized run (not pre-created)

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
- Predecessor (terminal FAIL, not rerun):
  `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
- Contract: `config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v4.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence (future): `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v4&#47;`
- Observability: `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
- Falsy-zero hygiene: `PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE`
- Binding fix: `MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX`
- Measurement-validity prerequisites (fail-closed before real panel):
  effective config digest inequality; open_side binding; exit observability;
  synthetic divergence

## Gates

- Economic offline gate closed
- Promotion closed
- Holdout untouched
- No runtime / orders
- No evaluation run in this slice
