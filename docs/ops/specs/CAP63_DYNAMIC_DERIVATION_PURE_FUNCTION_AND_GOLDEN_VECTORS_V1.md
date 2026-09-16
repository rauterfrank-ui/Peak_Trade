---
title: "Cap 6.3 Dynamic Derivation Pure Function And Golden Vectors v1"
status: "PURE_FUNCTION_IMPLEMENTED_UNBOUND_DOCS_AND_SRC"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1"
---

# Cap 6.3 Dynamic Derivation Pure Function And Golden Vectors v1

Canonical persist of the **unbound** pure function `derive_scope_event_distances_v1`
under `OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.6.
This file is the decision/contract record and navigation twin. It is **not**
a productive producer, **not** a runtime bind, **not** generator-input
retirement, and **not** a numeric cutover of CURRENT Dual Envelope values.

```text
DOCUMENT_CLASS=PURE_FUNCTION_AND_GOLDEN_VECTORS_CONTRACT
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_UNBOUND_PURE_FUNCTION
EXPECTED_ORIGIN_MAIN=afc1a9730af286ba86adfb94113cd45f551ad1e7
PARENT_FREEZE_EXCEPTION_CONTRACT=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1.md
PARENT_FORMULA_OWNER_CONTRACT=docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
OWNER_CHOICE_PURE_FUNCTION_FAILURE_CHANNEL=FAIL_CLOSED_RESULT
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.6_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=SECTION_6_UNBOUND_CENSUS
ALREADY_ADJUDICATED=SECTION_3_OQ_C1_C2_AND_OWNER_CHOICE
NAVIGATION_ONLY=MAP_OF_TRUTH_AND_ATLAS
HISTORICAL_STATE=NONE_USED_AS_CURRENT
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_8_LATER_GATES
CONFLICTED=NONE
OWNER_CHOICE_REQUIRED=false
OWNER_CHOICE_CONSUMED=true
```

```text
DERIVED_DISTANCE_FUNCTION_IMPLEMENTED=true
DERIVED_DISTANCE_FUNCTION_PURE=true
DERIVED_DISTANCE_FUNCTION_UNBOUND=true
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MODEL_C_BOUND=false
CURRENT_CANONICAL_MODEL=MODEL_B
FORMULA_OWNER_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

## 2. Owner-choice consumed (failure channel)

Class: `CANONICAL_AUTHORITY`. Consumed by this persist; not reopened.

```text
OWNER_CHOICE_PURE_FUNCTION_FAILURE_CHANNEL=FAIL_CLOSED_RESULT
PURE_FUNCTION_FAILURE_CHANNEL=FAIL_CLOSED_RESULT
RESULT_CONTRACT_AUTHORITY_EFFECT=NONE
INVALID_RESULT_RAISES=false
INVALID_RESULT_HAS_USABLE_DISTANCES=false
INVALID_RESULT_HAS_FALLBACK=false
```

Valid result: `ok=true` and exclusively `up_distance`, `adverse_exit_distance`,
`reversal_distance`. Invalid result: `ok=false`, no usable distances, one
stable reason `INVALID_INPUT`. No raise for the invalid-band domain. No
partial result, replacement value, clamp, Cap 6.3 fallback, or last-derived
fallback.

The result type is a data contract only. Failure reasons describe input
validity only. They do not pre-empt later cycle or generator policy.

## 3. Pure function contract (CURRENT Authority + consumed Owner-choice)

Class: `ALREADY_ADJUDICATED` OQ-C1/OQ-C2 plus consumed Owner-choice.

```text
FUNCTION_NAME=derive_scope_event_distances_v1
PACKAGE=src.ops.derive_scope_event_distances_v1
INPUT=current_hysteresis_band
INPUT_TYPE=float
INPUT_COERCION_PRESENT=false
NUMERIC_POLICY=IEEE_FLOAT_NO_QUANTIZATION
OQ-C1=up_distance = current_hysteresis_band
OQ-C2_ADVERSE=up_distance * (80.0 / 200.0)
OQ-C2_REVERSAL=up_distance * (120.0 / 200.0)
VALIDITY=type_is_float AND finite AND > 0
FAILURE_REASON=INVALID_INPUT
HARD_MAX_POLICY_IMPLEMENTED=false
LAST_DERIVED_STATE_SEAM_IMPLEMENTED=false
CONFIRMATION_EPOCHS_DERIVED=false
PROFIT_PROTECTION_DERIVED=false
MIN_SCOPE_BAND_DERIVED=false
```

No tick/lot/ctVal/price-scale quantization. No `1.0` floor. No hard_max in
this function. No clamp to `200`/`80`/`120`.

## 4. Golden vectors

Class: `CANONICAL_AUTHORITY` for persistence location; expected values are
the OQ-C1/OQ-C2 formula, not CURRENT Dual Envelope authority.

Owner:
[`src/ops/derive_scope_event_distances_v1/golden_vectors_v1.py`](../../../src/ops/derive_scope_event_distances_v1/golden_vectors_v1.py)

