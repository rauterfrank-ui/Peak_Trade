---
title: "Cap 6.3 Dynamic Derivation Freeze-Exception Preconditions v1"
status: "FREEZE_EXCEPTION_PRECONDITIONS_CONTRACT_PERSISTED_DOCS_ONLY"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1"
---

# Cap 6.3 Dynamic Derivation Freeze-Exception Preconditions v1

Canonical persist of freeze-exception **preconditions** for later MODEL_C
derivation, under
`OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.4.
This file is the decision/contract record and navigation twin. It is **not**
a freeze-exception, **not** a runtime bind, **not** a formula authorization,
and **not** a numeric mutation.

```text
DOCUMENT_CLASS=FREEZE_EXCEPTION_PRECONDITIONS_CONTRACT_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
EXPECTED_ORIGIN_MAIN=a99ebe99dc09044ba78edddb7f6786df95accec6
PARENT_RESIDUAL_OWNER_CONTRACT=docs/ops/specs/CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md
PARENT_FORMULA_OWNER_CONTRACT=docs/ops/specs/CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1.md
PARENT_UNIT_CLASS_DECISION=docs/ops/specs/CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1.md
PARENT_MODEL_C_ARCHITECTURE=docs/ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
PARENT_DUAL_USE_SPLIT=docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md
PARENT_DIRECTIONAL_MAPPING=docs/ops/specs/DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.4_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=SECTION_3_CURRENT_FREEZE_SURFACES
ALREADY_ADJUDICATED=SECTION_4_PRECONDITION_GRAPH_AND_SECTION_5_LATER_EXCEPTION_SCOPE
NAVIGATION_ONLY=MAP_OF_TRUTH_AND_ATLAS
HISTORICAL_STATE=DIRECTIONAL_MAPPING_OQ_CENSUS_5_PRE_BIND_BLOCKER
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_8_LATER_GATES
CONFLICTED=NONE
OWNER_CHOICE_REQUIRED=false
```

This persist makes freeze-exception **preconditions** authority-ready as a
contract. It does **not** grant the exception, implement derivation, bind
MODEL_C, or mutate frozen numbers.

```text
FREEZE_EXCEPTION_PRECONDITIONS_CONTRACT_PERSISTED=true
FREEZE_EXCEPTION_PRECONDITIONS_MET=true
FREEZE_EXCEPTION_AUTHORIZED=false
FREEZE_EXCEPTION_ACTUALLY_PERSISTED=false
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

## 2. Explicit split A / B / C / D / E

Class: `CANONICAL_AUTHORITY`. This GO is **A only**.

```text
A_THIS_GO=FREEZE_EXCEPTION_PRECONDITIONS_CONTRACT
B_NOT_THIS_GO=ACTUAL_FREEZE_EXCEPTION_AUTHORIZATION_AND_PERSIST
C_NOT_THIS_GO=PURE_FUNCTION_AND_GOLDEN_VECTORS
D_NOT_THIS_GO=CROSS_INSTRUMENT_AND_PRICE_SCALE_VALIDATION
E_NOT_THIS_GO=RUNTIME_BIND_AND_ATOMIC_RETIRE_BIND
```

| Layer | Status after this persist | Owner of later GO |
|-------|---------------------------|-------------------|
| A Preconditions | `PERSISTED` / `MET` | this contract / Master Runbook §9.2.4 |
| B Freeze-exception | `UNAUTHORIZED` / `NOT_PERSISTED` | `OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1` (same workpackage as `LATER_REQUIRED_GO=MODEL_C_FREEZE_EXCEPTION`) |
| C Pure function + golden vectors | later; not authorized | `PURE_DERIVATION_FUNCTION_AND_GOLDEN_VECTORS` |
| D Cross-instrument / price-scale | later; `AUTHORITY_MISSING` | separate GO **before runtime bind**, not a freeze-exception precondition |
| E Runtime bind + atomic retire+bind | later; not authorized | `MODEL_C_RUNTIME_BIND` |

SSOT order after residual persist (Master Runbook §9.2.3, formula-owner
§11, residual-owner §7/§10): freeze-exception is the earliest unresolved
MODEL_C dependency; cross-instrument remains a separate later gate before
**runtime bind**. Derived architecture text that previously said
"before any freeze-exception GO" is navigation drift against that SSOT and
is corrected by this persist to "before runtime bind".

