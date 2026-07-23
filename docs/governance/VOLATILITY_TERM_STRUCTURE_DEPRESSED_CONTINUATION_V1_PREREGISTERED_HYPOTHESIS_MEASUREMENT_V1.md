# VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1 — Preregistered Hypothesis Measurement

## Status

`DEFINITION_ONLY_PREREGISTERED` — no Development evaluation executed.

## Identity

- `PROGRAM_ID`: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- `STRATEGY_ID`: `VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1`
- `HYPOTHESIS_ID`: `VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- `BASELINE_ID`: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- `DATASET_ID`: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- `PREDECESSOR`: `VOLATILITY_TERM_STRUCTURE_REVERSION_V1` (terminal `DEVELOPMENT_FAIL` / slot consumed)

## Causal claim

When the short-horizon&#47;long-horizon realized-volatility ratio is depressed
(percentile <= 0.20 for >= 2 bars), subsequent own-instrument returns are
hypothesized to continue with the short-horizon signed return. This is **not**
VTSR elevated reversion fade, not VEFCF failed-continuation fade, not VEPC
pullback-continuation, and not VCB&#47;VCEB breakout admission.

## Material difference vs VTSR

- Polarity: depressed (<=0.20) vs elevated (>=0.80)
- Direction: continuation-with vs fade-opposite
- VTSR explicitly forbade depressed entries; VTDC forbids elevated entries
- Normalization exit: ratio rises above 0.45 vs falls below 0.55

## ENTRY_CONTRACT

Depressed RV term-structure state, then continuation with short-horizon signed return.
No expansion&#47;compression-breakout prerequisite. Elevated-ratio entries forbidden in v1.

## EXIT_CONTRACT

Precedence: `INITIAL_STOP` → `TERM_STRUCTURE_NORMALIZATION_INVALIDATION` →
`REGIME_INVALIDATION` → `TIME_EXIT` → end-of-instrument&#47;panel. Trailing stop
forbidden. Ex-ante exit reachability required. Productive PnL evaluator reused.

## DIRECTION_CONTRACT

`OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION`; Double-Play remains sole directional transition authority.

## Dataset binding

`pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (DEVELOPMENT_ONLY, PIT-safe OHLCV). Holdout unbound&#47;untouched.

## Fees &#47; Slippage &#47; Turnover

Canonical fee 10 bps&#47;side, slippage 5 bps&#47;side, spread half 5 bps; cost stress
multipliers 0.5&#47;1.0&#47;1.5&#47;2.0. Single entry per depressed episode; time exit 48 bars.

## Admission &#47; Failure criteria

Preregistered economic admission gates identical in structure to lane family
(net PF, cost stress, MDD, concentration, time-segment robustness, event&#47;trade
sufficiency). Fail → `FAIL_CLOSED_NO_RETRY`.

## Run limit

`DEVELOPMENT_RUN_LIMIT=1`, `DEVELOPMENT_RUN_COUNT=1`, `DEVELOPMENT_SLOT_CONSUMED=true`,
`RETRY_FORBIDDEN=true`, `HOLDOUT_RUN_LIMIT=0`.

## Holdout prohibition

`HOLDOUT_FORBIDDEN=true`, `HOLDOUT_ACCESSED=false`, sealed holdout unbound.

## Gates &#47; Safety claims

`STRATEGY_IMPLEMENTED=true`, `EVALUATION_EXECUTED=true`, `PROMOTION_AUTHORIZED=false`,
`RUNTIME_AUTHORIZED=false`, `SHADOW_AUTHORIZED=false`, `TESTNET_AUTHORIZED=false`,
`LIVE_AUTHORIZED=false`, `ORDERS=false`.

## Contract digest

`84a21655045d792afbbfd8c62b68cf2cdbf17220a9c9528fd7f2aaa7913624ca`

## Canonical Development Evaluation Entry Point (definition&#47;binding only)

- Script: `scripts&#47;research&#47;run_evaluate_volatility_term_structure_depressed_continuation_development_v1.py`
- Binding: `config&#47;research&#47;volatility_term_structure_depressed_continuation_v1_development_evaluation_entry_point_binding_v1.json`
- Status: `RUN_SLOT_CONSUMED_DEVELOPMENT_FAIL`; evidence under evaluate_volatility_term_structure_depressed_continuation_development_v1/

## Next step

`NO_RETRY_SLOT_CONSUMED_DEVELOPMENT_FAIL_REQUIRES_NEW_SEPARATE_OPERATOR_GO_FOR_NEW_HYPOTHESIS_OR_INFRASTRUCTURE_SCOPE`

## Allowed next scope

- `VOLATILITY_REGIME_POST_VTDC_DEVELOPMENT_FAIL_LANE_LIFECYCLE_OPERATOR_DECISION_V1`
- GO tokens: lifecycle DECLARE / CLOSE_LANE / CREATE_SUCCESSOR

docs_token: DOCS_TOKEN_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