```text
GOLDEN_VECTOR_OWNER=src/ops/derive_scope_event_distances_v1/golden_vectors_v1.py
GOLDEN_VALID_COUNT=6
GOLDEN_INVALID_COUNT=10
GOLDEN_VECTOR_AUTHORITY=OQ_C1_C2_FORMULA_NOT_CURRENT_DUAL_ENVELOPE
```

The `200.0` valid vector is a formula coincidence with CURRENT MODEL_B
numbers. It is not clamp authority and not Dual Envelope fallback.

## 5. Explicit non-authorizations

```text
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MODEL_C_BOUND=false
MODEL_C_FORMULA_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
CONFIG_MUTATION_AUTHORIZED=false
HARD_MAX_POLICY_IMPLEMENTED=false
LAST_DERIVED_STATE_SEAM_IMPLEMENTED=false
CROSS_INSTRUMENT_VALIDATION_AUTHORIZED=false
TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false
CAP23_SELECTION_REWIRE_AUTHORIZED=false
CAP24_BINDING_REWIRE_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
```

## 6. Unbound census (required)

Class: `RAW_FORENSIC_EVIDENCE` via focused tests. Productive hosts continue to
pass Cap 6.3 frozen `200.0` / `80.0` / `120.0` into the generator.

```text
PRODUCTIVE_CONSUMER_COUNT=0
PRODUCTIVE_CALLGRAPH_REACHABLE=false
CURRENT_PRODUCER_AND_INPUTS_REMAIN_OPERATIVE=true
DUAL_AUTHORITY_INTRODUCED=false
ZERO_AUTHORITY_INTRODUCED=false
CAP63_FALLBACK_INTRODUCED=false
SEAM_MUST_NOT_EXIST_IN_RUNTIME_UNTIL_SEPARATE_RUNTIME_BIND_GO=true
```

Not imported by:

- `src&#47;trading&#47;master_v2&#47;integrated_offline_trading_logic_replay_v1.py`
- `src&#47;trading&#47;master_v2&#47;deterministic_scope_event_generator_v1.py`
- Cap 6.3 / Cap 6.2 / Cap 6.5 productive packages

## 7. CURRENT productive baseline (unchanged)

```text
CURRENT_CANONICAL_MODEL=MODEL_B
CURRENT_GENERATOR_DISTANCE_OWNER=CAPABILITY_6_3
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
confirmation_epochs=2
PROFIT_PROTECTION_DISTANCE=200.0
MIN_SCOPE_BAND_OWNER=NOT_CAP63
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

## 8. Residuals / later gates that remain OPEN

Class: `OPEN`. This persist does **not** close them and does **not** invent a
runtime-bind sequence.

```text
CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=AUTHORITY_MISSING
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
DERIVATION_SEAM_STATUS=UNBOUND
ATOMIC_RETIRE_BIND_AUTHORIZED=false
```

Cross-instrument validation and tick/lot/ctVal/price-scale remain separate
later gates **before** runtime bind. This persist does not authorize either.
Runtime bind + atomic retire remain layer E.

## 9. Machine markers

```text
MARKER: CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1_EXISTS
MARKER: DERIVED_DISTANCE_FUNCTION_IMPLEMENTED=true
MARKER: DERIVED_DISTANCE_FUNCTION_PURE=true
MARKER: DERIVED_DISTANCE_FUNCTION_UNBOUND=true
MARKER: PURE_FUNCTION_FAILURE_CHANNEL=FAIL_CLOSED_RESULT
MARKER: RESULT_CONTRACT_AUTHORITY_EFFECT=NONE
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MARKER: MODEL_C_BOUND=false
MARKER: DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
MARKER: DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MARKER: ATOMIC_RETIRE_BIND_AUTHORIZED=false
MARKER: DUAL_AUTHORITY_INTRODUCED=false
MARKER: ZERO_AUTHORITY_INTRODUCED=false
MARKER: CAP63_FALLBACK_INTRODUCED=false
MARKER: PRODUCTIVE_CALLGRAPH_REACHABLE=false
MARKER: CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
MARKER: TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
MARKER: LIVE_AUTHORIZED=false
MARKER: MAX_POSITIONS=1
```

## 10. STOP conditions

Stop immediately if this file is treated as:

1. productive producer authorization or runtime bind
2. atomic retirement of Cap 6.3 generator inputs `200.0` / `80.0` / `120.0`
3. mutation of CURRENT effective Dual Envelope or profit-protection values
4. Cap 6.3 fallback, clamp to frozen numbers, or a new floor
5. last-derived state seam or hard_max policy inside this function
6. Cap-23 / Cap-24 selection rewire
7. closure of cross-instrument validation or price-scale metadata
8. a second productive distance owner, dual authority, or zero authority
9. Testnet / Canary / Live, orders, credentials, or venue POST

## 11. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  Cross-instrument derived-distance validation remains the earliest named
  OPEN gate before runtime bind. Tick/lot/ctVal/price-scale metadata remains
  a separate later AUTHORITY_MISSING gate and is not consumed by that next
  GO. Runtime bind and atomic retire remain unauthorized.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
HARD_STOP_AFTER_THIS_PERSIST=true
NEXT_OWNER_GO_CONSUMED=false
```
