# Canonical open MR exit-efficiency hypothesis backlog v1

## Current SSOT status

- Verdict: `CANONICAL_OPEN_MR_EXIT_EFFICIENCY_BACKLOG_ZERO_PREREGISTERED_V6_TERMINAL_FAIL`
- Preregistered: exactly zero
- Terminal: V1&#47;V2 `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; V3 `FAIL`; V4&#47;V5 `INFRASTRUCTURE_FAILURE`; V6 `FAIL`
- V6 reason: `NET_PROFIT_FACTOR_NOT_IMPROVED`
- V6 economic delta vs V5: composite midband-cross OR frozen max-holding-horizon=48h
- No V6&#47;V5&#47;V4&#47;V3&#47;V2&#47;V1 rerun. No V7 auto-create.
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
research candidates. Zero `DEFINITION_ONLY_PREREGISTERED` hypotheses remain.
V1–V6 are terminal. No holdout access. No runtime activation. No productive
trading-logic mutation.

## Binding

- SSOT: `config&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json`
- Validator: `src&#47;research&#47;canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.py`
- Baseline (immutable): `bollinger_bands_v2_full_canonical_system_economic_binding_v1`
- Required treatment type: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Preregistered hypotheses

Exactly zero (`preregistered_count_exact=0`).

## Terminal hypotheses

Exactly six:

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

## Explicit exclusions

- No V1&#47;V2&#47;V3&#47;V4&#47;V5&#47;V6 rerun under consumed preregistrations
- No V3&#47;V4&#47;V5&#47;V6 partial-result, checkpoint, or economic-result reuse
- No holdout after FAIL&#47;INFRASTRUCTURE_FAILURE
- No retuning after FAIL&#47;INFRASTRUCTURE_FAILURE
- No V7 auto-create
- No parallel SHORT-side hypothesis
- No holdout candidate
- No cost-structure-weakening hypothesis
- No entry-eligibility reopen
- Open unpreregistered exit-efficiency candidates: empty

## Next separate action

Any new hypothesis requires a separate Operator-GO for definition-only
preregistration. No automatic V7 creation. No V6 rerun.
