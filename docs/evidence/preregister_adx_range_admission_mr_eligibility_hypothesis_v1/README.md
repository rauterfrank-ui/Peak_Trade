# Preregister ADX range-admission MR eligibility hypothesis v1

```text
SLICE=PREREGISTER_ADX_RANGE_ADMISSION_MR_ELIGIBILITY_HYPOTHESIS_V1
BASE_SHA=09472b33a4cc4a3abe819bc46d149bc4b7c4392a
CLASS=DEFINITION_ONLY
HYPOTHESIS_COUNT=1
MULTIPLE_TESTING_BUDGET=1
EVALUATION_RUN_COUNT_AUTHORIZED=1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
HOLDOUT_FORBIDDEN=true
BACKTEST=false
METRICS=false
DEVELOPMENT_PANEL_ACCESSED=false
ENTRY_ELIGIBILITY_DIVERGENCE_REQUIRED=true
PRIMARY_DECISION_METRIC=NET_PROFIT_FACTOR
PROMOTION_ELIGIBLE=false
```

## Purpose

Preregister exactly one falsifiable economic hypothesis and its frozen measurement
contract against the sealed independent DEVELOPMENT_ONLY panel. No evaluation run.

## Contract owner

`config/research/adx_range_admission_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Treatment

Pre-entry ADX(14) range-admission eligibility filter only (canonical
`[strategies.trend_following.defaults]` ADX period/threshold; calculator SSOT
`src&#47;strategies&#47;trend_following.py` (`TrendFollowingStrategy._compute_adx`),
Wilder ewm). Master V2 / Double-Play remain sole direction authority.
No productive trading-logic change in this slice.

## Distinction from prior FAILs (orthogonal mechanism)

Prior contracts failed with:

1. `identical_arms_gate_inactive_on_entries` (absolute-threshold multi-feature regime)
2. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (ATR percentile mid-band)
3. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (RSI exhaustion)

This contract does not reuse or retune those mechanisms; it uses single-feature
Wilder ADX(14) range admission (`ADX < 25`) and requires observed entry-eligibility
divergence as a hard measurement condition.
