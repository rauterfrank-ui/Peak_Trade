# Preregister volatility decay breakout hypothesis v1

```text
SLICE=PREREGISTER_VOLATILITY_DECAY_BREAKOUT_HYPOTHESIS_V1
BASE_SHA=1cbf47479ea24139f24816ac95846dc0cc410779
CLASS=DEFINITION_ONLY
FORENSIC_CLASS=HYPOTHESIS_TERMINAL
PROGRAM_ID=VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STRATEGY_ID=VOLATILITY_DECAY_BREAKOUT_V1
SIGNAL_FAMILY=VOLATILITY_REGIME
TARGET_PHENOMENON=VOLATILITY_DECAY_AFTER_HIGH_VOL_THEN_CHANNEL_BREAKOUT
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
PRIOR_TERMINAL=VOLATILITY_EXPANSION_PERSISTENCE_V1
MATERIAL_DIFFERENCE_FROM_VEP_V1=true
MATERIAL_DIFFERENCE_FROM_VCB_V1=true
NO_VEP_RETRY=true
NO_VEP_EXIT_REPAIR=true
```

## Purpose

Preregister exactly one falsifiable own-instrument volatility-regime
decay-breakout economic hypothesis and its frozen measurement contract
under `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1` after terminal VEP-V1
`FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`. No strategy producer. No
evaluation run. No dataset load. No holdout access. No run-slot consumption.
No retry of `VOLATILITY_EXPANSION_PERSISTENCE_V1` or
`VOLATILITY_COMPRESSION_BREAKOUT_V1`.

## Contract owner

`config/research/volatility_decay_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Baseline

`UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1` — identical unconditional 20-bar channel breakout; sole
difference is volatility-decay admission.

## Directional form

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT` — Double-Play remains sole
directional transition authority.

## Material difference vs VEP-V1

High→low vol decay admission (t-1>=0.70 → t<0.40, falling ATR) with window
t+1..t+8 and rearm >=0.70; not expansion persistence; not an exit repair of
`UNPAIRABLE_ENTRY_NO_EXIT`.

---
docs_token: DOCS_TOKEN_PREREGISTER_VOLATILITY_DECAY_BREAKOUT_HYPOTHESIS_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
