# Canonical Reality Gap Store v1

Contract for Peak_Trade Phase 7 Reality Gap Store.

```text
SCHEMA_VERSION=canonical_reality_gap_store_v1
REALITY_GAP_DOMAIN=peak_trade.canonical_reality_gap_store.v1
REALITY_GAP_STORE_PRESENT=true
REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY=false
REALITY_GAP_CAN_MUTATE_LIVE_CONFIG=false
REALITY_GAP_CAN_PROMOTE=false
PROMOTION_AUTHORITY=NONE
OBSERVED_SURFACE_IS_NOT_AUTHORIZATION=true
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION=true
```

Owners:

- `src&#47;experiments&#47;canonical_reality_gap_store_v1.py` — schema, gap evaluation, evidence
- `src&#47;experiments&#47;canonical_reality_gap_store_persist_v1.py` — append-only file persist and read

Reuse, do not replace:

```text
Phase 1  src.experiments.canonical_experiment_identity_v1     REUSE
Phase 2  src.experiments.canonical_experiment_memory_v1       REUSE experiment_id and REJECTED_REALITY_GAP
Phase 3  src.experiments.canonical_failure_memory_v1          REUSE REALITY_GAP_GATE mapping
Phase 4  metric_definitions                                   REUSE token
Phase 5  comparison SSOT                                      NOT_APPLICABLE
Phase 6  champion-challenger                                  NOT_APPLICABLE
```

```text
src.meta.learning_loop.runtime_observation_feedback_v1        NOT_APPLICABLE
src.governance.promotion_loop.engine                          NOT_APPLICABLE
src.experiments.live_session_registry                         NOT_APPLICABLE
```

Phase 3 remains the only Failure Memory SSOT. This layer may classify a gap as `REJECTED_REALITY_GAP`; it does not append failure-memory records and does not invent a second identity, comparability, robustness, or comparison truth.

## Shape

A Reality Gap record binds one COMPLETE Phase-1 experiment identity to explicit expected-versus-observed research measurements. Observations are caller-supplied numbers. This store does not query venues, start sessions, or submit orders.

```text
expected_surface = RESEARCH
observed_surface in {SHADOW, PAPER_EXCHANGE, TESTNET, LIVE}
observed_surface_is_not_authorization = true
```

`SHADOW`, `PAPER_EXCHANGE`, `TESTNET`, and `LIVE` are observation-source labels only. They do not authorize those execution planes.

## Canonical gap dimensions

Every supplied dimension must include explicit finite `expected`, `observed`, and non-negative `threshold` values. Missing values fail closed. Zero is never inferred for missing fee, slippage, funding, fill, latency, spread, or pnl.

| dimension | identity binding |
|---|---|
| `fee` | `fee_model_digest` |
| `slippage` | `slippage_model_digest` |
| `funding` | `funding_model_digest` |
| `fill` | none; explicit measurement only |
| `latency` | none; explicit measurement only |
| `spread` | none; explicit measurement only |
| `pnl` | none; explicit measurement only |

Cost dimensions must match the bound Phase-1 digest. At least one dimension is required.

```text
abs(observed - expected) <= threshold  => WITHIN_THRESHOLD
abs(observed - expected) >  threshold  => EXCEEDS_THRESHOLD
```

## Overall disposition

```text
any EXCEEDS_THRESHOLD => REJECTED_REALITY_GAP / REALITY_GAP_GATE
all WITHIN_THRESHOLD  => WITHIN_THRESHOLD / NOT_TRIGGERED
```

`REJECTED_REALITY_GAP` and `REALITY_GAP_GATE` are the Phase-2/3 tokens. Classification here is research evidence only.

## Canonical evidence fields

```text
experiment_id
experiment_identity
expected_surface
observed_surface
metric_definitions
threshold_policy_digest
gap_dimensions
dimension_results
overall_disposition
failed_gate
evidence_refs
created_at
```

## What is append-only

```text
same reality_gap_record_id + identical canonical content => idempotent accept
same reality_gap_record_id + divergent canonical content => FAIL_CLOSED
new reality_gap_record_id => append
```

`reality_gap_record_id` is a content digest of the canonical observation. It is not a timestamp identity.

## What this store cannot do

```text
REALITY_GAP_STORE_HAS_RUNTIME_AUTHORITY=false
REALITY_GAP_CAN_MUTATE_LIVE_CONFIG=false
REALITY_GAP_CAN_PROMOTE=false
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
OBSERVED_SURFACE_IS_NOT_AUTHORIZATION=true
```

Phase 7 does not start Phase 8 Regime-Aware Evaluation, live, canary, funding, or order submit.
