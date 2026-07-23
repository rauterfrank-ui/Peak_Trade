# VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1 — Strategy Implementation Only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` — evaluation unauthorized.

## Identity

- Strategy: `VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1`
- Hypothesis: `VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Predecessor: `VOLATILITY_TERM_STRUCTURE_REVERSION_V1` (terminal DEVELOPMENT_FAIL)
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`

## Mechanism

Depressed short&#47;long RV ratio (percentile <= 0.20 for >= 2 bars) admits
continuation with the short-horizon signed return. Fill at open of t+1.
Elevated-ratio entries forbidden. Rearm above 0.50.

## Exits

`INITIAL_STOP` → `TERM_STRUCTURE_NORMALIZATION_INVALIDATION` (>0.45) →
`REGIME_INVALIDATION` (>0.55) → `TIME_EXIT` → EOI&#47;EOP. Trailing forbidden.
Productive PnL evaluator reused.

## Safety

- `EVALUATION_EXECUTED=false`
- `DEVELOPMENT_RUN_COUNT=0`
- `HOLDOUT_ACCESSED=false`
- `LIVE_AUTHORIZED=false`
- `ORDERS=false`

## Next

Separate operator GO for bounded Development evaluation:
`GO_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1`

docs_token: DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
