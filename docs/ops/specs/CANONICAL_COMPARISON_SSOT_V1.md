# Canonical Comparison SSOT v1

Contract for Peak_Trade Phase 5 Comparison SSOT.

```text
SCHEMA_VERSION=canonical_comparison_ssot_v1
COMPARISON_DOMAIN=peak_trade.canonical_comparison_ssot.v1
COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY=false
COMPARISON_SSOT_CAN_MUTATE_LIVE_CONFIG=false
COMPARISON_SSOT_CAN_PROMOTE=false
COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE=false
CHAMPION_CHALLENGER_IMPLEMENTED=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_comparison_ssot_v1.py` — comparability, evidence, ranking gate

Reuse, do not replace:

- Phase 1 owner `src&#47;experiments&#47;canonical_experiment_identity_v1.py`
- Phase 2 owner `src&#47;experiments&#47;canonical_experiment_memory_v1.py` (`experiment_id`)
- Phase 3 owner `src&#47;experiments&#47;canonical_failure_memory_v1.py` (`REJECTED_COMPARABILITY`)
- Phase 4 owner `src&#47;experiments&#47;canonical_robustness_suite_v1.py` (`robustness_suite_version`, `metric_definition_version` as bound evidence tokens)

Existing Package N / learning-loop comparison surfaces remain a different domain:

```text
src.meta.learning_loop.comparison_ssot_v1          NOT_APPLICABLE as experiment Comparison SSOT
src.meta.learning_loop.comparison_metric_input_v1  NOT_APPLICABLE (silent fee/slippage defaults)
src.experiments.experiment_identity_manifest_v1    NOT_APPLICABLE (incomplete historical projection)
```

Those owners are not extended, not re-interpreted, and not used as a second identity or robustness truth. Phase 5 does not implement champion-challenger.

## Canonical comparison dimensions

Every comparison evaluates exactly these dimensions, in this order:

```text
dataset_identity
split_policy
fee_model
slippage_model
funding_model
risk_policy
portfolio_constraints
robustness_suite_version
metric_definitions
time_horizon
market_universe
```

Identity-bound dimensions are taken from the Phase 1 Canonical Experiment Identity. `robustness_suite_version`, `metric_definitions`, `time_horizon`, and `market_universe` are explicit comparison inputs. They are never inferred from live config, never defaulted, and never treated as compatible when missing.

## Comparability

```text
IDENTICAL     same canonical value on both sides
COMPATIBLE    different values, but an explicit versioned compatibility contract maps the pair
MISMATCH      different values without a covering compatibility rule
MISSING       absent, empty, unknown, unavailable, implicit, or default token
```

```text
all dimensions IDENTICAL or COMPATIBLE => COMPARABLE
otherwise => COMPARISON_REJECTED
```

`COMPARABLE` is the only status that permits ranking. `COMPARISON_REJECTED` candidates must not be ranked, must not be interpreted as better/worse, and must not be fed into champion/challenger decisions.

## Fail-closed missing dimensions

The following inferences are forbidden:

```text
missing fee model => compatible
missing funding model => compatible
missing split policy => compatible
missing robustness version => compatible
unknown market universe => compatible
```

Missing or unprovable Pflicht-Dimensionen yield `MISSING` and `COMPARISON_REJECTED`.

## Compatibility contract

A compatibility contract is optional and versioned. If present, it must declare an explicit `contract_version` and zero or more pairwise rules. Identity equality does not require a contract. Cross-value compatibility does. An empty or absent contract never invents compatibility.

## Canonical evidence fields

Every comparison record binds:

```text
left_experiment_id
right_experiment_id
comparison_contract_version
compatibility_contract_version
dimension_results
overall_comparability
rejection_reasons
evidence_refs
created_at
```

`experiment_id` is the Phase 2 derivation from Phase 1 `identity_digest`. Comparison does not invent a second experiment identity.

## Ranking

Ranking is research-only and descriptive. It requires every candidate pair to be `COMPARABLE`. Any `COMPARISON_REJECTED` pair yields `RANKING_REJECTED` and an empty ranked list. Ranking is not promotion, not champion-challenger, and not live mutation.

## What this SSOT cannot do

```text
COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY=false
COMPARISON_SSOT_CAN_MUTATE_LIVE_CONFIG=false
COMPARISON_SSOT_CAN_PROMOTE=false
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

Phase 5 does not start Phase 6 champion-challenger, live, canary, funding, or order submit.
