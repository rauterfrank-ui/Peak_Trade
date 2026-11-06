---
title: "Cap 6.3 Dynamic Derivation Cross-Instrument Validation v1"
status: "CROSS_INSTRUMENT_VALIDATION_PERFORMED_PRE_METADATA_DOCS_AND_EVIDENCE"
owner: "ops"
last_updated: "2026-09-17"
docs_token: "DOCS_TOKEN_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1"
---

# Cap 6.3 Dynamic Derivation Cross-Instrument Validation v1

Canonical persist of the **pre-metadata-scope** cross-instrument validation
under `OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.8.
This file is the decision/contract record and navigation twin. It is **not**
a MODEL_C runtime bind, **not** generator-input retirement, **not** a
tick/lot/ctVal/price-scale metadata gate, and **not** a numeric cutover of
CURRENT Dual Envelope values.

```text
DOCUMENT_CLASS=CROSS_INSTRUMENT_VALIDATION_CONTRACT_DOCS_AND_EVIDENCE
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_VALIDATION_EVIDENCE_AND_DOCS
EXPECTED_ORIGIN_MAIN=26b62aae2965bf146818a40e951513f9be05c5df
PARENT_PROTOCOL=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_PROTOCOL_V1.md
PARENT_PURE_FUNCTION_CONTRACT=docs/ops/specs/CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1.md
PARENT_FORMULA_OWNER_CONTRACT=docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
SELECTION_OWNER_REFERENCED=docs/ops/specs/MASTER_V2_CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.8_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=EVIDENCE_DIR_AND_CAP62_BAND_EXEMPLAR
ALREADY_ADJUDICATED=OQ_C1_OQ_C2_FORMULA_AND_CAP23_SELECTION_OWNER
NAVIGATION_ONLY=MAP_OF_TRUTH_AND_ATLAS
HISTORICAL_STATE=SECTION_3_SNAPSHOT_IDENTITY_JOIN
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_8_LATER_GATES
CONFLICTED=NONE
OWNER_CHOICE_REQUIRED=false
OWNER_CHOICE_CONSUMED=true
```

```text
CROSS_INSTRUMENT_VALIDATION_PERFORMED=true
VALIDATION_PROTOCOL_CONFORMANT=true
VALIDATION_UNIVERSE_FROM_EXISTING_AUTHORITY=true
BAND_PROVENANCE_VALID=true
OQ_C1_PASS=true
OQ_C2_PASS=true
FORMULA_UNCHANGED=true
RATIOS_UNCHANGED=true
UNAUTHORIZED_FLOOR_OR_CLAMP=false
METADATA_GATE_CONSUMED=false
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
MODEL_C_BOUND=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
PRODUCTIVE_SWITCH_PATH_CHANGED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
CURRENT_CANONICAL_MODEL=MODEL_B
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

## 2. What this persist does and does not do

Class: `CANONICAL_AUTHORITY`.

