---
title: "Cap 6.3 Dynamic Derivation Freeze-Exception v1"
status: "FREEZE_EXCEPTION_AUTHORITY_CONTRACT_PERSISTED_DOCS_ONLY"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1"
---

# Cap 6.3 Dynamic Derivation Freeze-Exception v1

Canonical persist of the **narrow MODEL_C dynamic-derivation freeze-exception
authority** under
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.5.
This file is the decision/contract record and navigation twin. It is **not**
a numeric mutation, **not** a runtime bind, **not** generator-input
retirement, and **not** a producer activation.

```text
DOCUMENT_CLASS=FREEZE_EXCEPTION_AUTHORITY_CONTRACT_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
EXPECTED_ORIGIN_MAIN=02f26b4356a76b3a8b228b05bbc2be8652205cbb
PARENT_PRECONDITIONS_CONTRACT=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1.md
PARENT_RESIDUAL_OWNER_CONTRACT=docs/ops/specs/CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md
PARENT_FORMULA_OWNER_CONTRACT=docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md
PARENT_UNIT_CLASS_DECISION=docs/ops/specs/CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1.md
PARENT_MODEL_C_ARCHITECTURE=docs/ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
PARENT_DUAL_USE_SPLIT=docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.5_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=SECTION_3_CURRENT_FREEZE_SURFACES
ALREADY_ADJUDICATED=SECTION_2_TEMPORAL_SPLIT_AND_SECTION_4_NAMED_SURFACES
NAVIGATION_ONLY=MAP_OF_TRUTH_AND_ATLAS
HISTORICAL_STATE=NONE_USED_AS_CURRENT
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_8_LATER_GATES
CONFLICTED=NONE
OWNER_CHOICE_REQUIRED=false
```

This persist grants **exception authority** only. CURRENT productive
MODEL_B numbers, producers, and aliases remain operative until a later
atomic cutover (layer E).

```text
FREEZE_EXCEPTION_PRECONDITIONS_MET=true
FREEZE_EXCEPTION_AUTHORIZED=true
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=true
FREEZE_EXCEPTION_ACTUALLY_PERSISTED=true
EXCEPTION_AUTHORITY=true
MUTATION_AUTHORITY=false
RUNTIME_BIND_AUTHORITY=false
EXCEPTION_AUTHORITY_IMPLIES_MUTATION_AUTHORITY=false
EXCEPTION_AUTHORITY_IMPLIES_RUNTIME_BIND_AUTHORITY=false
FORMULA_OWNER_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
MODEL_C_BOUND=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
DUAL_AUTHORITY_INTRODUCED=false
ZERO_AUTHORITY_INTRODUCED=false
CAP63_FALLBACK_INTRODUCED=false
```

## 2. Temporal split (required)

Class: `CANONICAL_AUTHORITY`.

```text
EXCEPTION_AUTHORITY != MUTATION_AUTHORITY
EXCEPTION_AUTHORITY != RUNTIME_BIND_AUTHORITY
MUTATION_AUTHORITY != RUNTIME_BIND_AUTHORITY
```

| Authority | This persist | Meaning |
|----------|--------------|---------|
| Exception authority | `true` | Named Cap 6.2 / 6.3 generator-input freeze and Cap 6.5 adverse consumer alias **may later** be retired/retargeted without silent bypass |
| Mutation authority | `false` | CURRENT `200.0` / `80.0` / `120.0` / `confirmation_epochs=2` / profit-protection `200.0` stay in force |
| Runtime-bind authority | `false` | `derive_scope_event_distances_v1` stays unimplemented; seam unbound; MODEL_C unbound |

Until the later atomic retire+bind (layer E), CURRENT Cap 6.3 generator
inputs remain the productive owner. Binding a derived producer while those
inputs stay live would be `DUAL_AUTHORITY`. Retiring those inputs without
binding the derived producer would be `ZERO_AUTHORITY`. Using Dual Envelope
as fallback after bind would be `CAP63_FALLBACK`. All three remain forbidden.

```text
CURRENT_PRODUCER_AND_INPUTS_REMAIN_OPERATIVE=true
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
ATOMIC_RETIRE_AND_BIND_REQUIRED=true
```

## 3. CURRENT freeze census (unchanged by this persist)

Class: `RAW_FORENSIC_EVIDENCE` for hosts/tests; `CANONICAL_AUTHORITY` for
capability freeze text. CURRENT productive baseline remains MODEL_B.

