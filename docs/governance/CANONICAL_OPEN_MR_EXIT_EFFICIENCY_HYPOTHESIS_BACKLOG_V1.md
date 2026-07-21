# Canonical open MR exit-efficiency hypothesis backlog v1

## Current SSOT status

- Verdict: `CANONICAL_OPEN_MR_EXIT_EFFICIENCY_BACKLOG_ONE_DEFINITION_ONLY_V8_PREREGISTERED`
- Preregistered: exactly one (`preregistered_count_exact=1`) — V8 reentry-cooldown
- Terminal: V1&#47;V2&#47;V7 `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; V3&#47;V6 `FAIL`; V4&#47;V5 `INFRASTRUCTURE_FAILURE`
- V7 remains terminal: `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; `FAILURE_CLASS=FROZEN_EXIT_PARAMETERS_MISMATCH`; `FAILURE_TIMING=BEFORE_PANEL_ACCESS`
- V7: `RUNNER_START_COUNT=1`; `RUN_SLOT_CONSUMED=true`; `RERUN_ALLOWED=false`; `V7_REOPEN_ALLOWED=false`
- V7: no development metrics; no economic PASS&#47;FAIL; not strategy-fail; not measurement-pass; no reopen
- V8: `DEFINITION_ONLY_PREREGISTERED`; `EVALUATION_RUN_COUNT=0`; `RUNNER_STARTED=false`; `RUN_SLOT_CONSUMED=false`
- V8 digest: `610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c`
- V8 structural hardening: complete `exit_mechanism.frozen_parameters` + pre-authorization parity validator
- V6 reason: `NET_PROFIT_FACTOR_NOT_IMPROVED`
- No V7&#47;V6&#47;V5&#47;V4&#47;V3&#47;V2&#47;V1 rerun. No V7 reopen. No V8 evaluation in this slice. No V9 auto-create.
- `NEXT_CANONICAL_ACTION=AWAIT_SEPARATE_OPERATOR_GO_FOR_V8_DEVELOPMENT_EVALUATION`
- Economic&#47;promotion gates closed. No runtime&#47;orders.

---
docs_token: DOCS_TOKEN_CANONICAL_OPEN_MR_EXIT_EFFICIENCY_HYPOTHESIS_BACKLOG_V1
STATUS: OPEN_BACKLOG
scope: research, offline-only, non-authorizing, terminal-governance closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

## Status

`OPEN_BACKLOG` — versioned canonical SSOT for Mean-Reversion exit-efficiency
research candidates. Zero preregistered hypotheses. V1–V7 are terminal.
No holdout access. No runtime activation. No productive trading-logic mutation.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Preregistered hypotheses

Exactly one (`preregistered_count_exact=1`): `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8` (`DEFINITION_ONLY_PREREGISTERED`, run count `0`).

## Terminal hypotheses

Exactly seven:

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

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5`
  — `TERMINAL_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INFRASTRUCTURE_FAILURE`
  — `DIAGNOSTIC_CLASS=PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — Baseline members completed `3&#47;46`; treatment `0&#47;46`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v5&#47;`

- `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`
  — `TERMINAL_FAIL`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=FAIL`
  — `REASON=NET_PROFIT_FACTOR_NOT_IMPROVED`
  — `ACCEPTANCE_CRITERIA_MET=false`
  — `EXIT_DIVERGENCE_OBSERVED=true`
  — Mechanism: `canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1`
  — Members completed: baseline `46&#47;46`; treatment `46&#47;46`
  — `RERUN_ALLOWED=false`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v6&#47;`
  — Governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6.md`
  — Failure attribution (evidence-only): `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`
  — Attribution governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION.md`


- `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7`
  — `TERMINAL_INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `EVALUATION_RUN_COUNT=1`
  — `RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
  — `FAILURE_CLASS=FROZEN_EXIT_PARAMETERS_MISMATCH`
  — `FAILURE_TIMING=BEFORE_PANEL_ACCESS`
  — `PANEL_BACKTEST_EXECUTED=false`
  — `DEVELOPMENT_METRICS_PRODUCED=false`
  — `ECONOMIC_VERDICT=NOT_EVALUATED`
  — `STRATEGY_FAIL=false` &#47; `ECONOMIC_FAIL=false` &#47; `MEASUREMENT_PASS=false`
  — `RERUN_ALLOWED=false` &#47; `V7_REOPEN_ALLOWED=false`
  — Digest: `4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680`
  — Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7&#47;`
  — Governance: `docs&#47;governance&#47;BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7.md`

## Explicit exclusions

- No V1&#47;V2&#47;V3&#47;V4&#47;V5&#47;V6 rerun under consumed preregistrations
- No V3&#47;V4&#47;V5&#47;V6 partial-result, checkpoint, or economic-result reuse
- No holdout after FAIL&#47;INFRASTRUCTURE_FAILURE
- No retuning after FAIL&#47;INFRASTRUCTURE_FAILURE
- No V7 rerun &#47; no V7 reopen
- No V7 auto-create
- No V8 auto-create
- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

`NEXT_CANONICAL_ACTION=AWAIT_SEPARATE_OPERATOR_GO_FOR_V8_DEVELOPMENT_EVALUATION`

No V7 rerun. No V7 reopen. No V8 evaluation in this slice. No V9 auto-create. No runner start.

## V7 terminal closeout

V7 DEVELOPMENT evaluation consumed its one-shot slot and terminated as `INCONCLUSIVE_INFRASTRUCTURE_FAILURE` (`FAILURE_CLASS=FROZEN_EXIT_PARAMETERS_MISMATCH`, `FAILURE_TIMING=BEFORE_PANEL_ACCESS`, diagnostic `PRE_PANEL_FROZEN_EXIT_PARAMETERS_MISMATCH_NO_PANEL_BACKTEST`). V7 remains terminal and unreopened. A separate V8 definition-only preregistration now exists with complete frozen-parameter SSOT and pre-authorization parity validation; V8 evaluation is not authorized in this slice. No V7 rerun. No V7 reopen. No V9 auto-create.
