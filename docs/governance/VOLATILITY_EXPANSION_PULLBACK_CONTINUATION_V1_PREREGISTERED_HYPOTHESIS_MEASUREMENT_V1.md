# VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1 — Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — no Development evaluation executed.

## Identity

- `PROGRAM_ID`: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- `STRATEGY_ID`: `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1`
- `HYPOTHESIS_ID`: `VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- `BASELINE_ID`: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- `DATASET_ID`: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- `PREDECESSOR`: `VOLATILITY_CONTRACTION_EXPANSION_BREAKOUT_V1` (terminal `FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT`)

## ENTRY_CONTRACT

Confirmed RV24 expansion (>=4 bars, percentile >= 0.65) + directional impulse, then bounded pullback (15%–50% of impulse range within <=8 bars), then continuation resume. No entry on expansion confirmation bar; no immediate breakout without pullback.

## EXIT_CONTRACT

Precedence: `INITIAL_STOP` → `PULLBACK_STRUCTURE_INVALIDATION` → `REGIME_INVALIDATION` → `TIME_EXIT` → end-of-instrument/panel. Trailing stop forbidden. Ex-ante exit reachability required. Productive PnL evaluator reused (no second PnL truth).

## DIRECTION_CONTRACT

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_PULLBACK_CONTINUATION`; Double-Play remains sole directional transition authority.

## COST_MODEL

fee 10 bps/side, slippage 5 bps/side, half-spread 5 bps; canonical multiplier 1.0; stress [0.5, 1.0, 1.5, 2.0].

## Gates

`DEVELOPMENT_RUN_LIMIT=1`, `DEVELOPMENT_RUN_COUNT=0`, `DEVELOPMENT_SLOT_CONSUMED=false`, `HOLDOUT_ACCESSED=false`, `LIVE_AUTHORIZED=false`, `ORDERS=false`.

## Canonical Development Evaluation Entry Point (definition/binding only)

- Script: `scripts/research/run_evaluate_volatility_expansion_pullback_continuation_development_v1.py`
- Binding: `config/research/volatility_expansion_pullback_continuation_v1_development_evaluation_entry_point_binding_v1.json`
- Unauthorized in this slice; no evaluation executed.

## Next step

Separate operator GO for strategy implementation, then separate GO for Development evaluation.

docs_token: VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
