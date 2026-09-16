---
title: "Cap 6.3 Dynamic Derivation Cross-Instrument Validation Protocol v1"
status: "PROTOCOL_OWNER_PERSISTED_DOCS_ONLY"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1"
---

# Cap 6.3 Dynamic Derivation Cross-Instrument Validation Protocol v1

Canonical persist of the **protocol owner** for
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1`
under
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.7.
This file is the decision/contract record and navigation twin. It is **not**
cross-instrument validation execution, **not** a validation harness, **not**
instrument golden evidence, **not** a productive producer, **not** a runtime
bind, **not** generator-input retirement, and **not** a numeric cutover of
CURRENT Dual Envelope values.

```text
DOCUMENT_CLASS=CROSS_INSTRUMENT_VALIDATION_PROTOCOL_CONTRACT_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
EXPECTED_ORIGIN_MAIN=eae0206aabea768ef183458ce62d3a299059f289
PARENT_PURE_FUNCTION_CONTRACT=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1.md
PARENT_FORMULA_OWNER_CONTRACT=docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
PARENT_UNIT_CLASS_DECISION=docs/ops/specs/CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1.md
SELECTION_OWNER_REFERENCED=docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.7_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=NONE_CREATED_BY_THIS_PERSIST
ALREADY_ADJUDICATED=SECTION_3_REUSED_OWNERS
NAVIGATION_ONLY=MAP_OF_TRUTH_AND_ATLAS
HISTORICAL_STATE=NONE_USED_AS_CURRENT
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_8_LATER_GATES
CONFLICTED=NONE
OWNER_CHOICE_REQUIRED=false
OWNER_CHOICE_CONSUMED=true
```

```text
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=PERSISTED
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_PATH=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1.md
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
CROSS_INSTRUMENT_VALIDATION_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MODEL_C_BOUND=false
CURRENT_CANONICAL_MODEL=MODEL_B
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
METADATA_GATE_CONSUMED=false
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
```

## 2. What this persist does and does not do

Class: `CANONICAL_AUTHORITY`.

This persist **closes** `CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER`.
It does **not** consume
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1`.

```text
VALIDATION_EXECUTED=false
VALIDATION_HARNESS_AUTHORIZED=false
INSTRUMENT_GOLDEN_EVIDENCE_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
CAP23_REWIRE_AUTHORIZED=false
CAP24_REWIRE_AUTHORIZED=false
NEW_INSTRUMENT_LIST_AUTHORIZED=false
NEW_UNIVERSE_OWNER_AUTHORIZED=false
TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false
QUANTIZATION_RULE_AUTHORIZED=false
ROUNDING_RULE_AUTHORIZED=false
OD2_ARMED_RESIDUAL_MUTATION_AUTHORIZED=false
ORIENTATION_MAPPING_MUTATION_AUTHORIZED=false
```

## 3. Reused authorities (no new trading semantics)

Class: `ALREADY_ADJUDICATED` owners referenced, not copied.

### 3.1 INSTRUMENT_SET_OR_SELECTION_RULE

```text
THIS_PROTOCOL_DEFINES_NO_INSTRUMENT_LIST=true
SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
SELECTION_OWNER_SPEC=docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md
SELECTION_MODE=SINGLE_SELECTED_FUTURE
MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
CAP23_REMAINS_SOLE_PRODUCTIVE_SELECTION_OWNER=true
```

Later validation may sample only futures that Cap 2.3 can select as
`SINGLE_SELECTED_FUTURE`. Offline `RuntimeScopeState` snapshots of such
instruments are allowed as **validation inputs**. They are not a second
selection owner, not a ranking universe, and not simultaneous multi-future
occupancy.

Cross-instrument meaning, already implied by the unbound function:

```text
DERIVE_FUNCTION_HAS_INSTRUMENT_ID_PARAMETER=false
DISTANCES_DIFFER_ACROSS_INSTRUMENTS_ONLY_VIA_EACH_INSTRUMENT_OWN_BAND=true
ABSOLUTE_CAP63_200_80_120_IS_NOT_SHARED_CROSS_INSTRUMENT_SCALE=true
```

### 3.2 BAND_INPUT_PROVENANCE

```text
BAND_FIELD_OWNER=trading.master_v2.double_play_state.RuntimeScopeState.current_hysteresis_band
BAND_PRODUCER=trading.master_v2.double_play_state.update_dynamic_boundaries
FORMULA_OWNER=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
OQ_C1_MAPPING=up_distance = current_hysteresis_band
SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=FORBIDDEN
GOLDEN_VECTORS_ARE_FORMULA_VECTORS_NOT_INSTRUMENT_UNIVERSE=true
HYSTERESIS_MULTIPLIER_USED=false
```

`current_hysteresis_band` is the trailing-band field already written by
`update_dynamic_boundaries`. Formula golden vectors in
`src&#47;ops&#47;derive_scope_event_distances_v1&#47;golden_vectors_v1.py`
remain formula vectors. They are not an instrument universe and not productive
band authority.

### 3.3 PASS_FAIL_CRITERIA (pre-metadata-gate only)

Class: `CANONICAL_AUTHORITY` for the later validation GO. Not executed here.

PASS only if every sampled valid band from §3.1/§3.2 satisfies OQ-C1/OQ-C2
identity already recorded in the formula adjudication:

```text
up_distance = current_hysteresis_band
adverse_exit_distance = up_distance * (80.0 / 200.0)
reversal_distance = up_distance * (120.0 / 200.0)
```

and:

1. `derive_scope_event_distances_v1` remains unbound
   (`PRODUCTIVE_CALLGRAPH_REACHABLE=false`).
