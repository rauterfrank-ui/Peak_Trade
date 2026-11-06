# CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1 — Strategy Implementation Only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` — development evaluation unauthorized; slot unconsumed.

## Identity

- Strategy: `CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1`
- Hypothesis: `CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_NON_BITCOIN_PERPETUALS_V1`
- Predecessor: `VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1` (terminal DEVELOPMENT_FAIL)
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Dataset binding: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`

## Mechanism

Confirmed high cross-sectional RV-level rank (CS-RV-rank >= 0.80 for >= 2 bars)
admits fade opposite the short-horizon signed return (8 bars). Fill at open of t+1.
Low CS-vol-rank entries forbidden. BTC and spot excluded from ranking universe.
Panel members required min = 10. Rearm below 0.50. No channel/expansion/term-structure
prerequisite. Measurement contract digest frozen.

## Exits

`INITIAL_STOP` → `CROSS_SECTIONAL_VOL_RANK_NORMALIZATION_INVALIDATION` (<0.55) →
`REGIME_INVALIDATION` (<0.40) → `TIME_EXIT` → EOI&#47;EOP. Trailing forbidden.
Productive PnL evaluator reused. Risk&#47;sizing unchanged; Master-V2 &#47; Double-Play sole
directional authority.

## Safety

- `EVALUATION_EXECUTED=false`
- `DEVELOPMENT_RUN_COUNT=0`
- `RUN_SLOT_CONSUMED=false`
- `HOLDOUT_ACCESSED=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`

## Next

Separate operator GO for bounded Development evaluation:
`GO_CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1`

docs_token: DOCS_TOKEN_CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
