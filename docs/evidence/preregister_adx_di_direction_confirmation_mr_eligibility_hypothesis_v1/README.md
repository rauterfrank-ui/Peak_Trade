# Preregister ADX DI direction confirmation MR eligibility v1

```text
SLICE=PREREGISTER_ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HYPOTHESIS_V1
BASE_SHA=baadc192638e70ad713bb64e29258a0de2555491
BRANCH=research/preregister-adx-di-direction-confirmation-mr-entry-eligibility-v1
CLASS=DEFINITION_ONLY
HYPOTHESIS=ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
EVALUATION_AUTHORIZED=false
BACKTEST_AUTHORIZED=false
EVALUATION_RUN_COUNT=0
EVALUATION_RUN_LIMIT=1
HOLDOUT_ACCESSED=false
NO_EVALUATION_EXECUTED=true
```

## Scope

Definition-only preregistration of a single ADX(14) +DI/−DI direction-confirmation
pre-entry MR eligibility measurement contract on the sealed DEVELOPMENT_ONLY panel.
Orthogonal to six prior FAILs (regime, ATR, RSI, ADX-level, MA, MACD).

## Frozen filter

- `adx_period=14` from `config.toml` `[strategies.trend_following.defaults]`
- Calculator SSOT: `TrendFollowingStrategy._compute_adx`
- Long ELIGIBLE iff `minus_DI > plus_DI`
- Short ELIGIBLE iff `plus_DI > minus_DI`
- Tie / NaN → STAND_ASIDE
- `warmup_bars=28`; ADX level unused

## Declared future evaluation targets (not authorized here)

- Runner: `scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1.py`
- Evidence: `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`
- Package: `src/research/adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1/`

## Explicit non-actions

NO EVALUATION EXECUTED. No backtest, no economic metrics, no holdout, no runtime/orders,
no productive trading-logic mutation.
