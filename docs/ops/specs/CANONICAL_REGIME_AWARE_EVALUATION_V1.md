# Canonical Regime-Aware Evaluation v1

Contract for Peak_Trade Phase 8 Regime-Aware Evaluation.

```text
SCHEMA_VERSION=canonical_regime_aware_evaluation_v1
REGIME_AWARE_DOMAIN=peak_trade.canonical_regime_aware_evaluation.v1
REGIME_AWARE_EVALUATION_PRESENT=true
REGIME_MAPPING_EXPLICIT=true
REGIME_LOOKAHEAD_BLOCKED=true
CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT=true
BULL_BEAR_DECISION_QUALITY_EVALUABLE=true
REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY=false
REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG=false
REGIME_AWARE_EVALUATION_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_regime_aware_evaluation_v1.py` — evaluate, map, attribute, evidence

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id
Phase 3  REJECTED_REGIME_CONCENTRATION                        REUSE token, do not re-run
Phase 4  robustness_suite_version / metric_definitions        REUSE tokens
Phase 5  comparison SSOT                                      NOT_APPLICABLE
Phase 6  champion-challenger                                  NOT_APPLICABLE
Phase 7  reality gap store                                    NOT_APPLICABLE
```

```text
src.experiments.regime_sweeps                                 NOT_APPLICABLE
src.regime.canonical_regime_meta_gated_selection_v1           NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1                     NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
```

Phase 4 remains the only robustness SSOT. This layer does not re-implement `REGIME_STRESS`, comparison ranking, champion-challenger, or reality-gap classification. Research-regime labels and runtime-regime labels are never treated as silently identical.

## Shape

Strategies are evaluated per canonical regime family, not only globally. Every COMPLETE record binds one Phase-1 experiment identity and stores explicit per-regime research measurements.

Required families:

```text
TREND_RANGE
VOLATILITY
BULL_BEAR
LIQUIDITY_STATE
SPREAD_REGIME
FUNDING_REGIME
CRASH_STATE
RISK_ON_OFF
VOLATILITY_CLUSTERING
VENUE_MICROSTRUCTURE_STATE
```

Closed labels:

```text
TREND_RANGE            trend | range
VOLATILITY             high | low
BULL_BEAR              bull | bear
RISK_ON_OFF            risk-on | risk-off
```

Other families require an explicit non-unavailable token. A missing family fails closed.

## Per-regime metrics

Every slice must include explicit finite values for:

```text
return
sharpe
drawdown
turnover
fee_drag
slippage
failure_rate
sample_size
```

Missing values fail closed. Zero is never inferred for missing `fee_drag` or `slippage`. `sample_size` must be a positive int.

## Regime mapping

Research-regime and runtime-regime must not be treated as identical by string equality.

```text
EXPLICIT_MAPPING        versioned pairwise research_label -> runtime_label rules
DOCUMENTED_SEPARATION   declared distinct taxonomies; no identity mapping
```

Silent identity is forbidden. An explicit identity mapping rule is allowed only under `EXPLICIT_MAPPING`. Every research label used in the evaluation must be covered by that contract when the mode is `EXPLICIT_MAPPING`.

## Lookahead

Regime labels and decision-stage labels used at decision time must be point-in-time:

```text
label_as_of <= decision_as_of
```

Later economic outcomes and Bull/Bear quality assessments may have `evaluation_as_of >= decision_as_of`. Future market knowledge must not leak into runtime features or historical decisions.

## Canonical core-logic attribution

Evaluation must not stop at grouping PnL by `bull` or `bear`. Every COMPLETE record attributes the canonical trading decision chain, without lookahead:

```text
MARKET_CONTEXT
BULL_BEAR_CLASSIFICATION
STATE_SWITCH
SURVIVAL
SUITABILITY
DOUBLE_PLAY
ENTRY_POSITION_EXIT
ECONOMIC_OUTCOME
```

Stages bind Phase-1 digests. Attribution classes:

```text
MISCLASSIFICATION
TIMING_ERROR
GATE_FILTER_ERROR
EXECUTION_COST_EFFECT
STRATEGY_EDGE
NOT_ATTRIBUTABLE
```

`NOT_ATTRIBUTABLE` is required when evidence cannot distinguish the effect. Invented causal claims are forbidden.

## Bull/Bear decision quality

Explicit observations make Bull/Bear quality evaluable:

```text
CORRECT
INCORRECT
TOO_EARLY
TOO_LATE
```

Quality assessment does not rewrite the historical decision.

## Canonical evidence fields

```text
experiment_id
experiment_identity
metric_definitions
robustness_suite_version
mapping_contract
regime_slices
core_logic_attribution
bull_bear_decision_quality
regime_lookahead_blocked
canonical_core_logic_attribution_present
bull_bear_decision_quality_evaluable
evidence_refs
created_at
```

## What this layer cannot do

```text
REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY=false
REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG=false
REGIME_AWARE_EVALUATION_CAN_PROMOTE=false
LEARNING_CAN_WRITE_LIVE_CONFIG=false
LEARNING_CAN_INCREASE_RISK=false
LEARNING_CAN_INCREASE_LEVERAGE=false
LEARNING_CAN_FUND=false
LEARNING_CAN_SUBMIT_ORDER=false
LEARNING_CAN_ARM=false
LEARNING_CAN_ENABLE=false
LEARNING_CAN_CREATE_CONFIRM_TOKEN=false
LEARNING_CAN_USE_CONFIRM_TOKEN=false
LEARNING_CAN_AUTHORIZE_CANARY=false
LEARNING_CAN_PROMOTE_TO_LIVE=false
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC=false
```

Phase 8 does not start Phase 9 Portfolio Learning, live, canary, funding, or order submit.
