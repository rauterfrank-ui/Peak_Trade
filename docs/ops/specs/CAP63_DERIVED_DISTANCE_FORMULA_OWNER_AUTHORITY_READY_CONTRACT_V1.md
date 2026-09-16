---
title: "Cap 6.3 Derived Distance Formula Owner Authority-Ready Contract v1"
status: "FORMULA_OWNER_AUTHORITY_READY_CONTRACT_PERSISTED_DOCS_ONLY"
owner: "ops"
last_updated: "2026-09-16"
docs_token: "DOCS_TOKEN_CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1"
---

# Cap 6.3 Derived Distance Formula Owner Authority-Ready Contract v1

Canonical persist of the MODEL_C derived-distance **formula/producer identity**
under `OWNER_GO_BOUNDED_CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1`.

Semantic authority for this persist lives in Master Runbook §9.2.2.
This file is the decision/contract record and navigation twin. It is **not**
a second numeric owner, **not** a runtime bind, and **not** a freeze-exception.

```text
DOCUMENT_CLASS=FORMULA_OWNER_AUTHORITY_READY_CONTRACT_DOCS_ONLY
OWNER_GO=OWNER_GO_BOUNDED_CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_CLASS=R1_OFFLINE_DOCS_ONLY
EXPECTED_ORIGIN_MAIN=5b74e20f99db17fcaf9bcf386c3509cef2919864
PARENT_UNIT_CLASS_DECISION=docs/ops/specs/CAP63_DISTANCE_UNIT_CLASS_AND_VALUE_SCOPE_OWNER_DECISION_V1.md
PARENT_MODEL_C_ARCHITECTURE=docs/ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md
PARENT_MODEL_C_FORMULA_ADJUDICATION=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## 1. Epistemic class separation

```text
CANONICAL_AUTHORITY=MASTER_RUNBOOK_§9.2.2_PLUS_THIS_CONTRACT
RAW_FORENSIC_EVIDENCE=SECTION_3_CURRENT_MODEL_B
ALREADY_ADJUDICATED=SECTION_4_TARGET_MAPPING_OQ_C1_C2
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=SECTION_6_RESIDUALS
CONFLICTED=NONE
```

This persist makes the **target formula/producer identity authority-ready as a
contract**. It does **not** authorize runtime formula use.

```text
FORMULA_OWNER_AUTHORITY_READY_CONTRACT_PERSISTED=true
MODEL_C_FORMULA_AUTHORIZED=false
DERIVED_DISTANCE_FORMULA_AUTHORIZED=false
DERIVED_DISTANCE_PRODUCER_AUTHORIZED=false
DERIVATION_RUNTIME_BIND_AUTHORIZED=false
MODEL_C_BOUND=false
FREEZE_EXCEPTION_AUTHORIZED=false
THRESHOLD_OR_DISTANCE_MUTATION_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

## 2. Explicit split: CURRENT MODEL_B vs TARGET MODEL_C

### CURRENT productive numeric owner (unchanged)

Class: `CANONICAL_AUTHORITY` for CURRENT; `RAW_FORENSIC_EVIDENCE` for hosts.

```text
CURRENT_MODEL=MODEL_B
CURRENT_GENERATOR_DISTANCE_OWNER=CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1
CURRENT_NUMERIC_SSOT=config/ops/canonical_decision_runtime_config_v1.toml
CURRENT_LOADER=src/ops/decision_config_ownership_and_consumer_closure_v1/config_loader_v1.py
CURRENT_ALIASES=CANONICAL_UP_DISTANCE / CANONICAL_ADVERSE_EXIT_DISTANCE / CANONICAL_REVERSAL_DISTANCE
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
confirmation_epochs=2
CAP63_NUMERIC_VALUES_REINTERPRETED_AS_DYNAMICALLY_DERIVED=false
```

Frozen `200.0` / `80.0` / `120.0` remain the CURRENT productive generator
inputs. They are **not** retroactively dynamically-derived. This contract does
**not** change those values.

### TARGET derived producer (docs-only identity; unimplemented)

