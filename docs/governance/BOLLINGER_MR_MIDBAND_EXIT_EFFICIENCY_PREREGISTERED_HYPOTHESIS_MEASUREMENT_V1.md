# Bollinger/MR midband exit-efficiency — preregistered hypothesis and measurement v1

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: SUPERSEDED_BY_TERMINAL_EVALUATION_CLOSEOUT
scope: research, offline-only, non-authorizing, definition-only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definition-only preregistration of one DEVELOPMENT_ONLY exit-efficiency
> hypothesis derived from the sealed failure-decomposition `NEXT_RESEARCH_QUESTION`.
> No evaluation, no holdout access, no Economic/Promotion gate open, no Master-V2 /
> Double-Play / risk / sizing / execution mutation.

## Status

`DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract preregistered;
`EVALUATION_RUN_COUNT=0`; no evaluation executed.

## Binding

- Hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V1`
- Contract: `bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract.v1`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- `DEVELOPMENT_ONLY=true`
- `HOLDOUT_ALLOWED=false`
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1`
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only
- Baseline: `bollinger_bands_v2_full_canonical_system_economic_binding_v1` (immutable)
- Parent diagnostic: `bollinger_mr_economic_failure_decomposition_development_v1`
  (`DIAGNOSTIC_CLASS=COSTS_DESTROY_MARGINAL_EDGE`, `EXIT_LEAKAGE_MATERIAL=true`)
- Treatment: `POST_ENTRY_EXIT_EFFICIENCY_MECHANISM` (not implemented in this slice)
- Primary decision metric: `NET_PROFIT_FACTOR` (joint PASS requires all locked companions)

## Research question (exact)

`Given COSTS_DESTROY_MARGINAL_EDGE on the sealed DEVELOPMENT_ONLY Bollinger&#47;MR baseline (marginal gross PF~1.01, all-SHORT book), does a cost-structure or holding&#47;exit-efficiency change class exist that preserves gross edge without retuning terminal entry-eligibility parameters or reopening exhausted filter families?`

Scope selected: `EXIT_EFFICIENCY_ONLY` (not cost-structure weakening; not SHORT-side filter; not entry-eligibility reopen).

## Exit mechanism (ex ante, deterministic)

Canonical side-aware Bollinger middle-band mean-reversion exit from immutable baseline
binding parameters (`bb_period=20`, `bb_std=2.0`, exit level = middle band):

- LONG open: EXIT iff `close[t-1] < middle[t-1]` AND `close[t] >= middle[t]`
- SHORT open: EXIT iff `close[t-1] > middle[t-1]` AND `close[t] <= middle[t]`
- Stop-loss remains active if hit first
- Fail-closed if state &#47; bar-index &#47; digest binding missing
- No future MFE; no lookahead; no entry&#47;side&#47;instrument authority

`EXIT_DIVERGENCE_REQUIRED=true` — absence ⇒ `RESULT_CLASS=FAIL`.

## Pass criteria (frozen before any run)

PASS requires all of:

- `net_profit_factor_treatment > control`
- `net_pnl_treatment > control` and `net_return_treatment > control`
- MFE capture ratio improved
- MFE-to-exit leakage reduced
- improvement not solely explained by reduced trade count or artificially lower turnover
- no new instrument concentration
- canonical cost multiplier exactly `1.0` (never below)

## Terminal states

- `DEFINITION_ONLY_PREREGISTERED` (current)
- `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;PASS`
- `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;FAIL`

Maximum one development evaluation run.

## Gates

- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged&#47;closed
- On FAIL: retuning forbidden; holdout forbidden
- No runtime &#47; shadow &#47; testnet &#47; live &#47; orders
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false`
- `DOUBLE_PLAY_AUTHORITY_CHANGED=false`
- `RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false`

## Next step

Review and merge this definition-only PR before any development evaluation.


## Terminal evaluation closeout

See `docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V1.md`.
`RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE`; `EVALUATION_RUN_COUNT=1`; `RERUN_ALLOWED=false`.
