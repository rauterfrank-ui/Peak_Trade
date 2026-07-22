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
- Contract digest: `7a4ba7b765a7e7cc16155cb77b1448536b79a5416e2d758039a5574a82a74519`

## Frozen mechanism (operator-authorized)

- Vol estimator: ATR(20)/close, past-only
- Compression: percentile rank lookback 120, threshold <=0.20, min duration 12 bars
- Percentile tie method: `WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF`
  (`count(window_values <= current_value) &#47; count(window_values)`)
- Current ATR20-normalized value is included as the last observation in the 120-window
- Expansion: percentile rank >=0.75 on release offsets 1..6 inclusive after last compression bar
- Compression cycle: `SINGLE_USE`; reset on successful entry, channel-miss, and window expiry
- Max one expansion trigger per release cycle
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

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=true`
- `HOLDOUT_AUTHORIZED=false` / `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged/closed
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0` / `RUN_LIMIT=1`

## Contract digest

`7a4ba7b765a7e7cc16155cb77b1448536b79a5416e2d758039a5574a82a74519`

## Next step

`DEVELOPMENT_EVALUATION_AUTHORIZED_AWAITING_BOUNDED_EXECUTION_GO`

---
docs_token: DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-only preregistration
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