Class: `ALREADY_ADJUDICATED` mapping + `CANONICAL_AUTHORITY` for identity.
Not a runtime owner.

```text
TARGET_MODEL=MODEL_C
TARGET_FORMULA_OWNER=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
TARGET_FORMULA_OWNER_AUTHORITY_READY_CONTRACT=THIS_FILE
TARGET_DERIVED_PRODUCER_IDENTITY=derive_scope_event_distances_v1
TARGET_DERIVED_PRODUCER_STATUS=UNIMPLEMENTED
TARGET_DERIVATION_SEAM_STATUS=UNBOUND
TARGET_STATE_OWNER=trading.master_v2.double_play_state.RuntimeScopeState
TARGET_ANCHOR_OWNER=trading.master_v2.double_play_state.update_dynamic_boundaries.anchor_price
TARGET_BAND_OWNER=trading.master_v2.double_play_state.RuntimeScopeState.current_hysteresis_band
```

`current_hysteresis_band` is the proven trailing-band field written by
`update_dynamic_boundaries`. It is **not** yet a productive switch-event
distance producer. This persist does **not** make it one.

## 3. CURRENT MODEL_B producer → consumer (forensic; not rewritten)

Class: `RAW_FORENSIC_EVIDENCE`.

Productive generator SSOT remains Cap 6.3 TOML. Productive hosts pass those
frozen distances into
`run_integrated_offline_trading_logic_replay_v1`, which forwards
`inp.up_distance` / `inp.adverse_exit_distance` / `inp.reversal_distance`
into `generate_deterministic_scope_event` after `update_dynamic_boundaries`.
No derivation function is called.

Cap 6.5 profit-protection remains a separate owner
(`FROZEN_PROFIT_PROTECTION_DISTANCE=200.0`). Numeric coincidence with switch
`up_distance=200.0` is not shared authority.

`min_scope_band=50.0` remains `MIN_SCOPE_BAND_OWNER=NOT_CAP63`.

Research 100 bps and scenario `_distance_triplet_from_scope_v0` remain
non-productive / non-MODEL_C. They are not promoted by this persist.

## 4. TARGET mapping (already adjudicated; no new formula)

Class: `ALREADY_ADJUDICATED` from
`MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1` OQ-C1 / OQ-C2.

Intended pure function, **unbound** and **unimplemented**:

```text
FUNCTION_NAME=derive_scope_event_distances_v1
FUNCTION_STATUS=UNIMPLEMENTED
OQ-C1_MAPPING=
  up_distance = current_hysteresis_band
OQ-C2_MAPPING=
  adverse_exit_distance = up_distance * (80.0 / 200.0)
  reversal_distance     = up_distance * (120.0 / 200.0)
OQ-C2_CAP63_RATIOS_CONFIRMED=
  80 / 200 = 0.4
  120 / 200 = 0.6
SCALE_OWNER_WHEN_LATER_BOUND=DERIVED_UP_DISTANCE_FROM_SCOPE_SSOT
RATIO_PROVENANCE=CAP_6_3_FROZEN_RATIO_BASELINE
HYSTERESIS_MULTIPLIER_USED=false
```

Fail-closed input/output gates already recorded in the formula adjudication
remain the target gates. This persist does **not** add floors, clamps, silent
`1.0` invention, Cap-6.3 fallback, or new numeric targets.

Rejected as MODEL_C mapping (already rejected; still rejected):

- scenario `{band, 0.8*band, 2.0*band}` plus `max(..., 1.0)`
- research ratios `0.5` / `0.75`
- copying frozen `200` / `80` / `120` as the derived scale
- `hysteresis_multiplier`
- MODEL_A `transition_state` price-read of `current_*_boundary`

Not derived:

```text
confirmation_epochs=2
CONFIRMATION_EPOCHS_NOT_DERIVED_FROM_BAND=true
SWITCH_OWNER_REMAINS_TRANSITION_STATE=true
TRANSITION_STATE_MUST_NOT_READ_BOUNDARY_FIELDS_AS_PRICE_THRESHOLD=true
```

