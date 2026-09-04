---
title: "Directional Mapping Contract Repair v1"
status: "ACTIVE"
owner: "ops"
last_updated: "2026-09-05"
docs_token: "DOCS_TOKEN_DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1"
---

# Directional Mapping Contract Repair v1

## 1. Purpose

Persist the Owner-granted **directional mapping contract** and
**blast-radius adjudication** under:

```text
OWNER_GO=PEAK_TRADE_OWNER_GO_DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1
OWNER_GO_STATUS=GRANTED_CONFIRMED
PERSIST_GO=PEAK_TRADE_OWNER_GO_DIRECTIONAL_MAPPING_CONTRACT_PERSIST_VALIDATE_AND_PR_V1
PERSIST_GO_STATUS=GRANTED_CONFIRMED
AUTHORIZED_SCOPE=DIRECTIONAL_MAPPING_CONTRACT_REPAIR_AND_BLAST_RADIUS_ADJUDICATION_ONLY
BOUND_ORIGIN_MAIN_SHA=415b3146867d8be1284105639a31bd2dc1e1ca2c
PARENT_CENSUS=docs/ops/specs/DIRECTIONAL_SCOPE_ANCHOR_AND_SIDE_SWITCH_SEMANTICS_CENSUS_V1.md
CONTRACT_RUNTIME_BOUND=false
```

This file records **target mapping policy** and **what a later runtime GO
must co-change**. It does **not** implement the repair, remap the
generator, change `transition_state`, change Entry/Exit, change anchors
or boundaries, bind MODEL_C, grant a freeze exception, modify PR `#6270`,
or authorize Live.

```text
DOCUMENT_CLASS=DOCS_ONLY_MAPPING_CONTRACT_AND_BLAST_RADIUS
PARALLEL_SSOT_CREATED=false
MAPPING_CONTRACT_ADJUDICATED=true
MAPPING_CONTRACT_RUNTIME_BOUND=false
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
MODEL_C_RUNTIME_BINDING_AUTHORIZED=false
ANCHOR_RUNTIME_CHANGE_AUTHORIZED=false
BOUNDARY_FORMULA_CHANGE_AUTHORIZED=false
TRANSITION_STATE_RUNTIME_CHANGE_AUTHORIZED=false
GENERATOR_RUNTIME_REMAP_AUTHORIZED=false
ENTRY_EXIT_RUNTIME_CHANGE_AUTHORIZED=false
PR_6270_MODIFICATION_AUTHORIZED=false
LIVE_MUTATION_AUTHORIZED=false
MODEL_B_REMAINS_PRODUCTIVE_BASELINE=true
CORE_LOGIC_CHANGE=false
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
```

Parent forensic census (separate persist; not a runtime owner):
see `PARENT_CENSUS` in §1. That sibling spec is **not** part of this PR.

OQ texts below are **verbatim** from that census §12.

## 2. Epistemic class separation

```text
CANONICAL_AUTHORITY=THIS_OWNER_GO_PLUS_CENSUS_PLUS_BOUND_ORIGIN_MAIN_CODE
FORENSIC_RAW_EVIDENCE=PARENT_CENSUS
ALREADY_ADJUDICATED_CONCLUSION=SECTION_4_AND_5
BLAST_RADIUS=SECTION_7
HISTORICAL_INTERMEDIATE=CURRENT_RUNTIME_MAPS_ON_ORIGIN_MAIN
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=RUNTIME_BIND_OF_THIS_CONTRACT
CONFLICTED=NONE_AFTER_THIS_ADJUDICATION
```

Current productive maps remain **HISTORICAL_INTERMEDIATE** until a later
runtime-bind GO. This file does not silently rewrite runtime.

## 2.1 Epistemic lanes (do not collapse)

