# Canonical Experiment Memory v1

Contract for Peak_Trade Phase 2 Immutable Experiment Memory.

```text
SCHEMA_VERSION=canonical_experiment_memory_v1
MEMORY_DOMAIN=peak_trade.canonical_experiment_memory.v1
EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY=false
EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG=false
EXPERIMENT_MEMORY_CAN_PROMOTE=false
```

Owners:

- `src&#47;experiments&#47;canonical_experiment_memory_v1.py` — schema, validation, identity binding
- `src&#47;experiments&#47;canonical_experiment_memory_store_v1.py` — append-only file persist and read

Phase 1 owner `src&#47;experiments&#47;canonical_experiment_identity_v1.py` remains the Canonical Experiment Identity. This layer stores that identity in full; it does not invent a second identity.

Existing `src&#47;experiments&#47;tracking&#47;run_summary.py` and `src&#47;experiments&#47;live_session_registry.py` remain incomplete historical tracking surfaces. They are not COMPLETE experiment memory and are not imported or migrated by this contract.

## What is immutable

After a record is successfully persisted, historical truth cannot change:

- metrics
- disposition / rejection_reason
- lineage / parent_experiment
- experiment_identity and core-logic digests
- artifact refs
- created_at

## What is append-only

```text
same experiment_id + identical canonical content => idempotent accept
same experiment_id + divergent canonical content => FAIL_CLOSED
new experiment_id => append
```

Silent overwrite, upsert-with-changed-truth, and in-place mutation are forbidden. Later corrections must be a new record. `supersedes_experiment_id` is an optional typed reference only; this phase does not apply amendments.

## Conflict

A conflict is any persist attempt where `experiment_id` already exists and the canonical JSON payload differs. The store raises `ExperimentRecordConflictError` and leaves the original file unchanged.

## Experiment identity binding

`experiment_id` is derived deterministically from Phase 1 `identity_digest`. The persisted `experiment_identity` object is the complete Canonical Experiment Identity v1 record, including:

- `trading_decision_core_digest`
- `market_context_contract_digest`
- `bull_bear_logic_digest`
- `state_switch_logic_digest`
- `survival_logic_digest`
- `suitability_logic_digest`
- `double_play_logic_digest`
- `entry_position_exit_logic_digest`

`dataset_ref`, `cost_model_ref`, `risk_policy_ref`, and `portfolio_ref` must be `IDENTITY_DIGEST_BOUND` to the corresponding identity digests. Missing fee, slippage, funding, or risk bindings remain fail-closed in Phase 1 identity; this memory layer never defaults them to zero.

## Lineage

- Root: `parent_experiment=null`, `lineage.kind=ROOT`, empty ancestors
- Child: explicit `parent_experiment`, `lineage.kind=PARENT_BOUND`, ancestors starting with the parent
- Self-parent and direct cyclic ancestors are rejected
- Parent overwrite of an existing record is a conflict, not a mutation

## Artifact refs

Artifacts are reproducible pointers, not local developer paths:

- `REPO_RELATIVE` or `STORE_RELATIVE`
- POSIX relative path without `..`, empty segments, or absolute/home/drive prefixes
- sha256 digest of the artifact bytes as claimed by the caller

## Read surface

The store can `append`, `get`, `exists`, and `list_metadata`. It does not rank, compare, promote, or run failure-memory / champion-challenger logic.

## What this store cannot do

```text
EXPERIMENT_MEMORY_HAS_RUNTIME_AUTHORITY=false
EXPERIMENT_MEMORY_CAN_MUTATE_LIVE_CONFIG=false
EXPERIMENT_MEMORY_CAN_PROMOTE=false
```

Experiment Memory is historical research truth. It is not config, not promotion authority, not runtime authority, and not trading authority. Disposition values such as `SHADOW_ELIGIBLE`, `TESTNET_ELIGIBLE`, and `PROMOTION_EVIDENCE_READY` are memory labels only and do not authorize live, canary, orders, funding, risk, or leverage.
