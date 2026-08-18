# Canonical Identity-Bound Offline Observation Binding v1

Contract for Peak_Trade identity-bound offline observation binding from existing
backtest/research observation owners. This is not Self-Learning Phase 13.

```text
SCHEMA_VERSION=canonical_identity_bound_offline_observation_binding_v1
BINDING_DOMAIN=peak_trade.canonical_identity_bound_offline_observation_binding.v1
BINDING_PRESENT=true
BINDING_AUTHORITY=RESEARCH_EVIDENCE_ONLY
PROMOTION_AUTHORITY=NONE
PROMOTION_APPLY_ALLOWED=false
BOUNDED_AUTO_ALLOWED=false
NEW_RUNNER_ARCHITECTURE=false
PACKAGE_N_HASH_REINTERPRETATION_FORBIDDEN=true
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
SELF_LEARNING_NOT_SELF_AUTHORIZING=true
```

Owner:

- `src&#47;experiments&#47;canonical_identity_bound_offline_observation_binding_v1.py` — bind only

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1              REUSE COMPLETE identity
Phase 2  src.experiments.canonical_experiment_identity_v1              REUSE identity_digest
Phase 2  src.experiments.canonical_experiment_memory_v1                REUSE experiment_id and memory
Phase 2  src.experiments.canonical_experiment_memory_store_v1          REUSE append-only persist
Phase 10 OfflineExperimentObservationsV1                               REUSE caller-supplied observation shape
```

```text
src.experiments.canonical_automated_offline_research_loop_v1           NOT_APPLICABLE as executor
src.experiments.canonical_experiment_identity_to_package_n_i16_promotion_admission_v1  NOT_APPLICABLE
src.experiments.experiment_identity_manifest_v1                        NOT_APPLICABLE as COMPLETE identity
src.experiments.tracking.run_summary                                   NOT_APPLICABLE as COMPLETE identity
src.experiments.live_session_registry                                  NOT_APPLICABLE as COMPLETE identity
src.governance.promotion_loop.engine                                   NOT_APPLICABLE as apply&#47;authority
src.live.live_gates                                                    NOT_APPLICABLE
```

This layer does not invent identity, does not rewrite Phase-1 digests, does not
create a second experiment-memory truth, and does not run a research loop. It
binds observations from the existing Phase-10 caller-supplied observation owner
onto an already COMPLETE Phase-1 identity and persists through the existing
Phase-2 immutable memory owner.

## Shape

```text
PHASE_1_COMPLETE_VALIDATION
OBSERVATION_OWNER_GUARD
CLAIMED_IDENTITY_DIGEST_BIND
CLAIMED_EXPERIMENT_ID_BIND
LINEAGE_DIGEST_BIND
IDENTITY_BOUND_OBSERVATION
PHASE_2_IMMUTABLE_MEMORY_RECORD
OPTIONAL_APPEND_ONLY_PERSIST
AUTHORITY_BOUNDARY
```

```text
existing OfflineExperimentObservationsV1 owner
        ↓
Phase-1 COMPLETE canonical experiment identity required
        ↓
identity-bound observation
        ↓
Phase-2 immutable experiment memory record
```

Allowed observation owner:

```text
OFFLINE_EXPERIMENT_OBSERVATIONS_V1
```

That token is the Phase-10 caller-supplied observation interface already consumed
by Phase-2 memory (`metrics`, `robustness_results`, `regime_results`, `artifacts`).
Unknown owners and historical incomplete surfaces fail closed.

## Fail closed

Any of the following yields a typed `REJECTED_*` result, never `BOUND`:

```text
missing Phase-1 identity
non-COMPLETE Phase-1 identity
identity digest mismatch
experiment_id mismatch
lineage &#47; digest mismatch
observation bound to a non-allowed owner
divergent duplicate persist (Phase-2 conflict)
requested apply
requested bounded_auto
legacy &#47; Package-N claimed as Phase-1 COMPLETE
identity or experiment_id reinterpretation required
```

Identity IDs and digests are never reconstructed or silently replaced. Package N
remains an incomplete historical projection. Completeness of a bound observation
does not make Package N or `RunSummary` COMPLETE.

Divergent duplicate persist reuses Phase-2 `ExperimentRecordConflictError`
semantics: same `experiment_id` plus divergent canonical content is fail-closed.
Identical canonical replay remains idempotent.

## Authority

```text
PROMOTION_AUTHORITY=NONE
PROMOTION_APPLY_ALLOWED=false
BOUNDED_AUTO_ALLOWED=false
BOUND != PROMOTED
BOUND != LIVE
BOUND != PHASE_10_RUNTIME
```

`BOUND` means only that a Phase-1 COMPLETE identity and an allowed observation
owner produced a Phase-2 memory record. It does not write live overrides, arm,
fund, submit orders, swap a Champion, authorize canary, or grant Phase 10
runtime authority.

## Non-effects

```text
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
ORDER_EFFECT=false
ACCOUNT_MUTATION_EFFECT=false
MULTI_FUTURE_AUTH_EFFECT=false
FUNDING_AUTH_EFFECT=false
PROMOTION_APPLY_EFFECT=false
BOUNDED_AUTO_EFFECT=false
RUNTIME_AUTHORITY_EFFECT=false
NEW_RUNNER_ARCHITECTURE=false
I82_FULL_MIGRATION=false
MD5_REMOVAL=false
IDENTITY_BACKFILL=false
G14_PRODUCTIVE_AUTHORITY=false
```