2. Valid result: `ok=true` and exclusively the three distances.
3. Nested geometry: `adverse_exit_distance > 0`, `reversal_distance > 0`,
   `adverse_exit_distance <= reversal_distance`,
   `adverse_exit_distance < up_distance`.
4. No clamp, floor, or Cap 6.3 fallback to frozen `200.0` / `80.0` / `120.0`.
5. The derivation consumes no `instrument_id`.

FAIL if any PASS item is broken.

Must **not** fail for, and must **not** claim:

```text
TICK_ALIGNMENT=NOT_IN_SCOPE
LOT_ALIGNMENT=NOT_IN_SCOPE
CTVAL_ALIGNMENT=NOT_IN_SCOPE
PRICE_SCALE_ALIGNMENT=NOT_IN_SCOPE
VENUE_EXECUTABILITY=NOT_IN_SCOPE
GENERATOR_HARD_MAX_POLICY=NOT_IN_SCOPE_HERE
```

### 3.4 EVIDENCE_OWNER_AND_PATH

```text
EVIDENCE_AUTHORITY_EFFECT=NONE
EVIDENCE_IS_NOT_TRADING_AUTHORITY=true
THIS_PROTOCOL_PERSIST_CREATES_NO_VALIDATION_EVIDENCE=true
LATER_VALIDATION_TEST_OWNER=tests/ops/test_cap63_dynamic_derivation_cross_instrument_validation_v1.py
LATER_VALIDATION_EVIDENCE_PATH=evidence/ops/cap63_dynamic_derivation_cross_instrument_validation_v1/
LATER_VALIDATION_CONTRACT_RECORD=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1.md
```

The later paths above are **illustrative allowlist names** until that GO
creates them. They have no runtime or trading authority.

### 3.5 ALLOWED_FILES (later validation GO only)

Allowed when
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1`
is later consumed:

- `tests&#47;ops&#47;test_cap63_dynamic_derivation_cross_instrument_validation_v1.py`
- `evidence&#47;ops&#47;cap63_dynamic_derivation_cross_instrument_validation_v1&#47;**`
- `docs&#47;ops&#47;specs&#47;CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1.md`
- Master Runbook persist for that validation closeout
- Map of Truth and Atlas navigation pointers (`AUTHORITY=NONE`)

Forbidden to that later GO (and to this persist):

- `src&#47;trading&#47;**`
- `src&#47;execution&#47;**`
- `src&#47;live&#47;**`
- productive generator rewiring
- `scope_direction_from_side_state_v1` mutation
- `transition_state` mutation
- Cap 23 / Cap 24 / TOP-20 / SSF rewire
- Cap 6.5 profit-protection `200.0` mutation
- tick / lot / ctVal / price-scale metadata authority

`src&#47;ops&#47;derive_scope_event_distances_v1` may be **imported** by later
tests. It must not be mutated by the later validation GO unless a separate
Owner-GO explicitly names that mutation.

## 4. CURRENT productive baseline (unchanged)

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
DERIVED_DISTANCE_FUNCTION_UNBOUND=true
PRODUCTIVE_CALLGRAPH_REACHABLE=false
```

## 5. Explicit non-authorizations

```text
CONFIG_MUTATION_AUTHORIZED=false
NUMERIC_MIGRATION_AUTHORIZED=false
SRC_RUNTIME_MUTATION_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
GENERATOR_INPUT_RETIREMENT_AUTHORIZED=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
CAP23_SELECTION_REWIRE_AUTHORIZED=false
CAP24_BINDING_REWIRE_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
OD2_ARMED_RESIDUAL_UNCHANGED=true
OD2_LAST_STEP=KEEP_BOUND_DESTINATION_PREFIX
```

## 6. Residuals / later gates that remain OPEN

Class: `OPEN`.

```text
CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
METADATA_GATE_CONSUMED=false
DERIVATION_SEAM_STATUS=UNBOUND
ATOMIC_RETIRE_BIND_AUTHORIZED=false
OD2_ARMED_RESIDUAL=OPEN
```

Tick/lot/ctVal/price-scale remains a **separate later** `AUTHORITY_MISSING`
gate and is **not consumed** by this protocol or by the next validation GO.

## 7. Machine markers

```text
MARKER: CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=PERSISTED
MARKER: CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
MARKER: METADATA_GATE_CONSUMED=false
MARKER: TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MARKER: MODEL_C_BOUND=false
MARKER: DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MARKER: THIS_PROTOCOL_DEFINES_NO_INSTRUMENT_LIST=true
MARKER: SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
MARKER: BAND_FIELD_OWNER=RuntimeScopeState.current_hysteresis_band
MARKER: SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=FORBIDDEN
MARKER: EVIDENCE_AUTHORITY_EFFECT=NONE
MARKER: LIVE_AUTHORIZED=false
MARKER: MAX_POSITIONS=1
```

## 8. STOP conditions

Stop immediately if this file is treated as:

1. executed cross-instrument validation or a validation harness
2. instrument-list or universe ownership
3. Cap 23 / Cap 24 / TOP-20 / SSF rewire
4. tick / lot / ctVal / price-scale / quantization / rounding authority
5. MODEL_C runtime bind or Cap 6.3 generator-input retirement
6. productive Dual Envelope numeric cutover
7. orientation, SideState, Neutral-Start, or OD2 ARMED mutation
8. Testnet / Canary / Live, orders, credentials, or venue POST

## 9. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  Execute Cap 6.3 cross-instrument derived-distance validation under this
  protocol. Do not bind MODEL_C. Do not consume the tick/lot/ctVal
  price-scale metadata gate.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
HARD_STOP_AFTER_THIS_PERSIST=true
NEXT_OWNER_GO_CONSUMED=false
TOKEN_RENAMED=false
```
