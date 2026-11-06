# Preregister entry-effective MR eligibility hypothesis v1

```text
SLICE=PREREGISTER_ENTRY_EFFECTIVE_MR_ELIGIBILITY_HYPOTHESIS_V1
BASE_SHA=66486fbd08b8e8401663fb0ef7d835c72360ca53
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
PROMOTION_ELIGIBLE=false
```

## Purpose

Preregister exactly one falsifiable economic hypothesis and its frozen measurement
contract against the sealed independent DEVELOPMENT_ONLY panel. No evaluation run.

## Contract owner

`config/research/entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Treatment

Pre-entry ATR percentile mid-band eligibility filter only (canonical
`vol_regime_filter` defaults). Master V2 / Double-Play remain sole direction
authority. No productive trading-logic change in this slice.

## Distinction from prior FAIL

Prior contract
`regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract.v1`
failed with `identical_arms_gate_inactive_on_entries`. This contract does not
reuse or retune that regime classifier; it requires observed entry-eligibility
divergence as a hard measurement condition.