## 5. Producer / seam identity (authority-ready; unimplemented / unbound)

Class: `CANONICAL_AUTHORITY` for **identity and location only**.

```text
TARGET_DERIVED_PRODUCER=derive_scope_event_distances_v1
TARGET_DERIVED_PRODUCER_PACKAGE=UNIMPLEMENTED_NO_SRC_OWNER
TARGET_DERIVATION_SEAM=
  update_dynamic_boundaries
  → runtime_scope_pre / trailing_anchor_used
  → [UNBOUND derive_scope_event_distances_v1]
  → generate_deterministic_scope_event
HOST_WHEN_LATER_BOUND=
  run_integrated_offline_trading_logic_replay_v1
  after runtime_scope_pre / trailing_anchor_used
  before the generator call
SEAM_MUST_NOT_EXIST_IN_RUNTIME_UNTIL_SEPARATE_RUNTIME_BIND_GO=true
NO_SECOND_RUNTIME_OWNER_NOW=true
NO_SECOND_RUNTIME_OWNER_AFTER_BIND=true
```

Until a later runtime-bind GO:

- the function **must not** exist in productive runtime
- the seam **must not** exist in productive runtime
- productive hosts continue to pass Cap 6.3 frozen distances
- this contract is **not** a second productive distance owner

Not authorized as seams (already forbidden by the parent MODEL_C contract):

- `transition_state`
- `step_switch_gate`
- silent mutation of Cap 6.3 TOML values
- scenario `_distance_triplet_from_scope_v0`

## 6. Residuals that remain OPEN

Class: `OPEN`. This persist does **not** close them and does **not** invent
owners, protocols, or values.

```text
CAP62_DIGEST_STATUS=OWNED
CAP65_ADVERSE_STATUS=OWNED
CAP62_CAP65_RESIDUAL_OWNER_CONTRACT=
  docs/ops/specs/CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md
  Master Runbook §9.2.3
CAP62_DIGEST_POST_RETIREMENT_SEMANTICS=
  Cap 6.2 digest surface remains Cap 6.2; material retargets to
  derive_scope_event_distances_v1 plus OQ-C2 policy identity;
  not retired Cap 6.3 generator numerics; not cycle-varying floats.
CAP65_ADVERSE_POST_RETIREMENT_SEMANTICS=
  Cap 6.5 remains consumer of derived OQ-C2 adverse; must not become
  an own frozen 80.0 owner; alias of Cap 6.3 retires in atomic cutover.
EXIT_POLICY_CONFIG_DIGEST_POST_RETIREMENT_SEMANTICS=
  adverse plus embedded Cap 6.3 digest retarget; profit-protection and
  time-hold remain Cap 6.5 own material.

CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
CROSS_INSTRUMENT_VALIDATION_PERFORMED=false
CROSS_INSTRUMENT_VALIDATION_PROTOCOL_OWNER=AUTHORITY_MISSING
TICK_LOT_CTVAL_PRICE_SCALE_METADATA_AUTHORITY=AUTHORITY_MISSING
```

Cap-6.2 digest and Cap-6.5 adverse residuals are owned in
[`CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md`](CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md).
That persist does **not** authorize freeze-exception or runtime bind.

Cross-instrument validation of derived-distance semantics is a **separate**
later Owner-GO **before** runtime bind. It is **not** a Cap-23 / Cap-24
selection rewire. Cap 23 remains sole productive selection owner. This persist
does not ratify an instrument set, price-scale table, tick/lot/ctVal schema,
or derived output ranges.

## 7. Later migration boundary (not authorized now)

Class: `ALREADY_ADJUDICATED` policy (OQ-C3 / OQ-C6) recorded as the later
bind/retire boundary. Not executed here.

