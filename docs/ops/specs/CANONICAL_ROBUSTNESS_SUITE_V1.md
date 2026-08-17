# Canonical Robustness Suite v1

Contract for Peak_Trade Phase 4 Canonical Robustness Suite.

```text
SCHEMA_VERSION=canonical_robustness_suite_v1
ROBUSTNESS_DOMAIN=peak_trade.canonical_robustness_suite.v1
ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY=false
ROBUSTNESS_SUITE_CAN_MUTATE_LIVE_CONFIG=false
ROBUSTNESS_SUITE_CAN_PROMOTE=false
SINGLE_METRIC_PROMOTION=false
PROMOTION_AUTHORITY=NONE
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owner:

- `src&#47;experiments&#47;canonical_robustness_suite_v1.py` — catalog, evaluation, evidence identity

Reuse, do not replace:

- Phase 1 owner `src&#47;experiments&#47;canonical_experiment_identity_v1.py`
- Phase 2 owner `src&#47;experiments&#47;canonical_experiment_memory_v1.py` (`experiment_id`, `REJECTED_*`)
- Phase 3 owner `src&#47;experiments&#47;canonical_failure_memory_v1.py`
- Monte Carlo / block bootstrap `src&#47;experiments&#47;monte_carlo.py`
- Crash scenarios `src&#47;experiments&#47;stress_tests.py`
- Cost / funding model refs `src&#47;backtest&#47;cost_config_v0.py`, `src&#47;backtest&#47;funding_model_v1.py`

Existing walk-forward and parameter-sensitivity **runners** are not imported. They pull trading/config surfaces that this research contract must not touch. The suite adapts their observation contracts instead of re-running the engines.

## Canonical evidence fields

Every COMPLETE record binds:

```text
robustness_suite_version
experiment_id
experiment_identity
candidate_ref
dataset_ref / dataset_digest
split_policy_ref
cost_model_ref
risk_policy_ref
seed / deterministic randomness contract
metric_definition_version
test_results
aggregate_status
failed_gates
evidence_refs
created_at
```

No silent fee, slippage, funding, split, seed, or core-logic defaults. Critical refs are `IDENTITY_DIGEST_BOUND` to Phase 1 digests.

## Catalog

Required robustness tests are always represented. If a test cannot be executed with bound infrastructure or provided observations, the status is explicit:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
NOT_EVALUATED
BLOCKED_MISSING_CAPABILITY
```

`PASS` is never inferred from a missing result.

Required tests:

- train / validation / holdout
- walk-forward
- rolling OOS
- purged split
- embargo
- Monte Carlo
- block bootstrap
- parameter sensitivity
- fee / slippage / funding / latency / spread / liquidity stress
- crash scenarios
- missing-data / bad-tick / regime / risk stress
- multiple-testing controls
- single-metric promotion guard

Advanced statistical controls are catalogued and deferred unless a methodically correct owner exists:

```text
DEFLATED_SHARPE_RATIO
PROBABILISTIC_SHARPE_RATIO
PROBABILITY_OF_BACKTEST_OVERFITTING
CPCV
WHITE_REALITY_CHECK
SPA_TEST
```

These remain `BLOCKED_MISSING_CAPABILITY` with an explicit reason. Placeholder functions are forbidden.

## Aggregate status

```text
any FAIL => FAIL
required test not PASS => BLOCKED
required evidence dimension not COMPUTED => BLOCKED
else PASS
```

Missing Pflicht-Evidence is `BLOCKED`, never a silent PASS.

## Single-metric promotion

```text
BEST_SHARPE => PROMOTE
```

is forbidden. The suite emits `ROBUSTNESS_EVIDENCE` only. It does not implement promotion authority, live mutation, or config mutation.

## Failure Memory

Failed required gates can be projected into Phase 3 Failure Memory using existing `REJECTED_*` tokens. Historical experiment and failure records are not overwritten. Append-only / immutable semantics stay with Phase 2 and Phase 3 stores.

## What this suite cannot do

```text
ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY=false
ROBUSTNESS_SUITE_CAN_MUTATE_LIVE_CONFIG=false
ROBUSTNESS_SUITE_CAN_PROMOTE=false
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

Phase 4 does not start Phase 5 Comparison SSOT, champion-challenger, live, canary, funding, or order submit.
