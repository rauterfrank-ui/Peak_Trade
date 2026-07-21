---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6
STATUS: DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL
scope: research, offline-only, non-authorizing, terminal closeout
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR composite exit-efficiency — DEVELOPMENT evaluation v6

> **Non-authorizing:** Terminal closeout after exactly one authorized
> DEVELOPMENT_ONLY evaluation for hypothesis
> `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`.
> Economic change vs V5: composite side-aware midband-cross OR max-holding-horizon=48h.
> No holdout access. No Economic&#47;Promotion gate open. No rerun. No V7 auto-create.

## Status

`DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;FAIL`

- `RESULT_CLASS=FAIL`
- `REASON=NET_PROFIT_FACTOR_NOT_IMPROVED`
- `ECONOMIC_VERDICT=FAIL`
- `ACCEPTANCE_CRITERIA_MET=false`
- `EVALUATION_RUN_COUNT=1`
- `EVALUATION_COMPLETED=true`
- `PANEL_BACKTEST_EXECUTED=true`
- `HOLDOUT_DATA_ACCESSED=false`
- `RERUN_ALLOWED=false`
- `EXIT_DIVERGENCE_OBSERVED=true`
- Treatment binding: `exits_forced_by_gate=326` (`midband=318`, `max_holding=10`)
- Baseline trades `109` &#47; treatment trades `566`
- Baseline PF `~1.027` &#47; treatment PF `~0.924`
- Baseline net return `~-0.00041` &#47; treatment `~-0.00246`
- Members completed: baseline `46&#47;46`, treatment `46&#47;46`
- Mechanism: `canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1`
- Lifecycle checkpoint: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5`
- Base SHA: `60cb252fb47aa54bb554d29a029efa3b7666457f`
- Preregistration digest: `9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5`

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`
- Contract: `config&#47;research&#47;bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v6.json`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v6&#47;`

## Explicit non-actions

No V6 rerun. No holdout after FAIL. No retuning after FAIL. No V7 auto-create.
No economic&#47;promotion gate open. No runtime&#47;orders. No Master-V2 &#47; Double-Play &#47;
risk &#47; sizing &#47; execution mutation.
