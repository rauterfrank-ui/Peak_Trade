# Canonical Advanced Search v1

Contract for Peak_Trade Phase 12 Advanced Search.

```text
SCHEMA_VERSION=canonical_advanced_search_v1
ADVANCED_SEARCH_DOMAIN=peak_trade.canonical_advanced_search.v1
ADVANCED_SEARCH_PRESENT=true
ADVANCED_SEARCH_AUTHORITY=RESEARCH_ONLY
SEARCH_IS_AUTHORITY_MECHANISM=false
SEARCH_HAS_RUNTIME_AUTHORITY=false
SEARCH_CAN_MUTATE_LIVE_CONFIG=false
SEARCH_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
SELF_LEARNING_NOT_SELF_AUTHORIZING=true
BEST_SHARPE_IS_NOT_AUTO_WINNER=true
PHASE_13_STARTED=false
```

Owner:

- `src&#47;experiments&#47;canonical_advanced_search_v1.py` — propose research candidates only

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE identity
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id
Phase 3  src.experiments.canonical_failure_memory_v1          REUSE fingerprint and duplicate assessment
Phase 4  robustness_suite_version / robustness_policy_digest  REUSE tokens
Phase 7  src.experiments.canonical_reality_gap_store_v1       REUSE gap records as signals
Phase 10 canonical_automated_offline_research_loop_v1         REUSE as request target, not executor
Phase 11 src.experiments.canonical_meta_learning_v1           REUSE research_proposals as priority signals
```

```text
Phase 5  src.experiments.canonical_comparison_ssot_v1         NOT_APPLICABLE as ranking authority
Phase 6  src.experiments.canonical_champion_challenger_v1     NOT_APPLICABLE as ranking authority
Phase 8  src.experiments.canonical_regime_aware_evaluation_v1 NOT_APPLICABLE as calculator
Phase 9  src.experiments.canonical_portfolio_learning_v1      NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1                    NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
src.live.live_gates                                           NOT_APPLICABLE
src.experiments.canonical_automated_offline_research_loop_v1  NOT_APPLICABLE as executor
```

```text
ADVANCED_SEARCH == SEARCH_MECHANISM
ADVANCED_SEARCH != AUTHORITY_MECHANISM
SEARCH_SCORE != CANONICAL_CHAMPION_CHALLENGER_RANKING
BEST_SHARPE != AUTO_WINNER
```

This layer does not invent identity, comparability, metrics, robustness, failure, or ranking truth. It proposes identity-bound research candidates. It does not start Phase 13, live, canary, funding, order submit, confirm tokens, productive config write, or autonomous promotion.

## Authority

```text
SELF_LEARNING != SELF_AUTHORIZING
ADVANCED_SEARCH_AUTHORITY=RESEARCH_ONLY
```

Search may create research candidates, hypotheses, parameter-region proposals, search evidence, and offline-experiment requests. Search may consume Phase-11 priority signals. Search must not authoritatively promote experiments, candidates, or champions.

## Supported search mechanism

This contract implements exactly one mechanism:

```text
BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH
```

The method enumerates a declared discrete search space in canonical order, applies fail-closed identity / constraint / failure-memory gates, and uses Phase-11 signals only as documented priority weights.

The following method tokens are recognized and fail closed as unsupported:

```text
BAYESIAN_OPTIMIZATION
OPTUNA
EVOLUTIONARY_SEARCH
GENETIC_ALGORITHM
ML_BASED_SEARCH
AGENTIC_HYPOTHESIS_GENERATION
REINFORCEMENT_LEARNING
```

Unknown methods fail closed. No hidden global random state is used. The bound `seed` is part of search identity even though this method is deterministic.

## Shape

A COMPLETE record evaluates one explicit search request against a Phase-1 identity template plus optional Phase-3 failure records, Phase-7 reality-gap records, and Phase-11 research proposals.

```text
SEARCH_SPACE_VALIDATION
CONSTRAINT_ENFORCEMENT
IDENTITY_BINDING
FAILURE_MEMORY_ASSESSMENT
META_LEARNING_PRIORITY_BINDING
CANDIDATE_PROPOSAL
OFFLINE_EXPERIMENT_REQUEST
SEARCH_EVIDENCE
```

Silent step omission is forbidden. Every generated candidate is represented in evidence, including rejected and deprioritized candidates.

```text
SEARCH_CAN_CREATE_RESEARCH_CANDIDATES=true
SEARCH_CAN_CREATE_HYPOTHESES=true
SEARCH_CAN_PROPOSE_PARAMETER_REGIONS=true
SEARCH_CAN_USE_META_LEARNING_SIGNALS=true
SEARCH_CAN_REQUEST_OFFLINE_EXPERIMENTS=true
```

```text
OFFLINE_EXPERIMENT_REQUEST != run Phase 10 loop
OFFLINE_EXPERIMENT_REQUEST != write config
OFFLINE_EXPERIMENT_REQUEST != execute robustness
```

## Identity binding

Every candidate must be bound with `build_canonical_experiment_identity_v1` before storage. The identity template supplies every critical binding. Search may vary only declared research-parameter axes that already exist on the template.

No implicit:

```text
fees
slippage
funding
dataset versions
split policies
risk policies
portfolio definitions
seeds
core-logic versions
```

A candidate without a COMPLETE identity is rejected fail-closed and is never proposed.

Frozen template fields must remain identical on every candidate identity:

```text
fee_model_digest
slippage_model_digest
funding_model_digest
cost_model_digest
risk_policy_digest
portfolio_digest
split_policy_digest
dataset_digest
feature_pipeline_digest
strategy_identity
seed
git_sha
trading_decision_core_digest and core-logic component digests
```

`strategy_params_digest` and `identity_digest` may change with the proposed parameters.

## Constraints and Goodhart safety

Risk, cost, data, robustness, and authority limits are constraints, not optimizer objectives.

Forbidden search axes include risk, leverage, turnover, tail risk, liquidity, fill, fee, slippage, funding, holdout, split, dataset, enable, arm, live, testnet, order, canary, confirm token, promotion, and core-logic surfaces.

```text
SEARCH_CAN_WRITE_LIVE_CONFIG=false
SEARCH_CAN_WRITE_TESTNET_CONFIG=false
SEARCH_CAN_INCREASE_RISK=false
SEARCH_CAN_INCREASE_LEVERAGE=false
SEARCH_CAN_FUND=false
SEARCH_CAN_SUBMIT_ORDER=false
SEARCH_CAN_ARM=false
SEARCH_CAN_ENABLE=false
SEARCH_CAN_CREATE_CONFIRM_TOKEN=false
SEARCH_CAN_USE_CONFIRM_TOKEN=false
SEARCH_CAN_AUTHORIZE_CANARY=false
SEARCH_CAN_PROMOTE_TO_LIVE=false
SEARCH_CAN_REPLACE_PRODUCTIVE_CHAMPION=false
SEARCH_CAN_AUTONOMOUSLY_REPLACE_CORE_LOGIC=false
```

Search priority is not canonical ranking. Incomparable or unevaluated candidates are never ranked. Robustness is not shortened. Promotion gates are not redefined.

## Failure Memory and duplicates

Before a candidate may be proposed, Phase 3 is assessed for:

```text
exact hypothesis duplicate
hypothesis fingerprint
known rejected parameter region
known failure class
known robustness failure
known reality-gap failure
```

```text
DUPLICATE_DETECTED != AUTOMATIC_RESEARCH_BAN
```

Allowed actions remain the Phase-3 set: `WARN` / `ANNOTATE` / `PRIORITIZE` / `DEPRIORITIZE` / `REQUIRE_EXPLICIT_RETEST_REASON`. Failure Memory may deprioritize or warn. It must not silently omit a candidate. A duplicate without `retest_reason` is an explicit `REJECTED_DUPLICATE_WITHOUT_RETEST` evidence row, not a proposed candidate.

## Meta-Learning binding

```text
META_LEARNING_OUTPUT_REUSE=research_proposals
SEARCH_PRIORITY_REUSE=PRIORITIZE_RESEARCH|DEPRIORITIZE_RESEARCH|INVESTIGATE|RETEST_WITH_EXPLICIT_REASON
FAILURE_SIGNAL_REUSE=Phase 3 records
ROBUSTNESS_SIGNAL_REUSE=Phase 3 REJECTED_* robustness classes
REALITY_GAP_SIGNAL_REUSE=Phase 7 records
```

Meta-Learning may change search priority. It does not create authority. Signals without a bound `meta_learning_identity` fail closed.

## Determinism

Search identity binds:

```text
search_method
search_method_version
search_space_digest
objective_definition/version
constraint_definition/version
seed
budget
parent hypothesis/reference
input evidence refs
generated candidate refs
```

Identical lineage-bound inputs yield an identical result.

## Canonical evidence fields

```text
search_identity
search_method
search_method_version
search_space
objective
constraint
seed
budget
parent_hypothesis_id
candidates
hypotheses
parameter_region_proposals
offline_experiment_requests
duplicate_assessments
search_evidence
overall_status
created_at
```

Candidate statuses:

```text
PROPOSED
BUDGET_EXCLUDED
DEPRIORITIZED_KNOWN_FAILURE
REJECTED_DUPLICATE_WITHOUT_RETEST
REJECTED_IDENTITY
REJECTED_CONSTRAINT
```

`SEARCH_COMPLETE` is not promotion, not Champion swap, and not runtime authority.

## What this layer cannot do

```text
SEARCH_IS_AUTHORITY_MECHANISM=false
SEARCH_HAS_RUNTIME_AUTHORITY=false
SEARCH_CAN_MUTATE_LIVE_CONFIG=false
SEARCH_CAN_WRITE_LIVE_CONFIG=false
SEARCH_CAN_WRITE_TESTNET_CONFIG=false
SEARCH_CAN_PROMOTE=false
AUTONOMOUS_CHAMPION_SWAP=false
AUTONOMOUS_PROMOTION=false
SEARCH_CAN_INCREASE_RISK=false
SEARCH_CAN_INCREASE_LEVERAGE=false
SEARCH_CAN_FUND=false
SEARCH_CAN_SUBMIT_ORDER=false
SEARCH_CAN_ARM=false
SEARCH_CAN_ENABLE=false
SEARCH_CAN_CREATE_CONFIRM_TOKEN=false
SEARCH_CAN_USE_CONFIRM_TOKEN=false
SEARCH_CAN_AUTHORIZE_CANARY=false
SEARCH_CAN_PROMOTE_TO_LIVE=false
SEARCH_CAN_REPLACE_PRODUCTIVE_CHAMPION=false
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC=false
HISTORICAL_RECORD_MUTATION=false
PRODUCTIVE_CONFIG_MUTATION=false
PHASE_13_STARTED=false
```

Phase 12 does not start Phase 13, live, canary, funding, order submit, confirm tokens, productive config write, or autonomous promotion.