## 3. CURRENT freeze / authority census

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

### 3.1 Surfaces a later freeze-exception must name (otherwise derivation cannot bind without silent bypass)

These surfaces currently pin Cap 6.3 generator-input distances. A later
exception (B) must name them so MODEL_C can later retire those generator
inputs without silently circumventing Cap 6.2 / 6.3 / 6.5 freeze rules.

| Surface | Forensic pin (origin/main `a99ebe99`) | Later exception role |
|---------|----------------------------------------|----------------------|
| Cap 6.3 numeric SSOT | `config/ops/canonical_decision_runtime_config_v1.toml` `up_distance` / `adverse_exit_distance` / `reversal_distance` | Exception to treat these as **retireable generator inputs**, not as perpetual Dual Envelope SSOT |
| Cap 6.3 capability freeze | `docs/ops/CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md` `EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true` | Exception to that invariant **for the three generator distances only**, after B+E; not a silent TOML rewrite now |
| Cap 6.3 expected-value / parity pins | `src/ops/decision_config_ownership_and_consumer_closure_v1/constants_v1.py` `EXPECTED_UP_DISTANCE=200.0`; `parity_v1.py` `CANONICAL_UP_DISTANCE == EXPECTED_UP_DISTANCE` | Later retarget/retire of generator expected-value guards; not now |
| Cap 6.3 digest payload | Cap 6.3 `values_payload` hashes `confirmation_epochs` plus the three generator distances | Distances retarget at E; `confirmation_epochs` stays Cap 6.3 |
| Cap 6.2 persistence freeze text | `docs/ops/specs/CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1.md` "No change to `up_distance=200.0` / `adverse_exit_distance=80.0` / `reversal_distance=120.0`" | Exception to that freeze for generator-input aliases only |
| Cap 6.2 FROZEN_* aliases | `src/ops/dynamic_scope_persistence_binding_v1/constants_v1.py` aliases `CANONICAL_*` as `FROZEN_*`; `parity_v1.py` asserts `200.0` / `80.0` / `120.0` | Exception to retire those aliases at E in favor of derived-producer policy identity (§9.2.3) |
| Cap 6.2 host defaults | `host_binding_v1.py` defaults `up_distance=FROZEN_UP_DISTANCE` (and adverse/reversal) | Exception to stop defaulting productive host distances from retired Cap 6.3 generator inputs |
| Cap 6.2 digest CURRENT material | `dynamic_scope_config_digest_v1` currently hashes Cap 6.3 generator distances | Post-retirement material already owned in §9.2.3; exception is required before E may retarget |
| Cap 6.5 adverse consumer alias | `src/ops/exit_policy_producer_binding_v1/constants_v1.py` `FROZEN_ADVERSE_EXIT_DISTANCE = float(CANONICAL_ADVERSE_EXIT_DISTANCE)`; `parity_v1.py` asserts `80.0` | Exception to **retarget the consumer**, not to mint a Cap 6.5 own frozen `80.0` |
| Cap 6.5 exit-policy digest CURRENT material | `exit_policy_config_digest_v1` hashes adverse + embedded Cap 6.3 digest | Retarget with §9.2.3; exception required before E |
| Tests pinning Dual Envelope | `tests/ops/test_decision_config_ownership_and_consumer_closure_v1.py`; `tests/ops/test_dynamic_scope_persistence_binding_v1.py`; `tests/ops/test_exit_policy_producer_binding_v1.py` | Later test-owner retarget at B/C/E as authorized; not this GO |

### 3.2 Freeze authority that remains unchanged (not inside later exception B)

| Surface | Why it stays frozen |
|---------|---------------------|
| Cap 6.5 profit-protection `FROZEN_PROFIT_PROTECTION_DISTANCE=200.0` | OQ-C5 identity split; own Cap 6.5 owner; numeric coincidence with switch-event `up_distance` is not dual-use collapse |
| `confirmation_epochs=2` | Cap 6.3 runtime config; not derived from band |
| `min_scope_band=50.0` | `MIN_SCOPE_BAND_OWNER=NOT_CAP63` |
| `MAX_POSITIONS=1` | unchanged |
| Directional mapping runtime-bound polarity / PENDING orientation | Mapping contract, not a distance freeze; already runtime-bound |
| MODEL_B Dual Envelope as CURRENT until E | B authorizes a later exception; it does not itself mutate CURRENT numbers |

