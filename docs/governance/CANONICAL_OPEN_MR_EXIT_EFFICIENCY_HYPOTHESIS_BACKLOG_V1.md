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
V1, V2, V3, and V4 are terminal. No holdout access. No runtime activation.
No productive trading-logic mutation.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Preregistered hypotheses

Exactly zero (`preregistered_count_exact=0`).

## Terminal hypotheses

Exactly four:

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v1&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V2`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v2&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3`
  — `TERMINAL_FAIL`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=FAIL`
  — `REASON=identical_arms_no_exit_divergence`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v3&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4`
  — `TERMINAL_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INFRASTRUCTURE_FAILURE`
  — `DIAGNOSTIC_CLASS=PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v4&#47;`

## Explicit exclusions

- No V1&#47;V2&#47;V3&#47;V4 rerun under consumed preregistrations
- No V3&#47;V4 partial-result, checkpoint, or economic-result reuse
- No holdout after FAIL&#47;INFRASTRUCTURE_FAILURE
- No retuning after FAIL&#47;INFRASTRUCTURE_FAILURE
- No V5 auto-create
- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

Any further exit-efficiency measurement requires a new hypothesis ID under a
separate Operator-GO. No automatic V5 creation.