```text
CURRENT_MODEL=MODEL_B
CURRENT_GENERATOR_DISTANCE_OWNER=CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1
CURRENT_NUMERIC_SSOT=config/ops/canonical_decision_runtime_config_v1.toml
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
confirmation_epochs=2
PROFIT_PROTECTION_DISTANCE=200.0
min_scope_band=50.0
MIN_SCOPE_BAND_OWNER=NOT_CAP63
```

Forensic pins on origin/main `02f26b435` (docs-only successor of `a99ebe99`;
source freeze pins unchanged):

| Surface | Pin |
|---------|-----|
| Cap 6.3 numeric SSOT | `config/ops/canonical_decision_runtime_config_v1.toml` |
| Cap 6.3 expected-value / parity | `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py` `EXPECTED_UP_DISTANCE=200.0`; `parity_v1.py` |
| Cap 6.2 FROZEN_* aliases | `src/ops/dynamic_scope_persistence_binding_v1/constants_v1.py` aliases `CANONICAL_*` as `FROZEN_*`; `parity_v1.py` asserts `200.0` / `80.0` / `120.0` |
| Cap 6.2 host defaults | `host_binding_v1.py` defaults from `FROZEN_*` |
| Cap 6.5 adverse consumer alias | `src/ops/exit_policy_producer_binding_v1/constants_v1.py` `FROZEN_ADVERSE_EXIT_DISTANCE = float(CANONICAL_ADVERSE_EXIT_DISTANCE)` |
| Cap 6.5 profit-protection own owner | `FROZEN_PROFIT_PROTECTION_DISTANCE=200.0` |

## 4. Named exception surfaces (this grant)

Class: `ALREADY_ADJUDICATED` by Master Runbook §9.2.4 §5. Consumed here as
the B persist.

This exception **names and excepts** only:

1. Cap 6.3 generator-input freeze for `up_distance` / `adverse_exit_distance`
   / `reversal_distance` (CURRENT `200.0` / `80.0` / `120.0`)
2. Cap 6.2 `FROZEN_*` alias / digest coupling to those generator inputs
3. Cap 6.5 adverse consumer alias (`FROZEN_ADVERSE_EXIT_DISTANCE` alias of
   Cap 6.3 `adverse_exit_distance`), so a later E may **retarget the consumer**
   to derived OQ-C2 adverse (not mint a Cap 6.5 own frozen `80.0`)

```text
EXCEPTION_SURFACES=
  CAP63_GENERATOR_INPUT_FREEZE_UP_ADVERSE_REVERSAL
  CAP62_FROZEN_ALIAS_AND_DIGEST_COUPLING_TO_THOSE_INPUTS
  CAP65_ADVERSE_CONSUMER_ALIAS_OF_CAP63_ADVERSE
EXCEPTS_CAP63_GENERATOR_INPUT_FREEZE=true
EXCEPTS_CAP62_GENERATOR_ALIAS_FREEZE=true
EXCEPTS_CAP65_ADVERSE_CONSUMER_ALIAS_FREEZE=true
```

## 5. Surfaces explicitly not excepted

```text
NON_EXCEPTION_SURFACES=
  CAP65_PROFIT_PROTECTION_OWNER_AND_VALUE_200
  CONFIRMATION_EPOCHS_2
  MIN_SCOPE_BAND_NOT_CAP63
  ALL_OTHER_CAP62_CAP63_CAP65_FREEZE_SURFACES
EXCEPTS_CAP65_PROFIT_PROTECTION_FREEZE=false
EXCEPTS_CONFIRMATION_EPOCHS=false
EXCEPTS_MIN_SCOPE_BAND=false
PROFIT_PROTECTION_IDENTITY_SPLIT_MUST_REMAIN=true
PROFIT_PROTECTION_MUST_NOT_FOLLOW_DERIVED_UP_DISTANCE=true
confirmation_epochs_REMAINS_CAP63=true
MIN_SCOPE_BAND_KEPT_SEPARATE=true
```

This exception is **not** a general freeze waiver for Cap 6.2 / 6.3 / 6.5.

## 6. Layer-A preconditions (consumed, still MET)

Class: `ALREADY_ADJUDICATED`. Required entry criteria from §9.2.4 remain true.

```text
PRECONDITION_GRAPH_1_UNIT_CLASS_PERSISTED=true
PRECONDITION_GRAPH_2_FORMULA_IDENTITY_PERSISTED=true
PRECONDITION_GRAPH_3_DUAL_USE_SPLIT_IMPLEMENTED=true
PRECONDITION_GRAPH_4_CAP62_DIGEST_OWNER_PERSISTED=true
PRECONDITION_GRAPH_5_CAP65_ADVERSE_OWNER_PERSISTED=true
PRECONDITION_GRAPH_DIRECTIONAL_MAPPING_RUNTIME_BOUND=true
PRECONDITION_GRAPH_PRECONDITIONS_CONTRACT_PERSISTED=true
CURRENT_CANONICAL_MODEL=MODEL_B
```

