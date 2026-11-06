# Preregister MACD histogram-countertrend MR eligibility hypothesis v1

```text
SLICE=PREREGISTER_MACD_HISTOGRAM_COUNTERTREND_MR_ELIGIBILITY_HYPOTHESIS_V1
BASE_SHA=4138ba5af3ebfd8d35fdff10986beec7bba88aae
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

`config/research/macd_histogram_countertrend_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Treatment

Pre-entry MACD(12,26,9) histogram-sign countertrend eligibility filter only (canonical
`[strategies.macd.defaults]`; calculator SSOT `src&#47;strategies&#47;macd.py` (`_calculate_macd`)).
Master V2 / Double-Play remain sole direction authority.
No productive trading-logic change in this slice.

## Distinction from prior FAILs (orthogonal mechanism)

Prior contracts failed with:

1. `identical_arms_gate_inactive_on_entries` (absolute-threshold multi-feature regime)
2. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (ATR percentile mid-band)
3. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (RSI exhaustion)
4. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (ADX range admission)
5. `net_profit_factor_not_improved_despite_entry_eligibility_divergence` (MA SMA(50) with-trend admission)

This contract does not reuse or retune those mechanisms; it uses single-feature
MACD histogram-sign countertrend admission (long iff histogram < 0; short iff
histogram > 0) and requires observed entry-eligibility divergence as a hard
measurement condition.
