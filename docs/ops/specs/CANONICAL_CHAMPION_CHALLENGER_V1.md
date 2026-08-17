# Canonical Champion-Challenger v1

Contract for Peak_Trade Phase 6 Champion-Challenger research evaluation.

```text
SCHEMA_VERSION=canonical_champion_challenger_v1
CHAMPION_CHALLENGER_DOMAIN=peak_trade.canonical_champion_challenger.v1
CHAMPION_CHALLENGER_PRESENT=true
AUTONOMOUS_CHAMPION_SWAP=false
CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY=false
CHAMPION_CHALLENGER_CAN_MUTATE_LIVE_CONFIG=false
CHAMPION_CHALLENGER_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_champion_challenger_v1.py` — evaluate, classify, recommend, evidence

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id
Phase 3  REJECTED_COMPARABILITY                               REUSE
Phase 4  robustness_suite_version / metric_definitions        REUSE tokens
Phase 5  src.experiments.canonical_comparison_ssot_v1         REUSE comparability and ranking
```

```text
src.governance.promotion_loop.engine                         NOT_APPLICABLE
src.meta.learning_loop.comparison_ssot_v1                    NOT_APPLICABLE
src.meta.learning_loop.canary_micro_live_readiness_v1        NOT_APPLICABLE
src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1  NOT_APPLICABLE
```

Phase 5 remains the only comparability SSOT. This layer does not re-implement dataset, split, fee, slippage, funding, risk, portfolio, robustness version, metric, time-horizon, or market-universe checks.

## Shape

```text
Champion
  ├── Challenger A
  ├── Challenger B
  └── Challenger N
```

Champion and Challenger are Phase-1/2 experiment identities. Complete experiments are not copied.

## Comparability

Every Champion-Challenger pair is evaluated by Phase 5 `build_canonical_comparison_result_v1`. Ranking of the comparable subset uses Phase 5 `rank_comparable_candidates_v1`.

```text
COMPARABLE => eligible for ranking / classification / research recommendation
COMPARISON_REJECTED => REJECTED_COMPARABILITY, excluded from ranked_experiment_ids
```

Incomparable candidates are never silently ranked. `BEST_SHARPE => WINNER` is forbidden.

## Evaluation dispositions

Per comparable Challenger:

```text
CHALLENGER_RESEARCH_PREFERRED
CHALLENGER_INFERIOR
TIE_OR_INCONCLUSIVE
```

Per incomparable Challenger:

```text
REJECTED_COMPARABILITY
```

Overall research recommendation:

```text
CHALLENGER_RESEARCH_PREFERRED
CHALLENGER_INFERIOR
TIE_OR_INCONCLUSIVE
NO_CLEAR_WINNER
REJECTED_COMPARABILITY
```

A Challenger may be `CHALLENGER_RESEARCH_PREFERRED` without replacing the Champion. Output `champion_experiment_id` equals the input Champion id. `autonomous_champion_swap=false`.

## Canonical evidence fields

```text
champion_experiment_id
challenger_experiment_ids
comparison_contract_version
comparison_ssot_version
robustness_suite_version
metric_definitions
evaluation_policy_version
pair_results
challenger_results
ranked_experiment_ids
research_recommendation
champion_state
evidence_refs
created_at
```

Scores are explicit research inputs bound to `metric_definitions`. This phase does not invent a new statistical optimizer.

## What this layer cannot do

```text
AUTONOMOUS_CHAMPION_SWAP=false
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

Phase 6 does not start Phase 7 Reality Gap Store, live, canary, funding, or order submit.
