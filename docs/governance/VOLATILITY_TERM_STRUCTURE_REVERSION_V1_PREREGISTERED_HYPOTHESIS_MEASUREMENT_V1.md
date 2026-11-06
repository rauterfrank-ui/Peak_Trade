# VOLATILITY_TERM_STRUCTURE_REVERSION_V1 — Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — no Development evaluation executed.

## Identity

- `PROGRAM_ID`: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- `STRATEGY_ID`: `VOLATILITY_TERM_STRUCTURE_REVERSION_V1`
- `HYPOTHESIS_ID`: `VOLATILITY_TERM_STRUCTURE_REVERSION_NON_BITCOIN_PERPETUALS_V1`
- `BASELINE_ID`: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- `DATASET_ID`: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- `PREDECESSOR`: `VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1` (terminal `DEVELOPMENT_FAIL` / slot consumed)

## Causal claim

When the short-horizon&#47;long-horizon realized-volatility ratio is elevated
(percentile >= 0.80 for >= 2 bars), subsequent own-instrument returns are
hypothesized to mean-revert (fade opposite the short-horizon signed return).
This is **not** VEFCF failed-continuation fade, VEPC pullback-continuation, or
VCB&#47;VCEB breakout admission.

## ENTRY_CONTRACT

Elevated RV term-structure state, then fade opposite short-horizon signed return.
No expansion&#47;compression-breakout prerequisite. Depressed-ratio entries forbidden in v1.

## EXIT_CONTRACT

Precedence: `INITIAL_STOP` → `TERM_STRUCTURE_NORMALIZATION_INVALIDATION` →
`REGIME_INVALIDATION` → `TIME_EXIT` → end-of-instrument&#47;panel. Trailing stop
forbidden. Ex-ante exit reachability required. Productive PnL evaluator reused.

## DIRECTION_CONTRACT

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_VOLATILITY_TERM_STRUCTURE_REVERSION`; Double-Play
remains sole directional transition authority.

## Gates

`DEVELOPMENT_RUN_LIMIT=1`, `DEVELOPMENT_RUN_COUNT=0`, `DEVELOPMENT_SLOT_CONSUMED=false`,
`HOLDOUT_ACCESSED=false`, `LIVE_AUTHORIZED=false`, `ORDERS=false`.

## Contract digest

`2868d009f043c6744c84487c883e9a42136bd71b188b6b8a365dbe8386a25cb4`

## Canonical Development Evaluation Entry Point (definition&#47;binding only)

- Script: `scripts&#47;research&#47;run_evaluate_volatility_term_structure_reversion_development_v1.py`
- Binding: `config&#47;research&#47;volatility_term_structure_reversion_v1_development_evaluation_entry_point_binding_v1.json`
- Unauthorized in this slice; no evaluation executed.

## Next step

Separate operator GO for strategy implementation, then separate GO for Development evaluation.

docs_token: DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_REVERSION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