This persist **consumes**
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1`
after protocol-conformant pre-metadata PASS.

It does **not** consume the tick/lot/ctVal/price-scale metadata gate.
It does **not** bind MODEL_C.

```text
VALIDATION_EXECUTED=true
PRE_METADATA_SCOPE=true
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
DUAL_ENVELOPE_WP=NOT_STARTED
```

## 3. Reused authorities (no new trading semantics)

### 3.1 INSTRUMENT_SET_OR_SELECTION_RULE

Class: `ALREADY_ADJUDICATED` owner consumed, not copied.

```text
THIS_VALIDATION_DEFINES_NO_INSTRUMENT_LIST=true
SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
SELECTION_MODE=SINGLE_SELECTED_FUTURE
MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
CAP23_REMAINS_SOLE_PRODUCTIVE_SELECTION_OWNER=true
VALIDATION_UNIVERSE_SOURCE=CAP22_EVIDENCE_RANKED_ELIGIBLE_CANDIDATES_AS_CAP23_SELECTABLE_CONTEXT
VALIDATION_UNIVERSE_PATH=docs/evidence/capability_2_2_productive_futures_ranking_producer_v1/productive_ranking/productive_futures_ranking_snapshot_v1.json
CAP22_EVIDENCE_RANKING_SNAPSHOT_ID=pfr_evidence_cap22_v1
CAP23_HISTORICAL_SELECTION_INSTRUMENT_ID=okx_eea:linear_perpetual:ADA:USDT:USDT:ada-usdt-swap
CAP23_HISTORICAL_SELECTION_RANKING_SNAPSHOT_ID=pfr_0f8f19329bd8de687457fab0
SNAPSHOT_IDENTITY_JOIN=NOT_PROVEN_IDENTICAL
SNAPSHOT_IDENTITY_JOIN_EPISTEMIC_CLASS=OPEN_OR_CONTRADICTORY
INSTRUMENT_COUNT=20
```

Cap 2.3 remains the sole productive selection owner. The validation universe
is the Cap 2.2 evidence ranking snapshot's 20 ranked `ELIGIBLE` candidates,
which Cap 2.3 is defined to consume as Top-20 candidate context. This persist
does **not** create a second universe owner.

The Cap 2.3 historical selection snapshot id `pfr_0f8f19329bd8de687457fab0`
is **not** proven identical to Cap 2.2 evidence id `pfr_evidence_cap22_v1`.
That join remains `OPEN_OR_CONTRADICTORY` and is not normalized away. The
historical Cap 2.3 selected instrument is a member of the consumed Cap 2.2
ranked set.

### 3.2 BAND_INPUT_PROVENANCE

```text
BAND_FIELD_OWNER=trading.master_v2.double_play_state.RuntimeScopeState.current_hysteresis_band
BAND_PRODUCER=trading.master_v2.double_play_state.update_dynamic_boundaries
OQ_C1_MAPPING=up_distance = current_hysteresis_band
OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND=ABSENT_ON_ORIGIN_MAIN
BAND_SAMPLE_CLASS=FORMULA_VALID_BAND_NOT_PER_INSTRUMENT_PRODUCTIVE_SNAPSHOT
BAND_SAMPLE_OWNER=src/ops/derive_scope_event_distances_v1/golden_vectors_v1.py
GOLDEN_VECTORS_ARE_FORMULA_VECTORS_NOT_INSTRUMENT_UNIVERSE=true
SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=false
HYSTERESIS_MULTIPLIER_USED=false
```

No origin/main `RuntimeScopeState.current_hysteresis_band` snapshot was found
for the Cap 2.3-selectable Cap 2.2 instruments. This persist does **not**
invent those observed pairs.

Numeric band samples are the already-adjudicated formula golden valid vectors.
They are formula vectors, not an instrument universe, and not productive band
authority. The cartesian (selectable instrument identity × formula-valid band)
proves the unbound function consumes no `instrument_id`.

Cap 6.2 `loaded_runtime_scope.current_hysteresis_band=50.0` on
`ETH-USD_UM_XPERP-310404` is a field-owner exemplar only. That instrument is
**not** in the Cap 2.3 selectable set and is not used as a productive sample
for a Cap 2.3 instrument.

### 3.3 PASS_FAIL_CRITERIA (pre-metadata-gate only)

PASS recorded for every sampled valid band:

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
VALIDATION_TEST_OWNER=tests/ops/test_cap63_dynamic_derivation_cross_instrument_validation_v1.py
VALIDATION_EVIDENCE_PATH=evidence/ops/cap63_dynamic_derivation_cross_instrument_validation_v1/
SAMPLE_COUNT=120
INSTRUMENT_COUNT=20
VALID_BAND_SAMPLE_COUNT=6
```

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
OD2_ARMED_RESIDUAL=OPEN
OD2_LAST_STEP=KEEP_BOUND_DESTINATION_PREFIX
```

## 6. Residuals / later gates that remain OPEN

Class: `OPEN`.

```text
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
METADATA_GATE_CONSUMED=false
DERIVATION_SEAM_STATUS=UNBOUND
ATOMIC_RETIRE_BIND_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
DUAL_ENVELOPE_WP=NOT_STARTED
OD2_ARMED_RESIDUAL=OPEN
OBSERVED_PER_INSTRUMENT_RUNTIME_SCOPE_STATE_BAND=ABSENT_ON_ORIGIN_MAIN
SNAPSHOT_IDENTITY_JOIN=NOT_PROVEN_IDENTICAL
```

Tick/lot/ctVal/price-scale remains a **separate later** `AUTHORITY_MISSING`
gate and is **not consumed** by this validation.

## 7. Machine markers

```text
MARKER: CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1_EXISTS
MARKER: CROSS_INSTRUMENT_VALIDATION_PERFORMED=true
MARKER: VALIDATION_PROTOCOL_CONFORMANT=true
MARKER: VALIDATION_UNIVERSE_FROM_EXISTING_AUTHORITY=true
MARKER: BAND_PROVENANCE_VALID=true
MARKER: OQ_C1_PASS=true
MARKER: OQ_C2_PASS=true
MARKER: FORMULA_UNCHANGED=true
MARKER: RATIOS_UNCHANGED=true
MARKER: UNAUTHORIZED_FLOOR_OR_CLAMP=false
MARKER: METADATA_GATE_CONSUMED=false
MARKER: TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MARKER: MODEL_C_BOUND=false
MARKER: DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MARKER: THIS_VALIDATION_DEFINES_NO_INSTRUMENT_LIST=true
MARKER: SELECTION_OWNER=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
MARKER: BAND_FIELD_OWNER=RuntimeScopeState.current_hysteresis_band
MARKER: BAND_SAMPLE_CLASS=FORMULA_VALID_BAND_NOT_PER_INSTRUMENT_PRODUCTIVE_SNAPSHOT
MARKER: SYNTHETIC_BAND_SET_AS_PRODUCTIVE_AUTHORITY=false
MARKER: EVIDENCE_AUTHORITY_EFFECT=NONE
MARKER: LIVE_AUTHORIZED=false
MARKER: MAX_POSITIONS=1
```

## 8. STOP conditions

Stop immediately if this file is treated as:

1. MODEL_C runtime bind or Cap 6.3 generator-input retirement
2. tick / lot / ctVal / price-scale / quantization / rounding authority
3. observed per-instrument productive `RuntimeScopeState` band snapshots
4. a proven identity join of Cap 2.2 evidence ranking id and Cap 2.3
   historical ranking snapshot id
5. Cap 23 / Cap 24 / TOP-20 / SSF rewire
6. productive Dual Envelope numeric cutover
7. orientation, SideState, Neutral-Start, or OD2 ARMED mutation
8. Testnet / Canary / Live, orders, credentials, or venue POST

## 9. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  Tick/lot/ctVal/price-scale metadata remains AUTHORITY_MISSING and is not
  consumed. MODEL_C runtime bind remains unauthorized. Dual-Envelope WP
  remains NOT_STARTED. Do not start those gates from this persist.
EXACT_NEXT_OWNER_GO_TOKEN=NOT_MINTED
NEXT_NAMED_OPEN_GATE=TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY_MISSING
NEXT_NAMED_OPEN_GATE_IS_NOT_AN_OWNER_GO_TOKEN=true
HARD_STOP_AFTER_THIS_PERSIST=true
NEXT_OWNER_GO_CONSUMED=true
TOKEN_RENAMED=false
```