## 7. Explicit non-authorizations

```text
CONFIG_MUTATION_AUTHORIZED=false
NUMERIC_MIGRATION_AUTHORIZED=false
SRC_RUNTIME_MUTATION_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
DERIVE_SCOPE_EVENT_DISTANCES_V1_IMPLEMENTATION_AUTHORIZED=false
DERIVATION_SEAM_IMPLEMENTATION_AUTHORIZED=false
PURE_FUNCTION_AND_GOLDEN_VECTORS_AUTHORIZED=false
NORMALIZATION_JOIN_IMPLEMENTATION_AUTHORIZED=false
CAP23_SELECTION_REWIRE_AUTHORIZED=false
CAP24_BINDING_REWIRE_AUTHORIZED=false
RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
CAP65_OWN_FROZEN_ADVERSE_80_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
CROSS_INSTRUMENT_VALIDATION_AUTHORIZED=false
TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
PERMIT_ENVELOPE_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
```

## 8. Residuals / later gates that remain OPEN

Class: `OPEN`. This persist does **not** close them.

```text
CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=AUTHORITY_MISSING
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
DERIVE_SCOPE_EVENT_DISTANCES_V1_STATUS=UNIMPLEMENTED
DERIVATION_SEAM_STATUS=UNBOUND
ATOMIC_RETIRE_BIND_AUTHORIZED=false
```

Canonical next after this persist is layer C (pure derivation function +
golden vectors vs MODEL_B). Cross-instrument / price-scale remain layer D,
required **before runtime bind** (layer E), not pulled into C.

## 9. Machine markers

```text
MARKER: CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: EXCEPTION_AUTHORITY_NOT_MUTATION
MARKER: EXCEPTION_AUTHORITY_NOT_RUNTIME_BIND
MARKER: FREEZE_EXCEPTION_PRECONDITIONS_MET=true
MARKER: FREEZE_EXCEPTION_AUTHORIZED=true
MARKER: MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=true
MARKER: FREEZE_EXCEPTION_ACTUALLY_PERSISTED=true
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MARKER: MODEL_C_BOUND=false
MARKER: FORMULA_OWNER_AUTHORIZED=false
MARKER: DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
MARKER: ATOMIC_RETIRE_BIND_AUTHORIZED=false
MARKER: DUAL_AUTHORITY_INTRODUCED=false
MARKER: ZERO_AUTHORITY_INTRODUCED=false
MARKER: CAP63_FALLBACK_INTRODUCED=false
MARKER: DUAL_AUTHORITY_FORBIDDEN=true
MARKER: ZERO_AUTHORITY_FORBIDDEN=true
MARKER: CAP63_GENERATOR_FALLBACK_FORBIDDEN=true
MARKER: CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
MARKER: TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
MARKER: LIVE_AUTHORIZED=false
MARKER: MAX_POSITIONS=1
```

## 10. STOP conditions

Stop immediately if this file is treated as:

1. mutation of frozen `200.0` / `80.0` / `120.0` / profit-protection `200.0`
2. `MUTATION_AUTHORITY=true` or `RUNTIME_BIND_AUTHORITY=true`
3. implementation of `derive_scope_event_distances_v1` or the Integrated Replay seam
4. generator-input retirement or atomic retire+bind
5. `MODEL_C_FORMULA_AUTHORIZED=true` or `MODEL_C_BOUND=true`
6. Cap 6.3 fallback, clamp to frozen numbers, or a new floor
7. Cap-23 / Cap-24 selection rewire
8. research BPS rewrite or Cap 6.5 profit-protection rewrite
9. a Cap 6.5 own frozen `80.0` adverse owner
10. a second productive distance owner, dual authority, or zero authority
11. closure of cross-instrument validation, price-scale metadata, or golden vectors
12. Testnet / Canary / Live, orders, credentials, or venue POST

## 11. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  pure derivation function plus golden vectors vs MODEL_B remain later
  and unauthorized. Cross-instrument derived-distance validation and
  tick/lot/ctVal price-scale metadata remain separate later gates before
  runtime bind. No seam, no atomic retire+bind, no CURRENT numeric mutation.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1
LATER_REQUIRED_GO_ALIAS=PURE_DERIVATION_FUNCTION_AND_GOLDEN_VECTORS
HARD_STOP_AFTER_THIS_PERSIST=true
NEXT_OWNER_GO_CONSUMED=false
```