```text
CURRENT_PRODUCTIVE_RUNTIME=origin/main maps and events (MODEL_B Dual Envelope)
OWNER_ADJUDICATED_TARGET=this contract §4–§6 (unbound)
KNOWN_MISMATCH=SHORT_ACTIVE continuation UPSCOPE currently starts Short→Long; PENDING generator orientation is destination-mirrored
AUTHORIZED_FUTURE_CHANGE=MINIMUM_ATOMIC_RUNTIME_REPAIR_SET after a separate runtime-bind GO
UNAUTHORIZED_CHANGE=ARMED last_active_side carry; freeze exception; MODEL_C bind; generator un-mirror; trailing-as-destination; PR #6270; Live
```

## 2.2 Core Bull / Bear directional invariants (adjudicated)

UPSCOPE / DOWNSCOPE are **relative regime** labels, not absolute
PRICE_UP / PRICE_DOWN names.

```text
BULL_LONG_FAVORABLE=PRICE_UP
BULL_LONG_ADVERSE=PRICE_DOWN
BULL_LONG_ACTIVE_ADVERSE_EDGE=LOWER
BULL_LONG_CONTINUATION=UPSCOPE
BULL_LONG_REVERSAL=DOWNSCOPE

BEAR_SHORT_FAVORABLE=PRICE_DOWN
BEAR_SHORT_ADVERSE=PRICE_UP
BEAR_SHORT_ACTIVE_ADVERSE_EDGE=UPPER
BEAR_SHORT_CONTINUATION=UPSCOPE
BEAR_SHORT_REVERSAL=DOWNSCOPE
```

```text
CURRENT_PRODUCTIVE_SHORT_TO_LONG_START_EVENT=UPSCOPE_CONFIRMED
TARGET_SHORT_TO_LONG_START_EVENT=DOWNSCOPE_CONFIRMED
TARGET_UNBOUND=true
PRODUCTIVE_RUNTIME_REMAINS_CURRENT_UNTIL_LATER_GO=true
```

## 3. Owner-GO bounds (this slice)

This slice **may**:

- adjudicate OQ-CENSUS-1..5 as mapping policy
- name CURRENT vs TARGET vs BOUND
- inventory blast radius for a later runtime-bind GO

This slice **must not**:

- edit `src/`, `config/`, or tests that change behavior
- change `transition_state`, `scope_direction_from_side_state_v1`,
  `_side_state_to_entry_exit_direction`, or `derive_active_side`
