# Canonical Failure Memory v1

Contract for Peak_Trade Phase 3 Failure Memory.

```text
SCHEMA_VERSION=canonical_failure_memory_v1
FAILURE_DOMAIN=peak_trade.canonical_failure_memory.v1
FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY=false
FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG=false
FAILURE_MEMORY_CAN_PROMOTE=false
FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN=false
DUPLICATE_DETECTED_IS_NOT_AUTOMATIC_RESEARCH_BAN=true
```

Owners:

- `src&#47;experiments&#47;canonical_failure_memory_v1.py` — schema, fingerprint, duplicate assessment
- `src&#47;experiments&#47;canonical_failure_memory_store_v1.py` — append-only file persist and read

Reuse, do not replace:

- Phase 1 owner `src&#47;experiments&#47;canonical_experiment_identity_v1.py`
- Phase 2 owner `src&#47;experiments&#47;canonical_experiment_memory_v1.py` (`REJECTED_*` dispositions and `experiment_id` derivation)

## What is immutable

After a record is successfully persisted, historical failure truth cannot change:

- hypothesis_fingerprint
- experiment_identity and core-logic digests
- failure_class / failed_gate / rejection_reason
- dataset_digest, regime, parameter_region
- cost_sensitivity / instability_indicators
- evidence_refs
- created_at

## What is append-only

```text
same failure_record_id + identical canonical content => idempotent accept
same failure_record_id + divergent canonical content => FAIL_CLOSED
new failure_record_id => append
```

`failure_record_id` is a content digest of the canonical observation. It is not a timestamp identity. The logical hypothesis key is `hypothesis_fingerprint`.

A later observation of the same logical failure (different canonical content, including a different `created_at`) is a new occurrence record.

## Duplicate detection

`hypothesis_fingerprint` is derived from:

- Phase 1 `identity_digest` (dataset, cost model, trading decision core, risk, portfolio, parent lineage)
- `hypothesis_id`
- `parameter_region`
- `regime`
- `robustness_policy_digest`

Changing any of those inputs yields a different fingerprint, so a justified retest is representable.

```text
DUPLICATE_DETECTED != AUTOMATIC_RESEARCH_BAN
```

Allowed duplicate actions: `WARN`, `ANNOTATE`, `PRIORITIZE`, `DEPRIORITIZE`, `REQUIRE_EXPLICIT_RETEST_REASON`. Persist is never silently blocked solely because a duplicate exists.

## Canonical rejection reasons

Failure class and rejection reason are the Phase 2 `REJECTED_*` tokens. Unknown classes fail closed. No free-text rejection identity.

| failure_class | failed_gate |
|---|---|
| `REJECTED_DATA_QUALITY` | `DATA_QUALITY_GATE` |
| `REJECTED_REPRODUCIBILITY` | `REPRODUCIBILITY_GATE` |
| `REJECTED_OVERFIT` | `OVERFIT_GATE` |
| `REJECTED_COST_SENSITIVITY` | `COST_SENSITIVITY_GATE` |
| `REJECTED_TAIL_RISK` | `TAIL_RISK_GATE` |
| `REJECTED_REGIME_CONCENTRATION` | `REGIME_CONCENTRATION_GATE` |
| `REJECTED_COMPARABILITY` | `COMPARABILITY_GATE` |
| `REJECTED_REALITY_GAP` | `REALITY_GAP_GATE` |
| `REJECTED_POLICY` | `POLICY_GATE` |

## Experiment identity binding

Every failure record stores the complete Phase 1 Canonical Experiment Identity, including trading-decision-core digests. `dataset_digest` and `experiment_id` are identity-bound. `evidence_refs` must include the bound `EXPERIMENT_RECORD`.

## What this store cannot do

```text
FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY=false
FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG=false
FAILURE_MEMORY_CAN_PROMOTE=false
FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN=false
```

Failure Memory is historical research truth. It is not config, not promotion authority, not runtime authority, and not trading authority. It does not implement Phase 4 robustness, Phase 5 comparison, or champion-challenger logic.
