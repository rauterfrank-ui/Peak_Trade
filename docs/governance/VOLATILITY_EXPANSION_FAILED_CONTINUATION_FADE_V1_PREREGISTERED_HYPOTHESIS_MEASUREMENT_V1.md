# VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1 — Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — no Development evaluation executed.

## Identity

- `PROGRAM_ID`: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- `STRATEGY_ID`: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1`
- `HYPOTHESIS_ID`: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_NON_BITCOIN_PERPETUALS_V1`
- `BASELINE_ID`: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- `DATASET_ID`: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- `PREDECESSOR`: `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1` (terminal `FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT` / `CONSUMED_NO_RETRY`)

## Causal claim

After confirmed RV expansion and a directional impulse, economic edge is hypothesized from
**failure of the continuation path** (fade opposite the impulse), not from VEPC-style
pullback-then-continuation.

## ENTRY_CONTRACT

Confirmed RV24 expansion (>=4 bars, percentile >= 0.65) + directional impulse, then within
an 8-bar monitoring window the first failed-continuation trigger wins:

1. impulse extreme break against the impulse
2. deep pullback (>=50% of impulse range) without continuation confirmation
3. qualifying pullback (>=15%) with window exhaustion without continuation confirmation

Successful VEPC-style continuation confirmation cancels fade for that sequence.
No entry on expansion confirmation bar; no immediate breakout without failure; no VEPC
continuation entry.

## EXIT_CONTRACT

Precedence: `INITIAL_STOP` → `IMPULSE_RECLAIM_INVALIDATION` → `REGIME_INVALIDATION` →
`TIME_EXIT` → end-of-instrument/panel. Trailing stop forbidden. Ex-ante exit reachability
required. Productive PnL evaluator reused (no second PnL truth).

## DIRECTION_CONTRACT

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_FAILED_CONTINUATION_FADE`; Double-Play remains sole
directional transition authority. Direction is opposite the failed impulse.

## COST_MODEL

fee 10 bps/side, slippage 5 bps/side, half-spread 5 bps; canonical multiplier 1.0;
stress [0.5, 1.0, 1.5, 2.0].

## Gates

`DEVELOPMENT_RUN_LIMIT=1`, `DEVELOPMENT_RUN_COUNT=0`, `DEVELOPMENT_SLOT_CONSUMED=false`,
`HOLDOUT_ACCESSED=false`, `LIVE_AUTHORIZED=false`, `ORDERS=false`.

## Canonical Development Evaluation Entry Point (definition/binding only)

- Script: `scripts&#47;research&#47;run_evaluate_volatility_expansion_failed_continuation_fade_development_v1.py`
- Binding: `config&#47;research&#47;volatility_expansion_failed_continuation_fade_v1_development_evaluation_entry_point_binding_v1.json`
- Unauthorized in this slice; no evaluation executed.

## Next step

Separate operator GO for strategy implementation, then separate GO for Development evaluation.

docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
