# Canonical Portfolio Learning v1

Contract for Peak_Trade Phase 9 Portfolio Learning.

```text
SCHEMA_VERSION=canonical_portfolio_learning_v1
PORTFOLIO_LEARNING_DOMAIN=peak_trade.canonical_portfolio_learning.v1
PORTFOLIO_LEARNING_PRESENT=true
STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED=true
STRONG_SINGLE_STRATEGY_IS_NOT_AUTOMATIC_PORTFOLIO_COMPONENT=true
AUTONOMOUS_ALLOCATION_APPLY=false
AUTONOMOUS_PORTFOLIO_PROMOTION=false
PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY=false
PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG=false
PORTFOLIO_LEARNING_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_portfolio_learning_v1.py` — evaluate, separate layers, evidence

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id
Phase 3  REJECTED_COMPARABILITY                               REUSE token
Phase 4  robustness_suite_version / metric_definitions        REUSE tokens
Phase 5  src.experiments.canonical_comparison_ssot_v1         REUSE comparability
Phase 6  champion-challenger                                  NOT_APPLICABLE
Phase 7  reality gap store                                    NOT_APPLICABLE
Phase 8  regime-aware evaluation                              NOT_APPLICABLE as calculator
```

```text
src.experiments.portfolio_robustness                          NOT_APPLICABLE
src.experiments.portfolio_presets                             NOT_APPLICABLE
src.experiments.portfolio_recipes                             NOT_APPLICABLE
src.risk.component_var                                        NOT_APPLICABLE
src.live.live_gates                                           NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1                     NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
```

Phase 5 remains the only comparability SSOT. This layer does not re-implement dataset, fee, slippage, funding, risk, or portfolio-constraint checks, does not rank members by isolated strategy score, and does not apply allocations.

## Shape

Strategy Learning and Portfolio Learning are separate layers. A COMPLETE record evaluates one research portfolio of at least two Phase-1-bound members.

```text
STRATEGY_LAYER
  signal quality
  execution robustness
  parameter stability
  regime suitability

PORTFOLIO_LAYER
  correlation
  covariance
  diversification
  concentration
  marginal risk
  risk contribution
  portfolio drawdown
  turnover
  capacity
  allocation stability
```

```text
STRONG_SINGLE_STRATEGY != AUTOMATIC_GOOD_PORTFOLIO_COMPONENT
```

Strategy-layer observations are stored as strategy evidence only. They never become `PORTFOLIO_COMPONENT_ELIGIBLE` by themselves.

## Comparability

Every unordered member pair is evaluated by Phase 5 `build_canonical_comparison_result_v1`.

```text
any COMPARISON_REJECTED => REJECTED_COMPARABILITY
all COMPARABLE          => portfolio gates may be evaluated
```

Incomparable members are never ranked together and never treated as a valid portfolio.

## Explicit measurements

Caller-supplied finite values are required. Missing values fail closed. Zero is never inferred for missing `fee_drag`, `slippage`, `correlation`, or `covariance`.

Required portfolio-level measurements:

```text
diversification
concentration
portfolio_drawdown
turnover
capacity
allocation_stability
```

Required per member:

```text
weight
marginal_risk
risk_contribution
fee_drag
slippage
strategy_layer observations
```

Required per unordered pair:

```text
correlation
covariance
```

`weight` values must be positive and sum to one. Input order is canonically sorted by `experiment_id` and does not change identity.

## Policy

An explicit versioned policy is required. Silent defaults are forbidden.

```text
max_pairwise_abs_correlation
max_concentration
min_diversification
max_abs_portfolio_drawdown
max_turnover
min_capacity
min_allocation_stability
max_risk_contribution
```

A portfolio is `PORTFOLIO_ELIGIBLE` only when every member pair is `COMPARABLE` and every portfolio gate is within policy. Otherwise `PORTFOLIO_INELIGIBLE` or `REJECTED_COMPARABILITY`.

## Canonical evidence fields

```text
member_experiment_ids
member_results
strategy_layer_observations
pairwise_results
portfolio_metrics
evaluation_policy
overall_disposition
strategy_and_portfolio_optimization_separated
portfolio_learning_present
applied_allocation
evidence_refs
created_at
```

## What this layer cannot do

```text
PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY=false
PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG=false
PORTFOLIO_LEARNING_CAN_PROMOTE=false
AUTONOMOUS_ALLOCATION_APPLY=false
AUTONOMOUS_PORTFOLIO_PROMOTION=false
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

Phase 9 does not start Phase 10 Automated Offline Research Loop, live, canary, funding, or order submit.