```text
PROFIT_PROTECTION_IDENTITY_SPLIT_MUST_REMAIN=true
PROFIT_PROTECTION_MUST_NOT_FOLLOW_DERIVED_UP_DISTANCE=true
confirmation_epochs_REMAINS_CAP63=true
MIN_SCOPE_BAND_KEPT_SEPARATE=true
DIRECTIONAL_MAPPING_IS_NOT_A_DISTANCE_FREEZE_EXCEPTION_SURFACE=true
```

## 4. Residual dependency / admission graph (preconditions)

Class: `ALREADY_ADJUDICATED`. These are **entry criteria** for later B.
They are **met** on origin/main `a99ebe99` plus this persist. Meeting them
does not grant B.

```text
PRECONDITION_GRAPH_1_UNIT_CLASS_PERSISTED=true
PRECONDITION_GRAPH_2_FORMULA_IDENTITY_PERSISTED=true
PRECONDITION_GRAPH_3_DUAL_USE_SPLIT_IMPLEMENTED=true
PRECONDITION_GRAPH_4_CAP62_DIGEST_OWNER_PERSISTED=true
PRECONDITION_GRAPH_5_CAP65_ADVERSE_OWNER_PERSISTED=true
PRECONDITION_GRAPH_DIRECTIONAL_MAPPING_RUNTIME_BOUND=true
PRECONDITION_GRAPH_THIS_PRECONDITIONS_CONTRACT_PERSISTED=true
ANCHOR_OR_PIPELINE_TRAILING_RUNTIME_REPAIR_REQUIRED_BEFORE_FREEZE_EXCEPTION=false
HARDENING_V2_LOCAL_DISTANCE_LITERALS_RESIDUAL_AFTER_CAP63=false
```

| Precondition | Evidence | Status |
|-----------|----------|--------|
| Cap 6.3 unit class / value-scope Owner decision | Master Runbook §9.2.1 | `MET` |
| Formula/producer identity contract | Master Runbook §9.2.2 | `MET` (`FORMULA_OWNER_AUTHORIZED=false`) |
| Dual-use profit-protection split | `MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md`; Cap 6.5 own `200.0` | `MET` |
| Cap 6.2 digest + Cap 6.5 adverse residual owners | Master Runbook §9.2.3 | `MET` |
| Directional mapping contract repair runtime-bound | `DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md` `CONTRACT_REPAIR_RUNTIME_BOUND=true`; OQ-CENSUS-5 blocker was **mapping** runtime bind, now satisfied | `MET` |
| ARMED residual / last_active_side | `ANCHOR_OR_PIPELINE_TRAILING_RUNTIME_REPAIR_REQUIRED_BEFORE_FREEZE_EXCEPTION=false` | **not** a freeze-exception precondition |
| This preconditions contract | Master Runbook §9.2.4 / this file | `MET` after this persist |

Historical note (`HISTORICAL_STATE`, not CURRENT blocker): directional
mapping OQ-CENSUS-5 said freeze-exception / MODEL_C runtime bind remain
blocked until **that mapping contract** is runtime-bound. That mapping
runtime bind is recorded. The marker
`OQ_CENSUS_5_ADJUDICATED_FREEZE_EXCEPTION_BLOCKED_UNTIL_RUNTIME_BIND`
must not be read as requiring MODEL_C runtime bind (layer E) before B.

## 5. Later freeze-exception (B) — scope, entry, exit

Class: `ALREADY_ADJUDICATED` target policy for **later** B. This section
does **not** authorize or persist B.

### 5.1 What later B would except (narrow)

Later B, if separately Owner-authorized, would persist an explicit
exception to:

