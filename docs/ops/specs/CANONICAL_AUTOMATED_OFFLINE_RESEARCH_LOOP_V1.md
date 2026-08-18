# Canonical Automated Offline Research Loop v1

Contract for Peak_Trade Phase 10 Automated Offline Research Loop.

```text
SCHEMA_VERSION=canonical_automated_offline_research_loop_v1
RESEARCH_LOOP_DOMAIN=peak_trade.canonical_automated_offline_research_loop.v1
AUTOMATED_OFFLINE_RESEARCH_LOOP=true
AUTOMATED_RUNTIME_AUTHORITY=false
RESEARCH_LOOP_PRESENT=true
RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY=false
RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG=false
RESEARCH_LOOP_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_automated_offline_research_loop_v1.py` — select, prepare, orchestrate, evidence

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE identity
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id and memory
Phase 3  src.experiments.canonical_failure_memory_v1          REUSE fingerprint, records, persist
Phase 4  src.experiments.canonical_robustness_suite_v1        REUSE robustness evidence
Phase 5  src.experiments.canonical_comparison_ssot_v1         REUSE comparability
Phase 6  src.experiments.canonical_champion_challenger_v1     REUSE challenger report
Phase 7  src.experiments.canonical_reality_gap_store_v1       REUSE gap report
```

```text
Phase 8  src.experiments.canonical_regime_aware_evaluation_v1 NOT_APPLICABLE as loop step
Phase 9  src.experiments.canonical_portfolio_learning_v1      NOT_APPLICABLE as loop step
src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1  NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1                    NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
src.live.live_gates                                           NOT_APPLICABLE
```

This layer does not re-implement identity, memory, robustness, comparison, champion-challenger, or reality-gap truth. It orchestrates those owners in a fixed offline sequence. It does not start Master Runbook numeric-volatility max-age enforcement, live, canary, funding, or order submit.

## Shape

A COMPLETE loop evaluates exactly one selected research hypothesis against an explicit Champion using caller-supplied offline observations.

```text
HYPOTHESIS_SELECTION
RESEARCH_HYPOTHESIS_PREPARATION
OFFLINE_EXPERIMENT_EXECUTION
CANONICAL_ROBUSTNESS_EXECUTION
COMPARABILITY_CHECK
CHALLENGER_REPORT_GENERATION
FAILURE_MEMORY_UPDATE
REALITY_GAP_REPORT_GENERATION
RESEARCH_METADATA_AGGREGATION
```

Silent step omission is forbidden. Every step is represented in evidence.

```text
OFFLINE_EXPERIMENT_EXECUTION = bind Phase-2 memory from caller-supplied observations
OFFLINE_EXPERIMENT_EXECUTION != run productive trading engine
OFFLINE_EXPERIMENT_EXECUTION != write config
```

## Hypothesis selection

Selection requires an explicit versioned policy. Silent defaults are forbidden.

```text
EXPLICIT_HYPOTHESIS_ID
```

Exactly one candidate must match `selected_hypothesis_id`. Empty candidate lists, unknown policies, and ambiguous matches fail closed. This layer does not invent a hypothesis.

Duplicate `hypothesis_fingerprint` values from Phase 3 Failure Memory are assessed. A duplicate is `WARN` / `ANNOTATE` / `DEPRIORITIZE` / `REQUIRE_EXPLICIT_RETEST_REASON`. It is never an automatic research ban. A detected duplicate without `retest_reason` fails closed.

## Offline experiment execution

Caller-supplied finite observations are required. Missing values fail closed. Zero is never inferred for missing fee, slippage, funding, or robustness observations.

`OFFLINE_EXPERIMENT_EXECUTION` binds a COMPLETE Phase-2 experiment-memory record. Historical experiment memory is not overwritten. Optional persist uses the Phase-2 append-only store.

## Comparability and challenger report

Champion versus selected Challenger is evaluated by Phase 5, then classified by Phase 6.

```text
COMPARABLE => eligible for ranking / classification / research recommendation
COMPARISON_REJECTED => REJECTED_COMPARABILITY, not ranked
```

A Challenger may be `CHALLENGER_RESEARCH_PREFERRED` without replacing the Champion. `autonomous_champion_swap=false`.

## Failure memory and reality gap

Failed robustness gates project into Phase 3 via the existing Phase-4 projector. Comparability and reality-gap rejections use the existing `REJECTED_*` tokens. Optional persist uses the Phase-3 and Phase-7 append-only stores.

Reality-gap `SHADOW` / `PAPER_EXCHANGE` / `TESTNET` / `LIVE` labels are observation-source labels only. They do not authorize those execution planes.

## Aggregate status

```text
any FAILED step => LOOP_FAILED
else LOOP_COMPLETE
```

`LOOP_COMPLETE` is not promotion, not Champion swap, and not runtime authority.

## Canonical evidence fields

```text
loop_identity
selected_hypothesis_id
selected_experiment_id
champion_experiment_id
step_results
hypothesis_selection
hypothesis_preparation
experiment_record
robustness_evidence
comparison_result
challenger_report
failure_records
duplicate_assessment
reality_gap_record
research_metadata
overall_status
created_at
```

## What this layer cannot do

```text
AUTOMATED_RUNTIME_AUTHORITY=false
RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY=false
RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG=false
RESEARCH_LOOP_CAN_PROMOTE=false
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
```

Phase 10 does not start live, canary, funding, order submit, confirm tokens, productive config write, or autonomous promotion.
