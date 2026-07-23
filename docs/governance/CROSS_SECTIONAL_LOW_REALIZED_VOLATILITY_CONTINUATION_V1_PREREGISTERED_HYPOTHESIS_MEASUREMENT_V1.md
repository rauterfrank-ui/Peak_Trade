# CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1 — Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — no Development evaluation executed.

## Identity

- `PROGRAM_ID`: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- `STRATEGY_ID`: `CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1`
- `HYPOTHESIS_ID`: `CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- `BASELINE_ID`: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- `DATASET_ID`: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- `PREDECESSOR`: `CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1` (terminal `DEVELOPMENT_FAIL` / slot consumed)

## Causal claim

When an instrument's trailing realized-volatility level ranks in the bottom
cross-sectional quintile (CS-RV-rank <= 0.20 for >= 2 bars) on the PIT OKX
USDT perpetual panel (BTC&#47;spot excluded), subsequent own-instrument returns are
hypothesized to continue with the short-horizon signed return. This is **not**
CSHRVF high-half fade, not VTDC&#47;VTSR term-structure, not expansion&#47;compression&#47;
decay&#47;pullback&#47;failed-continuation families, and not a reopen of the closed
cross-sectional momentum (return-ranking) lane.

## Why this successor (vs rejected alternatives)

- CSHRVF parameter retune &#47; high-half retry: rejected — single DEVELOPMENT slot consumed; retry forbidden.
- Further term-structure variant: rejected — both VTSR and VTDC halves failed economically.
- Expansion&#47;compression retry: rejected — VCB&#47;VEP&#47;VDB&#47;VDBX&#47;VCEB&#47;VEPC&#47;VEFCF already terminal.
- Own-instrument RV regime transition: rejected — overlaps exhausted temporal vol machines.
- Cross-sectional vol dispersion only &#47; standaside filter: rejected — not a falsifiable trade hypothesis under Double-Play in this create.
- CLOSE_LANE: not applied — operator GO selected CREATE_SUCCESSOR with a defensible unused CS-RV low half.
- CS momentum return-ranking reopen: forbidden — sibling lane `PROGRAM_CLOSED_NO_FURTHER_RESEARCH`.

## Material difference vs CSHRVF

- Rank half: CS-RV-rank <= 0.20 vs >= 0.80
- Direction: continuation-with vs fade-opposite
- Forbidden half: high CS-vol entries vs low CS-vol entries
- Normalization exit: CS-RV-rank rises above 0.45 vs falls below 0.55

## ENTRY_CONTRACT

Cross-sectional low RV-rank state (<=0.20 for >=2 bars), then continue with short-horizon
signed return. No expansion&#47;compression&#47;term-structure prerequisite. High CS-vol-rank entries
forbidden in v1. Futures-only OKX USDT perpetuals; BTC and spot excluded.

## EXIT_CONTRACT

Precedence: `INITIAL_STOP` → `CROSS_SECTIONAL_VOL_RANK_NORMALIZATION_INVALIDATION` →
`REGIME_INVALIDATION` → `TIME_EXIT` → end-of-instrument&#47;panel. Trailing stop
forbidden. Ex-ante exit reachability required. Productive PnL evaluator reused.

## DIRECTION_CONTRACT

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION`; Double-Play remains sole directional transition authority.

## Dataset binding

`pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (DEVELOPMENT_ONLY, PIT-safe OHLCV). Binding only — no panel load in this slice. Holdout unbound&#47;untouched.

## Fees &#47; Slippage &#47; Turnover

Canonical fee 10 bps&#47;side, slippage 5 bps&#47;side, spread half 5 bps; cost stress
multipliers 0.5&#47;1.0&#47;1.5&#47;2.0. Single entry per low-vol episode; time exit 48 bars.

## Bias &#47; leakage controls

Lookahead forbidden; completed bars only; signal lag 1; same-timestamp PIT cross-section only;
no holdout access; no post-hoc universe filter; thresholds frozen ex ante; development run limit 1;
retry after fail forbidden.

## Admission &#47; Failure criteria

Preregistered economic admission gates identical in structure to lane family
(net PF, cost stress, MDD, concentration, time-segment robustness, event&#47;trade
sufficiency). Fail → `FAIL_CLOSED_NO_RETRY`.

## Run limit

`DEVELOPMENT_RUN_LIMIT=1`, `DEVELOPMENT_RUN_COUNT=0`, `DEVELOPMENT_SLOT_CONSUMED=false`,
`RETRY_FORBIDDEN=true`, `HOLDOUT_RUN_LIMIT=0`.

## Holdout prohibition

`HOLDOUT_FORBIDDEN=true`, `HOLDOUT_ACCESSED=false`, sealed holdout unbound.

## Gates &#47; Safety claims

`STRATEGY_IMPLEMENTED=false`, `EVALUATION_EXECUTED=false`, `PROMOTION_AUTHORIZED=false`,
`RUNTIME_AUTHORIZED=false`, `SHADOW_AUTHORIZED=false`, `TESTNET_AUTHORIZED=false`,
`LIVE_AUTHORIZED=false`, `ORDERS=false`.

## Contract digest

`c0b116530a1bd9dd11bd9004d76c3fbfa74036348b3f6949483f6b0890b86872`

## Canonical Development Evaluation Entry Point (definition&#47;binding only)

- Script: `scripts&#47;research&#47;run_evaluate_cross_sectional_low_realized_volatility_continuation_development_v1.py`
- Binding: `config&#47;research&#47;cross_sectional_low_realized_volatility_continuation_v1_development_evaluation_entry_point_binding_v1.json`
- Unauthorized in this slice; no evaluation executed.

## Next step

Separate operator GO for strategy implementation, then separate GO for Development evaluation.

## Allowed next scope

- `CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`
- GO token: `GO_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_STRATEGY_IMPLEMENTATION_ONLY_V1`

docs_token: DOCS_TOKEN_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