1. Cap 6.3 freeze on generator-input distances `200.0` / `80.0` / `120.0`
2. Cap 6.2 freeze/parity on the same three distances as persistence aliases
3. Cap 6.5 **adverse consumer alias** freeze (`FROZEN_ADVERSE_EXIT_DISTANCE`
   alias of Cap 6.3 `80.0`), so E may retarget the consumer to derived
   OQ-C2 adverse

Later B would **not** except:

- Cap 6.5 profit-protection `200.0`
- `confirmation_epochs`
- `min_scope_band`
- CURRENT numeric mutation in the B persist itself
  (`EFFECTIVE_NUMERIC_VALUES_UNCHANGED` remains true until E)

```text
LATER_B_EXCEPTS_CAP63_GENERATOR_INPUT_FREEZE=true
LATER_B_EXCEPTS_CAP62_GENERATOR_ALIAS_FREEZE=true
LATER_B_EXCEPTS_CAP65_ADVERSE_CONSUMER_ALIAS_FREEZE=true
LATER_B_EXCEPTS_CAP65_PROFIT_PROTECTION_FREEZE=false
LATER_B_MUTATES_CURRENT_NUMERICS=false
LATER_B_IMPLEMENTS_DERIVE_SCOPE_EVENT_DISTANCES_V1=false
LATER_B_BINDS_RUNTIME=false
LATER_B_AUTHORIZES_ATOMIC_RETIRE_BIND=false
```

### 5.2 Entry criteria for later B

B may be considered only if all of the following remain true:

```text
FREEZE_EXCEPTION_PRECONDITIONS_MET=true
CURRENT_CANONICAL_MODEL=MODEL_B
MODEL_C_BOUND=false
FORMULA_OWNER_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
DUAL_AUTHORITY_INTRODUCED=false
ZERO_AUTHORITY_INTRODUCED=false
CAP63_FALLBACK_INTRODUCED=false
PROFIT_PROTECTION_IDENTITY_SPLIT_MUST_REMAIN=true
```

Cross-instrument validation and price-scale metadata are **not** entry
criteria for B. They remain layer D, required before E.

### 5.3 Exit criteria for later B (what B itself must persist)

When a later B persist is closed, it must leave:

```text
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=true
FREEZE_EXCEPTION_ACTUALLY_PERSISTED=true
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MODEL_C_BOUND=false
FORMULA_OWNER_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
ATOMIC_RETIRE_BIND_AUTHORIZED=false
DUAL_AUTHORITY_FORBIDDEN=true
ZERO_AUTHORITY_FORBIDDEN=true
CAP63_GENERATOR_FALLBACK_FORBIDDEN=true
CLAMP_OR_FLOOR_DERIVED_DISTANCES_TO_200_80_120=FORBIDDEN
ATOMIC_RETIRE_AND_BIND_REQUIRED=true
```

B is necessary and not sufficient for generator-input retirement. OQ-C3
retirement happens only after **B and E**. Missing derived output remains
fail-closed. Silent Cap 6.3 fallback remains forbidden.

## 6. Atomic cutover invariants (not executed here)

Class: `ALREADY_ADJUDICATED` policy (OQ-C3 / OQ-C6 / formula-owner / residual
§5). Binding and retirement remain layer E.

```text
ATOMIC_RETIRE_AND_BIND_REQUIRED=true
ATOMIC_RETIRE_BIND_AUTHORIZED=false
DUAL_AUTHORITY_FORBIDDEN=true
ZERO_AUTHORITY_FORBIDDEN=true
CAP63_GENERATOR_FALLBACK_FORBIDDEN=true
CLAMP_OR_FLOOR_DERIVED_DISTANCES_TO_200_80_120=FORBIDDEN
PROFIT_PROTECTION_IDENTITY_SPLIT_MUST_REMAIN=true
PROFIT_PROTECTION_MUST_NOT_FOLLOW_DERIVED_UP_DISTANCE=true
confirmation_epochs_REMAINS_CAP63=true
MIN_SCOPE_BAND_KEPT_SEPARATE=true
MAX_POSITIONS=1
```

A freeze-exception that retired Cap 6.3 generator inputs without binding
`derive_scope_event_distances_v1` would be `ZERO_AUTHORITY`. Binding the
derived producer while leaving Cap 6.3 generator inputs live would be
`DUAL_AUTHORITY`. Using Cap 6.3 Dual Envelope as fallback after bind would
be `CAP63_FALLBACK`. All three remain forbidden.

