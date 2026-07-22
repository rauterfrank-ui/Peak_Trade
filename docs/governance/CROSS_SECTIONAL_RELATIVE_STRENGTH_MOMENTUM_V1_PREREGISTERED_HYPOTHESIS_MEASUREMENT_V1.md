# Cross-sectional relative-strength momentum — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract complete for
development admission thresholds and time-segment robustness; no evaluation
authorized in this slice.

## Binding

- Hypothesis: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Target phenomenon: `PERSISTENCE_OF_RELATIVE_RETURNS_ACROSS_NON_BTC_LINEAR_USDT_FUTURES`
- Program: `MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1`
- Contract: `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Digest: `1d7f855027df438629765566cb559310820ab6699b6351bddc1577b1f731c158`
- Dataset: `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` (`DEVELOPMENT_ONLY`)
- Evidence: `docs&#47;evidence&#47;preregister_cross_sectional_relative_strength_momentum_hypothesis_v1&#47;`
- Multiple-testing budget: `1`
- Authorized later development evaluation runs: `1` (not in this slice)
- Holdout: `offline_economic_reevaluation_sealed_long_panel_v1` opaque exclusion only

## Thesis

Assets with stronger relative trailing performance than the eligible non-BTC
linear USDT futures universe may continue to outperform weaker assets over a
predefined forward horizon, and a deterministic cross-sectional ranking and
selection process may generate gross edge sufficient to survive canonical fees,
slippage, and predefined cost stress.

## Directional form (frozen)

Selected: `D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION`

Rationale: matches canonical single-slot cross-sectional ranking semantics
(`single_top1_by_score_desc` &#47; `symmetric_top1_sign`; `dual_rank_forbidden=true`;
`bottom1_selection_allowed=false`). Double-Play remains sole directional
transition authority. Forms A&#47;B&#47;C rejected for incompatibility with that
infrastructure.

## Signal and selection (frozen intent)

- Score family: raw trailing log return over lookback `N` (not volatility-normalized RS v0)
- Selection: fixed-N `1` top-by-score-desc; no adaptive thresholding; no quantile in v1
- Min eligible members for rank: `5`
- Signal lag: `1` bar
- Cooldown: `no_cooldown`
- Hold: until next rebalance
- Portfolio: preserve `RESEARCH_EQUAL_WEIGHT`

## Parameter governance (development grid only)

Bounded DEVELOPMENT-ONLY grid (selection before any future run; holdout forbidden;
post-result alteration forbidden):

- `lookback_N_candidates`: `10`, `20`, `48`
- `rebalance_interval_bars_candidates`: `1`, `4`, `24`

Deterministic model-selection rule: maximize `gross_profit_factor`; ties by
higher `net_profit_factor`, then lower `abs(max_drawdown)`, then lower
`lookback_N`, then lower `rebalance_interval_bars`.

## Economic admission

Configured thresholds reuse repository-native sources where available
(e.g. `economic_validity_policy_v1`, gross PF≥1.0, cost-stress 1.5x PF≥1.0), plus
explicit operator-authorized robustness admission thresholds:

- `minimum_rebalance_observations` = `30`
  (`EXPLICIT_OPERATOR_AUTHORIZATION`; valid evaluable rebalance timestamps only;
  not trades&#47;bars&#47;instruments&#47;orders; `not_result_calibrated=true`)
- `time_segment_robustness_pass_ratio` = `0.5`
  (`EXPLICIT_OPERATOR_AUTHORIZATION`; aligned to `economic_validity_policy_v1`
  pass-ratio convention as governance binding; `not_result_calibrated=true`)

## Time-segment robustness (operator-bound)

- `TIME_SEGMENT_DEFINITION_ID=CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1`
- Development period only: `2022-06-01T03:55:17Z` .. `2023-08-16T05:55:00Z`
  (seal-registry published common panel bounds; holdout excluded; period
  adjustment forbidden)
- Exactly four chronological equal-duration quarters: `TIME_SEGMENT_Q1`..`Q4`
- Remainder bars assigned to earliest segments (≤1 extra each)
- Denominator always 4; non-evaluable segments are not PASS and are not removed
- All four segments must be evaluable; otherwise `ROBUSTNESS_SAMPLE_INSUFFICIENT`
- Segment PASS uses the same preregistered economic&#47;cost&#47;sample&#47;drawdown&#47;net-PF
  gates as full development evaluation (no segment-specific invented thresholds)
- Minimum passing segments: `2` (`0.5 * 4`)
- Illustrative evidence `CHRONOLOGICAL_60_20_20_FLOOR_HOUR` partition is **not**
  authority and is not mutated
- `generic_walk_forward_v1` is **not** bound

## Causal independence

Not a Bollinger mean-reversion&#47;midband&#47;cooldown&#47;ADX-DI&#47;regime&#47;MA&#47;MACD&#47;RSI retry
and not an unchanged `cross_sectional_relative_strength&#47;v0` binding retry.

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `HOLDOUT_AUTHORIZED=false` &#47; `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged&#47;closed
- No runtime &#47; shadow &#47; testnet &#47; live &#47; orders
- `STRATEGY_IMPLEMENTATION_PRESENT=false` on this measurement contract artifact
- `DEVELOPMENT_RUN_COUNT=0` &#47; `RUNNER_START_COUNT=0`
- Pending admission thresholds: none

## Next step

`AWAIT_SEPARATE_OPERATOR_GO_FOR_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION`

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
