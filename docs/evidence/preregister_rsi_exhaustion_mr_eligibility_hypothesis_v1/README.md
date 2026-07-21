# Preregister RSI-exhaustion MR eligibility hypothesis v1

```text
SLICE=PREREGISTER_RSI_EXHAUSTION_MR_ELIGIBILITY_HYPOTHESIS_V1
BASE_SHA=695e050779633e1a9af6b7e2acb05ef7cf64d21e
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

`config/research/rsi_exhaustion_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json`

## Treatment

Pre-entry RSI(14) exhaustion-confirmation eligibility filter only (canonical
`rsi_exhaustion_filter` defaults, agreeing between `[strategy.rsi_strategy]` and
`[strategy.rsi_reversion_v1]`; calculator SSOT `src/strategies/rsi.py::calculate_rsi`,
EWM causal, not Wilder). Master V2 / Double-Play remain sole direction authority.
No productive trading-logic change in this slice.

## Distinction from prior FAILs (orthogonal mechanism)

Prior contract
`regime_gated_standaside_mr_preregistered_economic_hypothesis_measurement_contract.v1`
failed with `identical_arms_gate_inactive_on_entries` (absolute-threshold
multi-feature regime classifier).

Prior contract (PR #5361)
`entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract.v1`
failed with `net_profit_factor_not_improved_despite_entry_eligibility_divergence`
(ATR(14) rolling-percentile mid-band (25,75) `vol_regime_filter` primitive).

This contract does not reuse or retune either prior mechanism; it uses an
orthogonal momentum-exhaustion mechanism (RSI(14) oversold/overbought
confirmation) and requires observed entry-eligibility divergence as a hard
measurement condition, independently of the prior ATR contract's divergence
measurement.
