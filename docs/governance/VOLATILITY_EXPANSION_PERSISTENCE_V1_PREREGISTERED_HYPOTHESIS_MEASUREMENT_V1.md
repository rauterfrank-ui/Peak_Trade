# Volatility Expansion Persistence v1 Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — all operator thresholds frozen; no evaluation.

## Identity

- Hypothesis: `VOLATILITY_EXPANSION_PERSISTENCE_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_EXPANSION_PERSISTENCE_AFTER_CONFIRMED_EXPANSION`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`

## Frozen mechanism (operator-authorized)

- Vol estimator: ATR(14)&#47;close, past-only
- Percentile: lookback 120, weak-less-than-or-equal empirical CDF, current value included
- Expansion confirmation on bar t:
  - percentile(t) >= 0.80
  - percentile(t-1) >= 0.80
  - percentile(t-2) < 0.80
  - normalized_atr(t) > normalized_atr(t-1)
- Persistence window: t+1..t+6 inclusive; single-use event; rearm requires percentile < 0.80
- Entry earliest at open of t+1; no entry on t&#47;t-1&#47;t-2; no compression prerequisite
- Direction: mutually exclusive 20-bar completed channel break; Double-Play sole authority
- Exit&#47;PnL: bind existing productive exit&#47;PnL evaluator; no second PnL truth
- Event sufficiency: >=50 evaluable events AND >=30 executed trades AND >=10 events&#47;segment
- Costs: fee 10 bps&#47;side, slippage 5 bps&#47;side, half-spread 5 bps

## Dataset

- Bound DEVELOPMENT_ONLY: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Holdout: unbound, untouched, access forbidden

## Run budget

- development_run_limit=1
- development_run_count=0
- retry_forbidden=true

## Material difference vs VCB-V1

No compression regime; no entry on confirmation bar; ATR(14) two-bar >=0.80
confirmation with persistence window; not a parameter repair&#47;retry of
`VOLATILITY_COMPRESSION_BREAKOUT_V1`.

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `HOLDOUT_AUTHORIZED=false` &#47; `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged&#47;closed
- `DEVELOPMENT_RUN_COUNT=0` &#47; `RUNNER_START_COUNT=0` &#47; `RUN_LIMIT=1`

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_PERSISTENCE_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
