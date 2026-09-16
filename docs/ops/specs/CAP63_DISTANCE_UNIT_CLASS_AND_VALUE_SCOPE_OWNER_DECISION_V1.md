---
title: "Cap 6.3 Distance Unit Class And Value Scope Owner Decision v1"
status: "OWNER_DECISION_PERSISTED_DOCS_ONLY"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1"
---

# Cap 6.3 Distance Unit Class And Value Scope Owner Decision v1

Canonical persist of the Owner answers captured under
`OWNER_GO_BOUNDED_CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_DECISION_CAPTURE_V1`
and persisted by
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_INTENT_DECISION_PERSIST_DOCS_ONLY_V1`.

Semantic authority for these five fields lives in Master Runbook §9.2.1.
This file is the decision record and navigation twin. It is **not** a second
numeric owner and **not** a runtime bind.

```text
DOCUMENT_CLASS=OWNER_DECISION_RECORD_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_INTENT_DECISION_PERSIST_DOCS_ONLY_V1
OWNER_GO_STATUS=CONSUMED
CAPTURE_GO=OWNER_GO_BOUNDED_CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_DECISION_CAPTURE_V1
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
DECISION_KIND=TARGET_AUTHORITY_FOR_FUTURE_DISTANCE_SEMANTICS
NOT_A_CLAIM_ABOUT_HISTORICAL_UNIT_SEMANTICS=true
EXPECTED_ORIGIN_MAIN=c78e2fc06595e283e9de239ec04af28a7676674f
FORENSIC_EVIDENCE_BOUND_SHA=975ac8d67c98810f888c0322f1ab2f642c9c55bd
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Owner fields persisted verbatim

```text
CAP63_UNIT_CLASS=DYNAMICALLY_DERIVED
CAP63_VALUE_SCOPE=DYNAMICALLY_DERIVED
CAP63_CROSS_INSTRUMENT_VALIDITY=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CAP63_NORMALIZATION_JOIN_REQUIRED=REPLACED_BY_DYNAMIC_DERIVATION
MIN_SCOPE_BAND_IN_SCOPE=NO_KEEP_SEPARATE_OWNER
```

## Current productive baseline (unchanged by this persist)

```text
MODEL_B_STATUS=PRESERVE_AS_CURRENT_BASELINE
MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
MODEL_C_BOUND=false
FREEZE_EXCEPTION_AUTHORIZED=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
min_scope_band=50.0
MIN_SCOPE_BAND_OWNER=NOT_CAP63
CAP63_NUMERIC_VALUES_REINTERPRETED_AS_DYNAMICALLY_DERIVED=false
DERIVED_DISTANCE_FORMULA_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
MAX_POSITIONS=1
```

This persist does **not** change Cap 6.3 TOML values. Frozen `200.0` /
`80.0` / `120.0` remain the CURRENT productive generator numeric inputs under
MODEL_B. They are **not** retroactively declared dynamically-derived.

`min_scope_band=50.0` remains a separate owner (`_default_policies` Scope-Init
policy literal) and is outside this decision.

MODEL_C remains an unbound docs-only architectural target. This decision
states future distance **intent** (`DYNAMICALLY_DERIVED`). It does not bind
MODEL_C, does not authorize a freeze-exception, and does not authorize a
derivation formula, producer, or runtime seam.

Cross-instrument validity of the frozen numbers remains
`NOT_RATIFIED_PENDING_SEPARATE_VALIDATION`. No Selection, Trading, or
Execution authority is created.

## Explicit non-authorizations

```text
CONFIG_MUTATION_AUTHORIZED=false
NUMERIC_MIGRATION_AUTHORIZED=false
SRC_RUNTIME_MUTATION_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
FREEZE_EXCEPTION_AUTHORIZED=false
NORMALIZATION_JOIN_IMPLEMENTATION_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
PERMIT_ENVELOPE_AUTHORIZED=false
```

## Next authority boundary

Cap-6.2 digest residual owner and Cap-6.5 adverse residual owner are now
persisted docs-only in
[`CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md`](CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md)
(Master Runbook §9.2.3). That persist does **not** authorize runtime, a
freeze-exception, or numeric mutation.

```text
FORMULA_OWNER_AUTHORITY_READY_CONTRACT_PERSISTED=true
CAP62_DIGEST_OWNER_CONTRACT_PERSISTED=true
CAP65_ADVERSE_OWNER_CONTRACT_PERSISTED=true
DERIVED_DISTANCE_FORMULA_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
NEXT_BOUNDED_WORKPACKAGE=
  freeze-exception preconditions are persisted in Master Runbook §9.2.4.
  The freeze-exception itself remains later and unauthorized.
  Cross-instrument derived-distance validation remains a later separate
  GO before runtime bind.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1
HARD_STOP_AFTER_THIS_PERSIST=true
```
