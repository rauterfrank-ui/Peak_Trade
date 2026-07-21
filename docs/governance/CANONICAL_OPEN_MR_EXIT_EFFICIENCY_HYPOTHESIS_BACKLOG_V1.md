# Canonical open MR exit-efficiency hypothesis backlog v1

---
docs_token: DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG
scope: research, offline-only, non-authorizing, definition-only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for Mean-Reversion exit-efficiency
research candidates. Exactly one `DEFINITION_ONLY_PREREGISTERED` DEVELOPMENT_ONLY
hypothesis (V2) is open. V1 remains terminal infrastructure-inconclusive and is
not a rerun target. No holdout access. No runtime activation. No productive
trading-logic mutation.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Terminal hypotheses

Exactly one:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `EVALUATION_STARTED=true`
  — `EVALUATION_COMPLETED=false`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v1&#47;`

## Preregistered hypotheses

Exactly one:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
  — `DEFINITION_ONLY_PREREGISTERED`
  — `EVALUATION_RUN_COUNT=0`
  — `EVALUATION_STARTED=false`
  — `EVALUATION_COMPLETED=false`
  — `RESULT_CLASS=NOT_EVALUATED`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `V2_IS_RERUN_OF_V1=false`
  — `V1_PARTIAL_RESULTS_REUSED=false`
  — identical definition semantics to V1
  — mandatory binding: `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
  — Contract: `config&#47;research&#47;bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v2.json`
  — Evidence: `docs&#47;evidence&#47;preregister_bollinger_mr_midband_exit_efficiency_hypothesis_v2&#47;`

## Explicit exclusions

- No V1 rerun under the consumed V1 preregistration
- No V1 partial-result or checkpoint reuse into V2
- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- No automatic evaluation in this definition-only slice
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

Review and merge this definition-only V2 preregistration. Any development
evaluation requires a separate Operator-GO and must use the repaired
`EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1` surface.
