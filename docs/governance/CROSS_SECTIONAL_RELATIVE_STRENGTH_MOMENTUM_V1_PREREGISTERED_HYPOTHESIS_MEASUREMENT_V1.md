# Cross-sectional relative-strength momentum — preregistered hypothesis and measurement v1

## Status

`DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract frozen;
no strategy implementation; no evaluation.

## Binding

- Hypothesis: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1`
- Signal family: `CROSS_SECTIONAL_MOMENTUM`
- Target phenomenon: `PERSISTENCE_OF_RELATIVE_RETURNS_ACROSS_NON_BTC_LINEAR_USDT_FUTURES`
- Program: `MATERIAL_DIFFERENT_CROSS_SECTIONAL_MOMENTUM_PROGRAM_V1`
- Contract: `config&#47;research&#47;cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Digest: `2a2c0133c6f488b3aa5b14d9c85f7008b7711ad60f1d87e544330cec4c583869`
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
(e.g. `economic_validity_policy_v1`, gross PF≥1.0, cost-stress 1.5x PF≥1.0).

Pending (evaluation blocked until operator resolves):

- `minimum_rebalance_observations` → `REQUIRED_BUT_THRESHOLD_PENDING_OPERATOR_GOVERNANCE`
- `time_segment_robustness_pass_ratio` → `REQUIRED_BUT_THRESHOLD_PENDING_OPERATOR_GOVERNANCE`

## Causal independence

Not a Bollinger mean-reversion&#47;midband&#47;cooldown&#47;ADX-DI&#47;regime&#47;MA&#47;MACD&#47;RSI retry
and not an unchanged `cross_sectional_relative_strength&#47;v0` binding retry.

## Gates

- `EVALUATION_AUTHORIZED=false`
- `DEVELOPMENT_EVALUATION_AUTHORIZED=false`
- `HOLDOUT_AUTHORIZED=false` / `HOLDOUT_FORBIDDEN=true`
- `PROMOTION_ELIGIBLE=false`
- Economic offline gate unchanged&#47;closed
- No runtime &#47; shadow &#47; testnet &#47; live &#47; orders
- `STRATEGY_IMPLEMENTATION_PRESENT=false`
- `DEVELOPMENT_RUN_COUNT=0` / `RUNNER_START_COUNT=0`

## Next step

Review and merge this definition-only PR before any strategy implementation or
development evaluation. Separate operator GO required for implementation, then
for evaluation; pending thresholds must be resolved before evaluation.

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
