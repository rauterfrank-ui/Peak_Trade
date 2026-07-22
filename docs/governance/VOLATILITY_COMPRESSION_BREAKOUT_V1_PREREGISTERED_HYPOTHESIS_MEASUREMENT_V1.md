# Volatility Compression Breakout v1 Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — all operator thresholds frozen; no evaluation.

## Identity

- Hypothesis: `VOLATILITY_COMPRESSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1`
- Strategy: `VOLATILITY_COMPRESSION_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Target phenomenon: `VOLATILITY_COMPRESSION_TO_EXPANSION_TRANSITION`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Contract digest: `01b88e863470b44a1b0a7fa312f514b503de78cbcb499be638ea39b60fae3113`

## Frozen mechanism (operator-authorized)

- Vol estimator: ATR(20)/close, past-only
- Compression: percentile rank lookback 120, threshold <=0.20, min duration 12 bars
- Expansion: percentile rank >=0.75 within 6 bars after compression
- Entry: mutually exclusive 20-bar completed channel break after expansion
- Exit: initial 1.5×ATR stop; trailing 2.0×ATR risk-reducing; regime exit <0.50; time exit 48 bars; first event wins
- Event sufficiency: >=50 evaluable events AND >=20 executed trades AND >=10 events/segment
- Costs: fee 10 bps/side, slippage 5 bps/side, half-spread 5 bps

## Dataset

- Bound DEVELOPMENT_ONLY: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- Holdout: unbound, untouched, access forbidden

## Run budget

- development_run_limit=1
- development_run_count=0
- retry_forbidden=true

## Material difference

Explicit and checkable against terminal
`VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1` (see measurement contract
`material_difference_vs_terminal_coiled_spring`).

## Next step

`REVIEW_AND_MERGE_DEFINITION_ONLY_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_STRATEGY_IMPLEMENTATION_THEN_DEVELOPMENT_EVALUATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
