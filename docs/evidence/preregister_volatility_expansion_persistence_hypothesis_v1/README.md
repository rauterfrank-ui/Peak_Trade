# Preregister volatility expansion persistence hypothesis v1

```text
SLICE=PREREGISTER_VOLATILITY_EXPANSION_PERSISTENCE_HYPOTHESIS_V1
BASE_SHA=e40f4ff9023543b1a38a89c8436780c355a02803
CLASS=DEFINITION_ONLY
PROGRAM_ID=VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STRATEGY_ID=VOLATILITY_EXPANSION_PERSISTENCE_V1
SIGNAL_FAMILY=VOLATILITY_REGIME
TARGET_PHENOMENON=VOLATILITY_EXPANSION_PERSISTENCE_AFTER_CONFIRMED_EXPANSION
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
MATERIAL_DIFFERENCE_FROM_VCB_V1=true
NO_VCB_RETRY=true
```

## Purpose

Preregister exactly one falsifiable own-instrument volatility-regime
expansion-persistence economic hypothesis and its frozen measurement contract
under `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`. No strategy producer. No
evaluation run. No dataset load. No holdout access. No run-slot consumption.
No retry of `VOLATILITY_COMPRESSION_BREAKOUT_V1`.

## Contract owner

`config/research/volatility_expansion_persistence_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Baseline

`UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1` — identical unconditional 20-bar
channel breakout; sole difference is expansion-persistence admission.

## Directional form

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT` — Double-Play remains sole
directional transition authority.

## Material difference vs VCB-V1

No compression prerequisite; no entry on confirmation bar t; ATR(14) with
two-bar >=0.80 expansion confirmation and persistence window t+1..t+6; not a
parameter repair/retry of VCB-V1.