- add `last_active_side` (or any new `RuntimeScopeState` field)
- mutate Cap 6.2 / 6.3 / 6.5 numerics
- bind `derive_scope_event_distances_v1`
- touch `feat&#47;full-core-live-path-composition-root-v1` / PR `#6270`
- rewrite [FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md](FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md)
  in this slice (that file remains CURRENT; co-change is later and
  must move with runtime or it creates docs&#47;runtime drift)

## 4. OQ adjudication (verbatim questions; policy answers)

### OQ-CENSUS-1

```text
OQ_ID=OQ-CENSUS-1
OQ_TEXT_VERBATIM=Are generator SHORT UPSCOPE/DOWNSCOPE labels intentionally mirrored, or should they stay geometric to match transition_state and Manifest §6?
OQ_STATUS=ADJUDICATED_DOCS_ONLY
ADJUDICATED_TARGET_POLICY_NOT_RUNTIME_BOUND=true
```

**Adjudicated policy:** Generator SHORT **threshold math and
continuation label remain mirrored** (UPSCOPE = continuation of the
current `ScopeDirectionState`; proven by
`mirror_price_for_short` /
`test_long_short_mirror_structural_sequence`).

The **State Machine must consume the reversal label** while the
generator is SHORT-oriented:

```text
TARGET_SHORT_ACTIVE_STARTS_SHORT_TO_LONG_ON=DOWNSCOPE_CONFIRMED
CURRENT_SHORT_ACTIVE_STARTS_SHORT_TO_LONG_ON=UPSCOPE_CONFIRMED
```

Owner-BEAR: favorable downside must not switch; adverse upside must.
With mirrored generator math, adverse upside is `DOWNSCOPE_*`.
Current SM consumes `UPSCOPE_CONFIRMED` (continuation). That is the
repair target, not a generator geometry rewrite.

Rejected as this GO's repair: un-mirroring generator formulas
(would break the mirror test and Owner GLOBAL “spiegelbildliche
Distanzregel”).

Rejected as this GO's runtime: actually editing `transition_state`.

Neutral start **unchanged**:

```text
NEUTRAL_OBSERVE + UPSCOPE_CONFIRMED → LONG_ARMED
NEUTRAL_OBSERVE + DOWNSCOPE_CONFIRMED → SHORT_ARMED
LONG_ARMED + UPSCOPE_CONFIRMED → LONG_ACTIVE
```

`LONG_ARMED` is overloaded (neutral start **and** Short→Long terminal
arm). Terminal completion **keeps** `UPSCOPE_CONFIRMED` so neutral
start is not destroyed. See §5.

Manifest §6 prose “Bruch über die Boundary” is **geometric meaning**.
It is **not** identical to the `ScopeEvent` token `UPSCOPE_CONFIRMED`
under mirrored SHORT labels. Later docs co-change may note that
without rewriting Master Runbook SSOT path labels.

### OQ-CENSUS-2

```text
OQ_ID=OQ-CENSUS-2
OQ_TEXT_VERBATIM=Is trailing freeze on every non-ACTIVE SideState intended for the four-step pipeline?
OQ_STATUS=ADJUDICATED_DOCS_ONLY
```

**Adjudicated policy:** **Yes.** `derive_active_side` remains
LONG_ACTIVE / SHORT_ACTIVE only. Trailing freeze on the four-step
pipeline is intended. No later GO in this family may “fix” the stall
by trailing as the destination side during PENDING/BLOCKED/ARMED.

### OQ-CENSUS-3

```text
OQ_ID=OQ-CENSUS-3
OQ_TEXT_VERBATIM=Is implicit min/max reseed of leftover opposite-side anchor the intended post-switch reset (no explicit reseed in transition_state)?
OQ_STATUS=ADJUDICATED_DOCS_ONLY
```

**Adjudicated policy:** **Yes, as named semantics:**

```text
SIDE_SWITCH_ANCHOR_SEMANTICS=PRESERVE_THEN_IMPLICIT_REBASE_ON_FIRST_ACTIVE_TRAIL
```

`transition_state` does not write `anchor_price`. The POST-trail of the
cycle that first reaches opposite `*_ACTIVE` applies `min` (SHORT) or
`max` (LONG). Explicit reseed is **not** required before freeze
exception. CHOP / missing `volatility_estimate` leaves preserve-without-
rebase; that remain fail-closed, not a silent 1.0 invention.

This GO does **not** add an explicit reseed.

### OQ-CENSUS-4

```text
OQ_ID=OQ-CENSUS-4
OQ_TEXT_VERBATIM=Must the three SideState→direction maps remain distinct, or is a later GO allowed to unify them?
OQ_STATUS=ADJUDICATED_DOCS_ONLY
```

**Adjudicated policy:** **PARTIAL.**

| Map | Domain | Unification |
|-----|--------|-------------|
| `derive_active_side` | trailing ratchet | **Keep** (OQ-2) |
| `_side_state_to_entry_exit_direction` / `side_state_to_entry_exit_direction` | entry/exit armed-active-neutral | **Keep** as a consumer table (`*_BLOCKED` → NEUTRAL is real) |
| `scope_direction_from_side_state_v1` | generator orientation | **Repair target:** PENDING must follow **departing** ACTIVE side |

A later GO **may** introduce a structured projection. It **must not**
collapse Entry/Exit BLOCKED=NEUTRAL into trailing or generator enums.

**Hard constraint:** `LONG_ARMED` and `SHORT_ARMED` are **overloaded**
(neutral start vs pipeline terminal). A pure `SideState → ScopeDirectionState`
function **cannot** implement “hold departing ACTIVE until opposite
ACTIVE” for ARMED without extra carry (`last_active_side`). Adding that
field is **not** authorized here (Cap 6.2 persistence surface).

```text
RESIDUAL_AMBIGUITY=ARMED_REQUIRES_ADDITIONAL_HISTORY_SUCH_AS_LAST_ACTIVE_SIDE_IF_FULL_DEPARTING_AUTHORITY_IS_LATER_REQUIRED
LAST_ACTIVE_SIDE_BINDING_AUTHORIZED=false
ARMED_DIRECTION_RESIDUAL_AMBIGUITY=true
ARMED_STATE_OVERLOAD_PERSISTED=true
```

Do **not** invent a solution in this contract. ARMED is **not** part of
the minimum atomic runtime repair set.

Pure-`SideState` TARGET that **is** unambiguous:

```text
CURRENT: SWITCH_LONG_TO_SHORT_PENDING → SHORT
TARGET:  SWITCH_LONG_TO_SHORT_PENDING → LONG

CURRENT: SWITCH_SHORT_TO_LONG_PENDING → LONG
TARGET:  SWITCH_SHORT_TO_LONG_PENDING → SHORT
```

Residual after that TARGET (not closed by this contract’s later
pure-table repair): `SHORT_ARMED` / `LONG_ARMED` overload. Census
primary stall is PENDING; that is the high-leverage row.

### OQ-CENSUS-5

```text
OQ_ID=OQ-CENSUS-5
OQ_TEXT_VERBATIM=Does freeze-exception / MODEL_C runtime bind remain blocked until OQ-CENSUS-1 is adjudicated?
OQ_STATUS=ADJUDICATED_DOCS_ONLY
```

**Adjudicated policy:** **Yes, and stronger:** freeze-exception /
MODEL_C runtime bind remain blocked until **this mapping contract is
runtime-bound** (OQ-1 polarity **and** OQ-4 PENDING orientation).
Adjudicating the text here is **not** a runtime bind.

```text
MODEL_C_FREEZE_EXCEPTION_REMAINS_UNAUTHORIZED=true
THIS_ADJUDICATION_IS_NOT_A_RUNTIME_BIND=true
```

## 5. Target mapping (unbound)

Class: `ALREADY_ADJUDICATED_CONCLUSION`. Not consumed by runtime.

Vocabulary (mirrored generator, Owner GLOBAL):

```text
UPSCOPE_LABEL=CONTINUATION_OF_CURRENT_SCOPE_DIRECTION
DOWNSCOPE_LABEL=REVERSAL_OF_CURRENT_SCOPE_DIRECTION
LONG_GEOMETRIC_DOWN=DOWNSCOPE
SHORT_GEOMETRIC_UP=DOWNSCOPE
```

### 5.1 Trailing (unchanged)

`derive_active_side`: only `LONG_ACTIVE` → LONG, `SHORT_ACTIVE` → SHORT;
else NEUTRAL. Freeze intended.

### 5.2 Generator orientation TARGET (PENDING rows only)

| SideState | CURRENT `scope_direction_from_side_state_v1` | TARGET |
|-----------|-----------------------------------------------|--------|
| `LONG_ACTIVE` | LONG | LONG |
| `SWITCH_LONG_TO_SHORT_PENDING` | **SHORT** | **LONG** |
| `LONG_BLOCKED` | LONG | LONG |
| `SHORT_ARMED` | SHORT | SHORT (overload residual; not flipped here) |
| `SHORT_ACTIVE` | SHORT | SHORT |
| `SWITCH_SHORT_TO_LONG_PENDING` | **LONG** | **SHORT** |
| `SHORT_BLOCKED` | SHORT | SHORT |
| `LONG_ARMED` | LONG | LONG (overload residual; not flipped here) |
| else | fallback LONG | fallback LONG |

### 5.3 Short→Long SM TARGET (interacts with §5.2)

While generator is SHORT-oriented, SM consumes **reversal** =
`DOWNSCOPE_CONFIRMED`.

| SideState | CURRENT event | TARGET event |
|-----------|---------------|--------------|
| `SHORT_ACTIVE` | `UPSCOPE_CONFIRMED` | `DOWNSCOPE_CONFIRMED` |
| `SWITCH_SHORT_TO_LONG_PENDING` | `UPSCOPE_CONFIRMED` | `DOWNSCOPE_CONFIRMED` (after PENDING hold SHORT, this is geometric up) |
| `SHORT_BLOCKED` | `UPSCOPE_CONFIRMED` | `DOWNSCOPE_CONFIRMED` |
| `LONG_ARMED` | `UPSCOPE_CONFIRMED` | `UPSCOPE_CONFIRMED` (unchanged; shared with neutral start) |

Long→Short pipeline **event names stay** `DOWNSCOPE_CONFIRMED` at every
step. The PENDING orientation TARGET makes that token remain geometric
**down** on the frozen Long-era anchor (fixes census §11.2 stall).

### 5.4 Entry/Exit (unchanged by this contract)

Integrated Replay / adapter table remains the Entry/Exit owner.
Productive wallclock bridges carry a **parallel** PENDING map
(`SWITCH_*_PENDING` → still-`*_ACTIVE`). That parallel map is **not**
repaired here. It is blast-radius (must not be silently treated as the
canonical table).

## 6. Formula relation (no K choice)

```text
FORMULA_NUMERIC_SHAPE_STILL_VALID=true
FORMULA_DIRECTIONAL_INTERPRETATION_AFTER_THIS_CONTRACT=VALID_ONCE_RUNTIME_BOUND
FORMULA_REQUIRES_RE_ADJUDICATION=false
```

Unchanged unbound MODEL_C shape:

```text
up = 1.0 × current_hysteresis_band
adverse = 0.4 × up
reversal = 0.6 × up
```

No selection of `0.5` / `0.75` / `1.25` / `1.5` / `2.0`. After a later
runtime bind of **this** mapping contract, geometric-up on SHORT lands
on `DOWNSCOPE` and SM consumes it — then Band-Koinzidenz is polarity-
safe. Until that bind, freeze-exception stays false.

```text
MODEL_C_NUMERIC_SHAPE=
  up_distance = 1.0 * current_hysteresis_band
  adverse_exit_distance = 0.4 * up_distance
  reversal_distance = 0.6 * up_distance
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
MODEL_C_RUNTIME_BINDING_AUTHORIZED=false
CAP63_PRODUCTIVE_VALUES=
  up_distance=200.0
  adverse_exit_distance=80.0
  reversal_distance=120.0
  confirmation_epochs=2
CAP63_PRODUCTIVE_VALUES_UNCHANGED=true
```

## 7. Blast radius (later runtime-bind GO; not this slice)

Class: `FORENSIC_RAW_EVIDENCE` of **who must move together**. No edits.

### 7.1 Must co-change if SM Short→Long consumes `DOWNSCOPE_CONFIRMED`

| Surface | Why |
|---------|-----|
| `src/trading/master_v2/double_play_state.py` `transition_state` | Sole switch owner; four Short→Long guards |
| `tests/trading/master_v2/test_double_play_state.py` | Asserts `SHORT_ACTIVE` + `UPSCOPE_CONFIRMED` → PENDING |
| `tests/trading/master_v2/test_double_play_pure_stack_contract.py` | Same pipeline assertions |
| `tests/trading/master_v2/test_double_play_dashboard_display.py` | Same |
| `tests/trading/master_v2/test_offline_governance_tick_harness_v0.py` | Same |
| `tests/trading/master_v2/test_chop_scope_event_policy_binding_contract_v1.py` | PENDING via current event |
| `tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py` | Short binding after-state |
| `tests/trading/master_v2/test_canonical_dynamic_scope_trailing_state_continuity_v1.py` | Cooldown after UPSCOPE from SHORT |
| `src/trading/master_v2/offline_double_play_scenario_replay_v0.py` | Detects SHORT_ACTIVE → PENDING |
| `src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py` | Scenario switch envelope |
| `src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py` | PENDING branch |
| `src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py` | PENDING branch |
| [FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md](FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md) | `UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG` |
| `tests/ops/test_master_v2_state_switch_contract_static_v0.py` | Pins that marker; **must move with the contract** |
| [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) §4 upscope-transition prose | Vocabulary; not runtime |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_KILL_ALL_STATE_SWITCH_FAVORABLE_ADVERSE_EXTREME_MOVES_ACCEPTANCE_V0.md` | Pipeline token |

**Fail-closed rule for later GO:** do not change `transition_state`
without the static State-Switch marker test and the docs invariant in
the same diff. Do not change the docs invariant without runtime.

### 7.2 Must co-change if PENDING generator orientation is held to departing side

| Surface | Why |
|---------|-----|
| `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` `scope_direction_from_side_state_v1` | Productive owner of the table |
| `src/backtest/mv2_research_wiring_v1.py` | Projects next-bar `scope_direction_state` via that function |
| `tests/trading/master_v2/test_canonical_dynamic_scope_trailing_state_continuity_v1.py` | Calls the function / EntryExit map |

Generator **formulas** (`compute_evaluated_thresholds`,
`_matched_directional_conditions`) are **out of this repair**. Mirror
tests stay.

### 7.3 Parallel maps — do not silently “fix” as if they were the owner

| Surface | Observed fact |
|---------|----------------|
| Wallclock `decision_economics_cycle_bridge_v1.py` `_update_session_state_from_replay` | PENDING → still `*_ACTIVE` for Entry/Exit; **also** sets `scope_direction_state` from **composition** `selected_side`, not from `scope_direction_from_side_state_v1` |
| Wallclock `hardening_cycle_bridge_v2.py` | Same parallel PENDING → `*_ACTIVE` and composition-selected scope direction |
| `scope_event_generator_scenario_binding_adapter_v0.py` `active_side_to_scope_direction_v0` | `ActiveSide.SHORT` → SHORT else LONG; PENDING is trailing-NEUTRAL → **LONG** (already closer to Long→Short PENDING TARGET; **not** identical to productive table) |
| Cycle harnesses that assign `ScopeDirectionState.SHORT` literally | Test/scenario injection; not productive owner |

A later runtime GO that remaps only `scope_direction_from_side_state_v1`
**must** re-adjudicate the wallclock composition overlay. Leaving it
unexamined would re-create Dual Orientation on the productive host.

### 7.4 Explicitly out of scope (this family and later bind)

- PR `#6270` / `feat&#47;full-core-live-path-composition-root-v1`
- `update_dynamic_boundaries` / band formula / Cap 6.3 distances
- MODEL_C `derive_scope_event_distances_v1` seam
- Research BPS `100` / ratios `0.5` / `0.75`
- Scenario `_distance_triplet_from_scope_v0`
- `hysteresis_multiplier` runtime field
- Live / orders / credentials / GET / POST
- Census forensic text in the parent spec (do not rewrite OQ wording)

### 7.5 Blast-radius verdict

```text
BLAST_RADIUS_CLASS=BOUNDED_MAPPING_PLUS_DOCS_STATIC_TEST_COCHANGE
PARALLEL_ORIENTATION_OWNERS_EXIST=true
ARMED_OVERLOAD_BLOCKS_PURE_TABLE_FULL_HOLD=true
CAP62_LAST_ACTIVE_CARRY_NOT_IN_THIS_FAMILY_YET=true
```

### 7.6 Minimum atomic runtime repair set (not implemented here)

A later runtime-bind GO must **not** treat A and B as independent
repairs. They are one atomic set together with their direct tests.

```text
MINIMUM_ATOMIC_RUNTIME_REPAIR_SET=
  SHORT_REVERSAL_EVENT_POLARITY_PLUS_PENDING_GENERATOR_ORIENTATION_PLUS_DIRECT_CONTRACT_AND_BEHAVIOR_TESTS
```

| Atom | TARGET (unbound) |
|------|------------------|
| A | `SHORT_ACTIVE` reversal consumption: `UPSCOPE_CONFIRMED` → `DOWNSCOPE_CONFIRMED` |
| B | PENDING generator orientation: `SWITCH_LONG_TO_SHORT_PENDING` → LONG; `SWITCH_SHORT_TO_LONG_PENDING` → SHORT |
| C | Direct contract / static / behavior tests for A+B, including State-Switch marker `UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG` |

ARMED semantics, wallclock composition overlay, scenario
`active_side_to_scope_direction_v0`, and Entry/Exit tables are **outside**
this minimum set. Do not invent ARMED history-carry in that GO unless a
separate Owner decision authorizes `last_active_side`.

## 8. Case confirmation

```text
FINAL_CASE=CASE_2
DIRECTIONAL_MAPPING_CONTRACT_REPAIR_REQUIRED_BEFORE_FREEZE_EXCEPTION=true
CONTRACT_REPAIR_ADJUDICATED=true
CONTRACT_REPAIR_RUNTIME_BOUND=false
ANCHOR_OR_PIPELINE_TRAILING_RUNTIME_REPAIR_REQUIRED_BEFORE_FREEZE_EXCEPTION=false
```

## 9. Machine markers

```text
MARKER: DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: MAPPING_CONTRACT_ADJUDICATED=true
MARKER: MAPPING_CONTRACT_RUNTIME_BOUND=false
MARKER: OQ_CENSUS_1_ADJUDICATED_KEEP_GENERATOR_MIRROR_SM_CONSUMES_SHORT_REVERSAL_DOWNSCOPE
MARKER: OQ_CENSUS_2_ADJUDICATED_TRAILING_FREEZE_INTENDED
MARKER: OQ_CENSUS_3_ADJUDICATED_PRESERVE_THEN_IMPLICIT_REBASE
MARKER: OQ_CENSUS_4_ADJUDICATED_PARTIAL_PENDING_HOLD_DEPARTING_ACTIVE
MARKER: OQ_CENSUS_5_ADJUDICATED_FREEZE_EXCEPTION_BLOCKED_UNTIL_RUNTIME_BIND
MARKER: ARMED_SIDE_STATE_OVERLOAD_RESIDUAL=true
MARKER: WALLCLOCK_COMPOSITION_SCOPE_DIRECTION_OVERLAY_IN_BLAST_RADIUS=true
MARKER: STATE_SWITCH_STATIC_MARKER_MUST_COCHANGE_WITH_TRANSITION_STATE
MARKER: MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
MARKER: PR_6270_MUST_REMAIN_UNTOUCHED=true
MARKER: LIVE_AUTHORIZED=false
MARKER: NEXT_STOP=AWAIT_OWNER_GO_DIRECTIONAL_MAPPING_RUNTIME_BIND
```

## 10. STOP conditions

Stop immediately if this file is treated as:

1. runtime bind of `transition_state` or `scope_direction_from_side_state_v1`
2. freeze exception or MODEL_C derivation seam
3. authorization to un-mirror generator formulas
4. authorization to trail as destination during the pipeline
5. authorization to add Cap 6.2 `last_active_side` in this slice
6. a rewrite of the State-Switch contract without runtime (docs&#47;runtime drift)
7. PR `#6270` modification
8. Live / orders / credentials

## 11. Next stop

```text
NEXT_STOP=AWAIT_OWNER_GO_DIRECTIONAL_MAPPING_RUNTIME_BIND
MODEL_C_FREEZE_EXCEPTION_REMAINS_UNAUTHORIZED=true
REQUIRED_PRE_FREEZE_WORKPACKAGE=DIRECTIONAL_MAPPING_RUNTIME_BIND_OF_THIS_CONTRACT
```

That later GO must be scoped to §5 TARGET plus §7 co-change set. It is
not this GO.
