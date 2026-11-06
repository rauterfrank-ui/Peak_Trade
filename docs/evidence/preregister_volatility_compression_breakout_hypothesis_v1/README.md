# Preregister volatility compression breakout hypothesis v1

```text
SLICE=PREREGISTER_VOLATILITY_COMPRESSION_BREAKOUT_HYPOTHESIS_V1
BASE_SHA=fd9b1cd214413a56cf6fb26b09a33f8364fb6972
CLASS=DEFINITION_ONLY
PROGRAM_ID=VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STRATEGY_ID=VOLATILITY_COMPRESSION_BREAKOUT_V1
SIGNAL_FAMILY=VOLATILITY_REGIME
TARGET_PHENOMENON=VOLATILITY_COMPRESSION_TO_EXPANSION_TRANSITION
HYPOTHESIS_COUNT=1
MULTIPLE_TESTING_BUDGET=1
DATASET=pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1
DATASET_CLASS=DEVELOPMENT_ONLY
DATASET_BOUND=true
HOLDOUT_FORBIDDEN=true
HOLDOUT_BOUND=false
BASELINE_ID=UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1
BACKTEST=false
METRICS=false
PROMOTION_ELIGIBLE=false
IMPLEMENTATION_PRESENT=false
DEVELOPMENT_RUN_COUNT=0
RUNNER_START_COUNT=0
```

## Purpose

Preregister exactly one falsifiable own-instrument volatility-regime
compression→expansion→channel-breakout economic hypothesis and its frozen
measurement contract. No strategy producer. No evaluation run. No dataset load.
No holdout access. No run-slot consumption.

## Contract owner

`config/research/volatility_compression_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Baseline

`UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1` — identical unconditional 20-bar channel breakout; sole
difference is compression→expansion admission.

## Directional form

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT` — Double-Play remains sole directional transition authority.
