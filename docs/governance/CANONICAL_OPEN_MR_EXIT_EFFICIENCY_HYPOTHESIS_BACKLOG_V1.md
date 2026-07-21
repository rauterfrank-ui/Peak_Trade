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
research candidates. No `DEFINITION_ONLY_PREREGISTERED` hypothesis remains open.
V1 and V2 are both terminal infrastructure-inconclusive. No holdout access. No
runtime activation. No productive trading-logic mutation.

## Binding

- SSOT: `config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Terminal hypotheses

Exactly two:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `EVALUATION_STARTED=true`
  — `EVALUATION_COMPLETED=false`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v1/`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `EVALUATION_STARTED=true`
  — `EVALUATION_COMPLETED=false`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `RERUN_ALLOWED=false`
  — `V2_IS_RERUN_OF_V1=false`
  — `V1_PARTIAL_RESULTS_REUSED=false`
  — `PROCESS_DEATH_ROOT_CAUSE=PREMEASUREMENT_GATE_FALSE_POSITIVE_ZERO_OR_SENTINEL`
  — Observability: `EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1`
  — Evidence: `docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v2/`

## Preregistered hypotheses

None (`preregistered_count_exact=0`).

## Explicit exclusions

- No V1 rerun under the consumed V1 preregistration
- No V2 rerun under the consumed V2 preregistration
- No V1 partial-result or checkpoint reuse into V2
- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

Any new midband exit-efficiency measurement requires a new hypothesis ID and a
separate Operator-GO after the V2 premeasurement falsy-zero gate fix is present
in the evaluation package. No V1/V2 rerun.