```text
ATOMIC_RETIRE_AND_BIND_REQUIRED=true
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

When (and only when) a later freeze-exception GO **and** a later runtime-bind
GO are both granted and proven, Cap 6.3 `up_distance` /
`adverse_exit_distance` / `reversal_distance` retire as **generator inputs**
in the same atomic cutover that binds `derive_scope_event_distances_v1` as
the sole generator-distance authority. Hosts that currently pass Cap 6.3
aliases, Cap 6.2 digest material, parity pins, and expected-value guards must
cut over in that same atomic set. Missing derived output is fail-closed.
Silent Cap 6.3 fallback is forbidden.

Invariants that must survive that later cutover (already proven / required
now; not changed here):

- deterministic replay / parity
- no silent fallback (§9.3)
- one authority per runtime value
- restart reconstruction / digest fail-closed
- decision provenance
- fail-closed missing / invalid / stale / conflict
- nested adverse geometry (`adverse < up`, `adverse <= reversal`, `hard_max_*`)
- switch owner remains `transition_state`
- PR `#6270` untouched

OQ-C4 research same-derivation at later productive bind remains a later GO.
Research rewrite is **not** authorized here.

## 8. Explicit non-authorizations

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
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
VENUE_POST_AUTHORIZED=false
PERMIT_ENVELOPE_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
TRADING_LOGIC_CHANGED=false
DOUBLE_PLAY_SEMANTICS_CHANGED=false
```

## 9. Machine markers

```text
MARKER: CAP63_DERIVED_DISTANCE_FORMULA_OWNER_AUTHORITY_READY_CONTRACT_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: NON_AUTHORIZING_RUNTIME_POSTURE
MARKER: FORMULA_OWNER_AUTHORITY_READY_CONTRACT_PERSISTED=true
MARKER: MODEL_C_FORMULA_AUTHORIZED=false
MARKER: DERIVED_DISTANCE_FORMULA_AUTHORIZED=false
MARKER: DERIVED_DISTANCE_PRODUCER_STATUS=UNIMPLEMENTED
MARKER: DERIVATION_SEAM_STATUS=UNBOUND
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
MARKER: FREEZE_EXCEPTION_AUTHORIZED=false
MARKER: MODEL_C_BOUND=false
MARKER: CAP62_DIGEST_STATUS=OWNED
MARKER: CAP65_ADVERSE_STATUS=OWNED
MARKER: CROSS_INSTRUMENT_VALIDATION_STATUS=NOT_RATIFIED_PENDING_SEPARATE_VALIDATION
MARKER: ATOMIC_RETIRE_AND_BIND_REQUIRED=true
MARKER: LIVE_AUTHORIZED=false
MARKER: MAX_POSITIONS=1
```

## 10. STOP conditions

Stop immediately if this file is treated as:

1. `MODEL_C_FORMULA_AUTHORIZED=true` or runtime formula bind
2. implementation of `derive_scope_event_distances_v1` or the Integrated Replay seam
3. freeze-exception for Cap 6.2 / 6.3 / 6.5
4. mutation of frozen `200.0` / `80.0` / `120.0`
5. Cap 6.3 fallback, clamp to frozen numbers, or a new floor
6. Cap-23 / Cap-24 selection rewire
7. research BPS rewrite or Cap 6.5 profit-protection rewrite
8. a second productive distance owner
9. closure of cross-instrument validation (Cap-6.2 digest and Cap-6.5 adverse
   residual owners are persisted separately in §9.2.3; this file must not
   be treated as that persist)
10. Live / Testnet / orders / credentials / venue POST

## 11. Next authority boundary

```text
NEXT_BOUNDED_WORKPACKAGE=
  Freeze-exception authority is persisted in Master Runbook §9.2.5.
  Pure derivation function plus golden vectors are persisted in
  Master Runbook §9.2.6 (implemented unbound; not producer; not runtime bind).
  Cross-instrument derived-distance validation remains a later separate
  GO before runtime bind.
EXACT_NEXT_OWNER_GO_TOKEN=OWNER_GO_BOUNDED_CAP63_DYNAMIC_DERIVATION_CROSS_INSTRUMENT_VALIDATION_V1
HARD_STOP_AFTER_THIS_PERSIST=true
```
