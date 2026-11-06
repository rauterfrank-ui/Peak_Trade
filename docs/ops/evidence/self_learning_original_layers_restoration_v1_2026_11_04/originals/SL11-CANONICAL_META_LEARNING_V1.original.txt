# Canonical Meta-Learning v1

Contract for Peak_Trade Phase 11 Meta-Learning.

```text
SCHEMA_VERSION=canonical_meta_learning_v1
META_LEARNING_DOMAIN=peak_trade.canonical_meta_learning.v1
META_LEARNING_PRESENT=true
META_LEARNING_AUTHORITY=RESEARCH_ONLY
META_LEARNING_HAS_RUNTIME_AUTHORITY=false
META_LEARNING_CAN_MUTATE_LIVE_CONFIG=false
META_LEARNING_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
SELF_LEARNING_NOT_SELF_AUTHORIZING=true
```

Owner:

- `src&#47;experiments&#47;canonical_meta_learning_v1.py` — analyze existing evidence, emit research-only findings

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE identity
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id
Phase 3  src.experiments.canonical_failure_memory_v1          REUSE failure records
Phase 4  robustness_suite_version / metric_definitions        REUSE tokens
Phase 5  src.experiments.canonical_comparison_ssot_v1         REUSE comparability
Phase 7  src.experiments.canonical_reality_gap_store_v1       REUSE gap records
```

```text
Phase 6  src.experiments.canonical_champion_challenger_v1     NOT_APPLICABLE as ranking authority
Phase 8  src.experiments.canonical_regime_aware_evaluation_v1 NOT_APPLICABLE as calculator
Phase 9  src.experiments.canonical_portfolio_learning_v1      NOT_APPLICABLE
Phase 10 src.experiments.canonical_automated_offline_research_loop_v1  NOT_APPLICABLE as executor
src.meta.learning_loop.comparison_ssot_v1                    NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1.comparison_ranking_v1  NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
src.live.live_gates                                           NOT_APPLICABLE
```

This layer does not invent identity, robustness, comparability, failure, or reality-gap truth. It consumes already-versioned research evidence. It does not start Phase 12, live, canary, funding, order submit, or autonomous promotion.

## Authority

```text
SELF_LEARNING != SELF_AUTHORIZING
META_LEARNING_AUTHORITY=RESEARCH_ONLY
```

Results may prioritize research and emit research proposals. They must not authoritatively promote experiments, candidates, or champions. Ranking of research proposals is not ranking of trading candidates.

## Shape

A COMPLETE record analyzes a frozen, lineage-bound input set of experiment units plus optional Phase-3 failure records and Phase-7 reality-gap records.

Investigable questions, always represented:

```text
STRATEGY_FAMILY_OOS_SURVIVAL
PARAMETER_REGION_REPEATED_OVERFIT
SEARCH_SPACE_FALSE_POSITIVES
ROBUSTNESS_REALITY_GAP_ASSOCIATION
BACKTEST_METRIC_PREDICTIVE_ASSOCIATION
COST_MODEL_REALITY_UNDERESTIMATION
REGIME_RECURRING_FAILURE_MODES
PARAMETER_INSTABILITY
HYPOTHESIS_KIND_POOR_RESULTS
RESEARCH_PATH_INFORMATION_GAIN
```

Silent question omission is forbidden.

## Evidence rules

```text
NO_LOOKAHEAD=true
NO_INVENTED_MISSING_VALUES=true
NO_SILENT_ZERO_DEFAULT=true
CORRELATION_IS_NOT_CAUSALITY=true
SMALL_SAMPLE_IS_NOT_STRONG_PREDICTION=true
HISTORICAL_RECORD_MUTATION=false
```

Missing fee, slippage, funding, later-outcome, or robustness measurements are never inferred as `0` or `PASS`. Missing or non-comparable evidence is explicit:

```text
INSUFFICIENT_EVIDENCE
REJECTED_COMPARABILITY
INSUFFICIENT_SAMPLE
LOOKAHEAD_REJECTED
```

Claim types:

```text
NONE
DESCRIPTIVE
ASSOCIATION
```

`CAUSAL` is forbidden. Association counts must keep `causal_claim=false`. Claim strength may be `NONE` or `WEAK`. `STRONG` is forbidden.

## Comparability

Every unordered experiment pair is evaluated by Phase 5 `build_canonical_comparison_result_v1`.

```text
COMPARABLE => eligible for joint aggregation within a cohort
COMPARISON_REJECTED => excluded from that joint aggregation
```

Incomparable evidence is never jointly ranked or jointly aggregated. Version drift of bound `metric_definitions` or `robustness_suite_version` against the evaluation contract fails closed.

## Sample-size policy

An explicit versioned policy is required. Silent defaults are forbidden.

```text
min_sample_size_descriptive
min_sample_size_associative
min_recurrence_count
min_parameter_stability
```

```text
n < min_sample_size_descriptive => INSUFFICIENT_SAMPLE, claim NONE
n < min_sample_size_associative => no ASSOCIATION claim
```

## Canonical evidence fields

```text
meta_learning_identity
input_lineage
evaluation_policy
questions
research_proposals
overall_status
created_at
```

`meta_learning_identity` is a content digest of the canonical payload. Identical lineage-bound inputs yield an identical result. Input experiment ids and relevant contract &#47; metric versions are deterministically identifiable.

## What this layer cannot do

```text
META_LEARNING_HAS_RUNTIME_AUTHORITY=false
META_LEARNING_CAN_MUTATE_LIVE_CONFIG=false
META_LEARNING_CAN_PROMOTE=false
AUTONOMOUS_CHAMPION_SWAP=false
AUTONOMOUS_PROMOTION=false
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
HISTORICAL_RECORD_MUTATION=false
PRODUCTIVE_CONFIG_MUTATION=false
```

Phase 11 does not start Phase 12, live, canary, funding, order submit, confirm tokens, productive config write, or autonomous promotion.
