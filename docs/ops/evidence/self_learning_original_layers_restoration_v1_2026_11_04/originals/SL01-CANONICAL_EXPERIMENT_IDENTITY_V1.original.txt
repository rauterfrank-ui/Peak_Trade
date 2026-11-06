# Canonical Experiment Identity v1

Contract for Peak_Trade Phase 1 Canonical Experiment Identity.

```text
SCHEMA_VERSION=canonical_experiment_identity_v1
IDENTITY_DOMAIN=peak_trade.canonical_experiment_identity.v1
EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=false
```

Owner: `src&#47;experiments&#47;canonical_experiment_identity_v1.py`

Package N `src&#47;experiments&#47;experiment_identity_manifest_v1.py` remains an incomplete historical projection. This contract does not reinterpret existing Package N identity hashes.

## Canonicalization

- Mappings are key-sorted before hashing.
- Sets and frozensets are sorted; lists keep caller order.
- Digest envelopes bind `schema_version`, `digest_domain`, and `digest_algorithm`.
- Dictionary insertion order and local path walk order are not identity inputs.

## Critical inputs

A `COMPLETE` identity requires explicit bindings for:

- `git_sha` plus `working_tree_status=CLEAN`
- `strategy_identity`
- `strategy_params` (stored only as `strategy_params_digest`)
- `dataset_digest`
- `feature_pipeline_digest`
- `fee_model_digest`, `slippage_model_digest`, `funding_model_digest`
- `risk_policy_digest`
- `portfolio_digest`
- `split_policy_digest`
- `seed` as an explicit int
- reproducibility environment (`python_version`, `python_implementation`)
- canonical trading decision core:
  - `market_context_contract_digest`
  - `bull_bear_logic_digest`
  - `state_switch_logic_digest`
  - `survival_logic_digest`
  - `suitability_logic_digest`
  - `double_play_logic_digest`
  - `entry_position_exit_logic_digest`

`cost_model_digest` is derived from the three cost component digests. `trading_decision_core_digest` is derived from the seven core-logic component digests. No silent fee, slippage, funding, dataset, risk, split, seed, or core-logic defaults.

If a required research input is not yet canonically representable, callers must not invent a value. Missing or `UNKNOWN`/`UNAVAILABLE` inputs fail closed and never yield `COMPLETE`.

## Fail-closed behavior

Missing critical digest, missing seed, dirty tree, secret keys, non-finite floats, or extra host-identifying environment keys raise `CanonicalExperimentIdentityError`. Incomplete records are not emitted.

## Dirty-tree behavior

`inspect_code_provenance_v1` records `HEAD` plus porcelain path status. A dirty tree cannot produce `COMPLETE` identity and cannot be treated as the same clean `git_sha` state.

## Secret handling

Known credential field names (`api_key`, `token`, `password`, `confirm_token`, and related) are rejected before serialization and are never logged as values.

## `parent_lineage_ref`

- Root experiment: `kind=ROOT` and `parent_lineage_ref=null`.
- Child experiment: `kind=PARENT_BOUND` and an explicit parent reference.
- Root and parent-bound records are deterministically distinct.

## Authority

```text
EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=false
```

Identity is research metadata and evidence only. It does not write live-override runtime configuration, enable, arm, fund, submit orders, mint or use confirm tokens, authorize canary, or promote to live.

Binding the canonical trading decision core does not grant Learning the right to mutate or replace productive trading logic.

```text
LEARNING_MAY_RESEARCH_CORE_LOGIC_CHANGES=true
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC=false
SELF_LEARNING_MUST_LEARN_FROM_CANONICAL_TRADING_DECISION_PATH=true
CANONICAL_TRADING_DECISION_CORE_BOUND=true
```
