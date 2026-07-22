# Preregister volatility contraction→expansion breakout hypothesis v1

```text
SLICE=PREREGISTER_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_HYPOTHESIS_V1
BASE_SHA=87ee3c24c0cb3a1d74ed5b53e9072cbd21d7f41d
CLASS=DEFINITION_ONLY
SCOPE_TYPE=PREREGISTRATION_ONLY
FORENSIC_CLASS=HYPOTHESIS_TERMINAL
PROGRAM_ID=VOLATILITY_REGIME_RESEARCH_PROGRAM_V1
STRATEGY_ID=VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1
SIGNAL_FAMILY=VOLATILITY_REGIME
TARGET_PHENOMENON=VOLATILITY_CONTRACTION_TO_EXPANSION_JOINT_DIRECTIONAL_BREAKOUT
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
DEVELOPMENT_EVALUATION_EXECUTED=false
DEVELOPMENT_RUN_COUNT=0
RUNNER_START_COUNT=0
DEVELOPMENT_SLOT_CONSUMED=false
PRIOR_TERMINAL=VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1
MATERIAL_DIFFERENCE_FROM_VDBX_V1=true
MATERIAL_DIFFERENCE_FROM_VDB_V1=true
MATERIAL_DIFFERENCE_FROM_VEP_V1=true
MATERIAL_DIFFERENCE_FROM_VCB_V1=true
NO_VDBX_RETRY=true
NO_VDB_RETRY=true
NO_VEP_RETRY=true
NO_VCB_RETRY=true
```

## Purpose

Preregister exactly one falsifiable own-instrument volatility-regime
contraction→expansion joint-breakout economic hypothesis and its frozen
measurement contract under `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1` after
terminal VDBX `FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`. No strategy producer.
No evaluation run. No dataset load. No holdout access. No run-slot consumption.
No retry of terminal VDBX/VDB/VEP/VCB.

## Contract owner

`config/research/volatility_contraction_expansion_breakout_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Baseline

`UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1` — identical unconditional 20-bar
channel breakout; sole difference is joint contraction→expansion admission.

## Directional form

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT` — Double-Play remains sole
directional transition authority.

## Material difference vs VDBX / VCB

Edge from CONTRACTION→EXPANSION realized-vol state transition with same-bar
directed break and pairable opposite-break exits; not a decay signal and not a
VCB delayed release-window parameter retune.

---
docs_token: DOCS_TOKEN_PREREGISTER_VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_HYPOTHESIS_V1
STATUS: DEFINITION_ONLY
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