## 7. Explicit non-authorizations

```text
CONFIG_MUTATION_AUTHORIZED=false
NUMERIC_MIGRATION_AUTHORIZED=false
SRC_RUNTIME_MUTATION_AUTHORIZED=false
MODEL_C_RUNTIME_BIND_AUTHORIZED=false
DERIVE_SCOPE_EVENT_DISTANCES_V1_IMPLEMENTATION_AUTHORIZED=false
DERIVATION_SEAM_IMPLEMENTATION_AUTHORIZED=false
FREEZE_EXCEPTION_AUTHORIZED=false
NORMALIZATION_JOIN_IMPLEMENTATION_AUTHORIZED=false
CAP23_SELECTION_REWIRE_AUTHORIZED=false
CAP24_BINDING_REWIRE_AUTHORIZED=false
RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
CAP65_OWN_FROZEN_ADVERSE_80_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
CROSS_INSTRUMENT_VALIDATION_AUTHORIZED=false
TICK_LOT_CTVAL_PRICE_SCALE_IMPLEMENTATION_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
PERMIT_ENVELOPE_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
```

## 8. Residuals / later gates that remain OPEN

Class: `OPEN`. This persist does **not** close them and does **not** pull
them into freeze-exception preconditions.

```text
CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=AUTHORITY_MISSING
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
FREEZE_EXCEPTION_AUTHORIZED=false
DERIVE_SCOPE_EVENT_DISTANCES_V1_STATUS=UNIMPLEMENTED
DERIVATION_SEAM_STATUS=UNBOUND
ATOMIC_RETIRE_BIND_AUTHORIZED=false
```

Cross-instrument validation of derived-distance semantics remains a
**separate** later Owner-GO **before runtime bind** (layer D). It is **not**
a Cap-23 / Cap-24 selection rewire and **not** an entry criterion for B.

Tick/lot/ctVal / price-scale metadata remains `AUTHORITY_MISSING` (layer D).

Pure derivation function + golden vectors remain layer C, after B.

Runtime bind + atomic retire+bind remain layer E.

## 9. Machine markers

```text
MARKER: CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: NON_AUTHORIZING_RUNTIME_POSTURE
MARKER: FREEZE_EXCEPTION_PRECONDITIONS_CONTRACT_PERSISTED=true
MARKER: FREEZE_EXCEPTION_PRECONDITIONS_MET=true
MARKER: FREEZE_EXCEPTION_AUTHORIZED=false
MARKER: FREEZE_EXCEPTION_ACTUALLY_PERSISTED=false
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

1. `FREEZE_EXCEPTION_AUTHORIZED=true` or `MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=true`
2. `MODEL_C_FORMULA_AUTHORIZED=true` or runtime formula bind
3. implementation of `derive_scope_event_distances_v1` or the Integrated Replay seam
4. mutation of frozen `200.0` / `80.0` / `120.0` / profit-protection `200.0`
5. Cap 6.3 fallback, clamp to frozen numbers, or a new floor
6. Cap-23 / Cap-24 selection rewire
7. research BPS rewrite or Cap 6.5 profit-protection rewrite
8. a Cap 6.5 own frozen `80.0` adverse owner
9. a second productive distance owner, dual authority, or zero authority
10. closure of cross-instrument validation or price-scale metadata
11. atomic retire+bind, Testnet / Canary / Live, orders, credentials, or venue POST

## 11. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  freeze-exception for Cap 6.2 / 6.3 generator-input freeze and Cap 6.5
  adverse consumer alias freeze remains later and unauthorized. This
  persist closed preconditions only. Cross-instrument derived-distance
  validation and tick/lot/ctVal price-scale metadata remain separate later
  gates before runtime bind. No derivation function, no seam, no atomic
  retire+bind.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1
LATER_REQUIRED_GO_ALIAS=MODEL_C_FREEZE_EXCEPTION
HARD_STOP_AFTER_THIS_PERSIST=true
NEXT_OWNER_GO_CONSUMED=false
```
