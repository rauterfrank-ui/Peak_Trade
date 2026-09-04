---
title: "MODEL_C Formula and Policy Adjudication v1"
status: "ACTIVE"
owner: "ops"
last_updated: "2026-09-04"
docs_token: "DOCS_TOKEN_MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1"
---

# MODEL_C Formula and Policy Adjudication v1

## 1. Purpose

Persist the Owner-granted **formula and policy adjudication** for MODEL_C
(OQ-C1..C6) under:

```text
OWNER_GO=PEAK_TRADE_OWNER_GO_MODEL_C_FORMULA_ADJUDICATION_V1
OWNER_GO_STATUS=GRANTED_CONFIRMED
AUTHORIZED_SCOPE=MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_ONLY
BOUND_ORIGIN_MAIN_SHA=e9bd94965a3f6e9bdc29b76b1e0c1cfbe3a4b594
PARENT_CONTRACT=docs/ops/specs/MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md
```

This file records the **intended derivation mapping and policy**. It does
**not** implement MODEL_C, bind runtime, grant a freeze exception, rewrite
profit-protection, rewrite research distances, bind `hysteresis_multiplier`,
modify PR `#6270`, or authorize Live.

```text
DOCUMENT_CLASS=DOCS_ONLY_FORMULA_AND_POLICY_ADJUDICATION
PARALLEL_SSOT_CREATED=false
MODEL_C_ARCHITECTURE_TARGET=AUTHORIZED
MODEL_C_FORMULA=ADJUDICATED_DOCS_ONLY_NOT_RUNTIME_BOUND
MODEL_C_FORMULA_ADJUDICATED=true
MODEL_C_FORMULA_POLICY_ADJUDICATED=true
MODEL_C_FORMULA_RUNTIME_BOUND=false
ADJUDICATED_TARGET_POLICY_NOT_RUNTIME_BOUND=true
MODEL_C_FORMULA_AUTHORIZED=false
MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
PR_6270_MODIFICATION_AUTHORIZED=false
LIVE_MUTATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
RUNTIME_BRIDGE_ACTIVATION=false
CORE_LOGIC_CHANGE=false
MODEL_B_REMAINS_PRODUCTIVE_BASELINE=true
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

Parent architecture contract:
[MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md](MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md).

Clarified mapping wording here is **not** runtime materialization.

## 2. Epistemic class separation

```text
CANONICAL_AUTHORITY=THIS_OWNER_GO_PLUS_PARENT_MODEL_C_CONTRACT
FORENSIC_RAW_EVIDENCE=SECTION_4
ALREADY_ADJUDICATED_CONCLUSION=SECTION_5_AND_6
HISTORICAL_INTERMEDIATE=WP1_CONTRACT_FORMULA_UNSET
NAVIGATION_ONLY=MAP_OF_TRUTH
HYPOTHESIS=NONE_USED_AS_CONCLUSION
OPEN=RUNTIME_BIND_FREEZE_EXCEPTION
CONFLICTED=NONE
```

Rejected as formula sources (not used as MODEL_C mapping):

| Source | Why rejected |
|--------|----------------|
| Scenario `_distance_triplet_from_scope_v0` `{1.0, 0.8, 2.0}` plus `max(..., 1.0)` | TEST/SCENARIO only; invents a `1.0` floor; parent contract forbids citing it as MODEL_C |
| Research 100 bps / ratios `1 : 0.5 : 0.75` | Parallel research producer; rewrite unauthorized; not the productive Cap 6.3 geometry |
| Cap 6.3 frozen `200`, `80`, `120` as the derived scale | That is MODEL_B Dual Envelope; MODEL_C replaces the generator **scale**, not by copying the freeze |
| `hysteresis_multiplier` | Docs vocabulary only; not a `RuntimeScopeState` field; runtime bind unauthorized |
| Direct `transition_state` read of `current_*_boundary` | MODEL_A; already rejected |

## 3. Owner-GO bounds (this slice)

This adjudication **may** decide OQ-C1..C6 as policy text.

This adjudication **must not**:

- add `derive_scope_event_distances_v1` (or any seam) to runtime
- change Cap 6.2 / 6.3 / 6.5 effective numerics
- change `profit_protection_distance` wiring
- change `mv2_research_wiring_v1` BPS distances
- introduce `hysteresis_multiplier` as a runtime field
- touch `feat&#47;full-core-live-path-composition-root-v1` / PR `#6270`
- treat Formula GO as freeze-exception GO

Productive baseline remains MODEL_B until a later freeze-exception GO
**and** a later runtime-bind GO are granted and proven.

## 4. Forensic geometry (not a new SSOT)

Class: `FORENSIC_RAW_EVIDENCE`.

**Trailing SSOT** (`update_dynamic_boundaries` in
[`src/trading/master_v2/double_play_state.py`](../../../src/trading/master_v2/double_play_state.py)):

```text
band = clamp_band_width(volatility_estimate * mark_price)
LONG:  anchor = max(prior_anchor, mark); down = anchor - band; up = anchor + band
SHORT: anchor = min(prior_anchor, mark); up = anchor + band; down = anchor - band
current_hysteresis_band = band
```

When trailing has updated, the stored band is **symmetric**:

```text
|anchor_price - current_downscope_boundary| == current_hysteresis_band
|current_upscope_boundary - anchor_price| == current_hysteresis_band
```

Missing `volatility_estimate` or `chop_latched=true` returns the prior
state unchanged (no `1.0` invention).

**Generator thresholds** (`compute_evaluated_thresholds` in
[`src/trading/master_v2/deterministic_scope_event_generator_v1.py`](../../../src/trading/master_v2/deterministic_scope_event_generator_v1.py)):

```text
LONG:  downscope_candidate = trailing_anchor - up_distance
       up_candidate        = trailing_anchor + up_distance
       adverse_exit        = trailing_anchor - adverse_exit_distance
SHORT: downscope_candidate = trailing_anchor + up_distance
       up_candidate        = trailing_anchor - up_distance
       adverse_exit        = trailing_anchor + adverse_exit_distance
constraint: adverse_exit_distance <= reversal_distance
invariant: nested adverse (adverse < up) must not suppress DOWNSCOPE/UPSCOPE
```

If `up_distance = current_hysteresis_band` after a successful trailing
update, generator candidate thresholds **coincide geometrically** with
`current_downscope_boundary` / `current_upscope_boundary`. MODEL_A is
still rejected: `transition_state` consumes `ScopeEvent`, not those
fields as a price threshold.

**Cap 6.3 productive ratios** (frozen; still the MODEL_B numeric owner):

```text
up_distance = 200.0
adverse_exit_distance = 80.0
reversal_distance = 120.0
confirmation_epochs = 2
ADVERSE_TO_UP_RATIO = 80.0 / 200.0 = 0.4
REVERSAL_TO_UP_RATIO = 120.0 / 200.0 = 0.6
```

Owner:
[`config/ops/canonical_decision_runtime_config_v1.toml`](../../../config/ops/canonical_decision_runtime_config_v1.toml)
and Cap 6.3
[`docs/ops/CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md`](../CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md).

**Cap 6.5 dual-use** (FORENSIC_BEFORE the separately authorized identity
split; not current productive wiring after that split):

```text
FORENSIC_CLASS=HISTORICAL_INTERMEDIATE
DUAL_USE_BEFORE=
  FROZEN_PROFIT_PROTECTION_DISTANCE = float(CANONICAL_UP_DISTANCE)
  productive bridge: profit_protection_distance = decision_cfg.up_distance
DUAL_USE_AFTER_SEE=
  docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md
```

This formula record does **not** implement that split. The later identity
split keeps the effective profit-protection value `200.0` under a Cap 6.5
own owner. It does **not** bind MODEL_C derivation.

**Research parallel producer** (not rewritten here):

```text
up = mark * (100 / 10000)
adverse = up * (60/120) = 0.5 * up
reversal = up * (90/120) = 0.75 * up
```

Owner: [`src/backtest/mv2_research_wiring_v1.py`](../../../src/backtest/mv2_research_wiring_v1.py).

## 5. Formula adjudication (OQ-C1, OQ-C2)

Class: `ALREADY_ADJUDICATED_CONCLUSION` from this Owner-GO.

Intended pure function, **unbound** until a later runtime-bind GO:

```text
FUNCTION_NAME=derive_scope_event_distances_v1
SEAM=
  update_dynamic_boundaries
  → [UNBOUND derive_scope_event_distances_v1]
  → generate_deterministic_scope_event
HOST_WHEN_LATER_BOUND=
  run_integrated_offline_trading_logic_replay_v1
  after runtime_scope_pre / trailing_anchor_used
  before the generator call
```

### OQ-C1 — `up_distance`

```text
OQ-C1_STATUS=ADJUDICATED_DOCS_ONLY
ADJUDICATED_TARGET_POLICY_NOT_RUNTIME_BOUND=true
PRODUCTIVELY_CONSUMED_NOW=false
OQ-C1_MAPPING=
  up_distance = current_hysteresis_band
OQ-C1_FIELD_OWNER=RuntimeScopeState.current_hysteresis_band
OQ-C1_HYSTERESIS_MULTIPLIER_USED=false
```

`current_hysteresis_band` is the clamped trailing band width already
written by `update_dynamic_boundaries`. It is **not**
`hysteresis_multiplier`.

Fail-closed input gates (for any later implementation; not implemented here):

1. `current_hysteresis_band` must be finite and `> 0`.
2. Do **not** invent `1.0` or `min_band_width` as a silent floor at the
   derivation seam (`clamp_band_width` already ran inside trailing).
3. If trailing has updated this cycle, the symmetry check must hold:
   `|anchor_price - current_downscope_boundary| == current_hysteresis_band`
   and `|current_upscope_boundary - anchor_price| == current_hysteresis_band`.
   Divergence is `FAIL_CLOSED` (asymmetric bands are not the current
   productive implementation; do not pick a boundary ad hoc).
4. Derived `up_distance` must remain `<=` generator
   `hard_max_scope_distance` or the cycle is `FAIL_CLOSED`.

Rejected OQ-C1 alternatives:

- `|anchor_price - current_downscope_boundary|` as **primary** mapping
  (equivalent today under symmetry; secondary consistency check only)
- any ATR multiplier, offset, or `hysteresis_multiplier`
- scenario `{band, 0.8*band, 2.0*band}`

### OQ-C2 — `adverse_exit_distance` and `reversal_distance`

```text
OQ-C2_STATUS=ADJUDICATED_DOCS_ONLY
ADJUDICATED_TARGET_POLICY_NOT_RUNTIME_BOUND=true
PRODUCTIVELY_CONSUMED_NOW=false
OQ-C2_MAPPING=
  adverse_exit_distance = up_distance * (80.0 / 200.0)
  reversal_distance     = up_distance * (120.0 / 200.0)
OQ-C2_CAP63_RATIOS_CONFIRMED=
  80 / 200 = 0.4
  120 / 200 = 0.6
OQ-C2_RATIO_TEXT_INCONSISTENCY_STATUS=NOT_PRESENT_IN_DECISION_RECORD
OQ-C2_RATIO_PROVENANCE=CAP_6_3_FROZEN_RATIO_BASELINE
OQ-C2_SCALE_OWNER=DERIVED_UP_DISTANCE_FROM_SCOPE_SSOT
```

This preserves the productive **relative** geometry (nested adverse
inside downscope/upscope; `adverse < reversal`) while the **scale**
follows the Scope SSOT.

Fail-closed:

1. `adverse_exit_distance > 0` and `reversal_distance > 0` and finite.
2. `adverse_exit_distance <= reversal_distance` (generator already
   rejects the inverse).
3. `adverse_exit_distance < up_distance` (nested-adverse invariant).
4. Derived adverse / reversal must remain `<=` generator
   `hard_max_adverse_distance` / `hard_max_reversal_distance` or the
   cycle is `FAIL_CLOSED`.

Rejected OQ-C2 alternatives:

- research ratios `0.5` and `0.75`
- scenario ratios `0.8` and `2.0`
- independent mappings from ATR or from `hysteresis_multiplier`
- copying frozen `80.0` and `120.0` as absolute MODEL_C values

### Not derived

```text
confirmation_epochs = 2
CONFIRMATION_EPOCHS_NOT_DERIVED_FROM_BAND=true
FOUR_STEP_PIPELINE_PRESERVED=true
SWITCH_OWNER_REMAINS_TRANSITION_STATE=true
TRANSITION_STATE_MUST_NOT_READ_BOUNDARY_FIELDS_AS_PRICE_THRESHOLD=true
```

## 6. Policy adjudication (OQ-C3..C6)

Class: `ALREADY_ADJUDICATED_CONCLUSION` from this Owner-GO.
None of these policies is executed in this slice.

### OQ-C3 — Cap 6.3 distances after a later bind

```text
OQ-C3_STATUS=ADJUDICATED_DOCS_ONLY
OQ-C3_UNTIL_FREEZE_EXCEPTION=
  Cap 6.3 200/80/120 remain the productive generator SSOT
  EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
  MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
OQ-C3_AFTER_SEPARATE_FREEZE_EXCEPTION_AND_RUNTIME_BIND=
  RETIRE Cap 6.3 up/adverse/reversal as generator inputs
  DO_NOT_CLAMP_OR_FLOOR_DERIVED_DISTANCES_TO_200_80_120
OQ-C3_CLAMP_REJECTED_REASON=
  A Cap 6.3 numeric clamp after derivation would re-create Dual Envelope
confirmation_epochs remains Cap 6.3 owner (value 2)
```

Formula GO is **not** a freeze-exception GO.

### OQ-C4 — Research BPS producer

```text
OQ-C4_STATUS=ADJUDICATED_DOCS_ONLY
OQ-C4_NOW=
  Dual producer remains; research 100 bps path is not rewritten
  RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
OQ-C4_AT_PRODUCTIVE_RUNTIME_BIND=
  Research must consume the same derive_scope_event_distances_v1 mapping
  A BPS exception at bind time is forbidden (would re-create Dual Envelope
  on the research path)
OQ-C4_REWRITE_PERFORMED=false
```

### OQ-C5 — Profit-protection dual-use split

```text
OQ-C5_STATUS=IMPLEMENTED_IDENTITY_SPLIT
OQ-C5_SPLIT_MANDATORY=true
OQ-C5_NUMERIC=
  KEEP_FROZEN_200.0 as Cap 6.5 own owner
OQ-C5_IDENTITY=
  profit_protection_distance MUST NOT alias switch-event up_distance
OQ-C5_REWRITE_AUTHORIZED=false
OQ-C5_IDENTITY_SPLIT_PERFORMED=true
OQ-C5_NEW_PROFIT_PROTECTION_FORMULA=UNSET_NOT_INVENTED
OWNER_PERSIST=docs/ops/specs/MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md
```

The split is an **identity** split, not a new Exit formula. Cap 6.5
`FROZEN_PROFIT_PROTECTION_DISTANCE = 200.0` is no longer
`float(CANONICAL_UP_DISTANCE)`. Productive hosts pass that Cap 6.5
constant, not `decision_cfg.up_distance`.

### OQ-C6 — Trailing freeze (`volatility_estimate` missing / `chop_latched`)

```text
OQ-C6_STATUS=ADJUDICATED_DOCS_ONLY
OQ-C6_WHEN_TRAILING_RETURNS_PRIOR_STATE_AND_PRIOR_BAND_VALID=
  USE_LAST_DERIVED_DISTANCES
  (band/boundaries are unchanged; last mapping stays aligned)
OQ-C6_WHEN_NO_VALID_PRIOR_DERIVATION=
  FAIL_CLOSED
  (no switch-event candidates; do not invent 1.0)
OQ-C6_CAP_63_FALLBACK=FORBIDDEN
OQ-C6_CAP_63_FALLBACK_REJECTED_REASON=
  Falling back to frozen 200/80/120 during freeze would re-create Dual Envelope
```

This matches trailing's own fail-closed freeze (return prior state; no
`1.0` invention).

## 7. What remains unauthorized

```text
MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
DERIVATION_SEAM_UNBOUND=true
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
PROFIT_PROTECTION_REWRITE_AUTHORIZED=false
RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
PR_6270_MODIFICATION_AUTHORIZED=false
LIVE_MUTATION_AUTHORIZED=false
PURE_DERIVATION_FUNCTION_CODE_AUTHORIZED=false
GOLDEN_VECTOR_RUNTIME_HARNESS_AUTHORIZED=false
```

MODEL_B (`200`, `80`, `120` into the generator; Cap 6.5 profit-protection
own `200.0`, not an alias of switch-event `up_distance`) remains the
productive baseline.

## 8. Staging (updated)

1. Docs-only architecture contract (WP1) — **closed** on
   `e9bd94965a3f6e9bdc29b76b1e0c1cfbe3a4b594` (PR `#6271`)
2. Owner Formula and Policy adjudication — **this file**
3. Dual-use split implementation (switch-event vs profit-protection
   identity; numeric remains `200.0`) — **implemented**
4. Freeze-exception Cap 6.2 / 6.3 / 6.5 — **not authorized** (`NEXT_STOP`)
5. Pure derivation function + golden vectors vs MODEL_B — **not authorized**
6. Runtime bind at the Integrated Replay seam — **not authorized**

Steps 3 and 4 must not be skipped. Formula adjudication does not skip
them.

## 9. Relation to existing authorities

| Document | Relation |
|----------|----------|
| [MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md](MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md) | Parent architecture contract; this file fills OQ-C1..C6 as docs-only policy |
| [CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md](CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md) | Trailing SSOT consumed; not replaced |
| [FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md](FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md) | `hysteresis_multiplier` remains unbound docs vocabulary |
| [CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1.md](CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1.md) | Dual-use identity split implemented separately; profit-protection remains 200.0 under Cap 6.5 own owner |
| Canonical Master Runbook | Unchanged; this file does not rewrite SSOT path labels |

Master Runbook §1 path labels and Map of Truth `TRADING_DECISION_CORE`
remain navigation / path labels, not this formula.

## 10. Machine markers

```text
MARKER: MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: NON_AUTHORIZING_RUNTIME_POSTURE
MARKER: MODEL_C_FORMULA=ADJUDICATED_DOCS_ONLY_NOT_RUNTIME_BOUND
MARKER: MODEL_C_FORMULA_ADJUDICATED=true
MARKER: MODEL_C_FORMULA_POLICY_ADJUDICATED=true
MARKER: MODEL_C_FORMULA_RUNTIME_BOUND=false
MARKER: ADJUDICATED_TARGET_POLICY_NOT_RUNTIME_BOUND=true
MARKER: MODEL_C_FORMULA_AUTHORIZED=false
MARKER: MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
MARKER: MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
MARKER: OQ-C1=up_distance_eq_current_hysteresis_band
MARKER: OQ-C2=cap_6_3_ratios_on_derived_up
MARKER: OQ-C3=retire_cap_6_3_generator_inputs_after_later_freeze_exception_no_clamp
MARKER: OQ-C4=same_derivation_at_later_research_bind_no_rewrite_now
MARKER: OQ-C5=identity_split_implemented_keep_frozen_200
MARKER: OQ-C6=last_derived_or_fail_closed_no_cap_6_3_fallback
MARKER: HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: SWITCH_OWNER_REMAINS_TRANSITION_STATE
MARKER: DERIVATION_SEAM_UNBOUND
MARKER: LIVE_AUTHORIZED=false
MARKER: NEXT_STOP=AWAIT_OWNER_GO_MODEL_C_FREEZE_EXCEPTION
```

## 11. STOP conditions

Stop immediately if text or a later change:

1. Treats this file as `MODEL_C_FORMULA_AUTHORIZED=true` for runtime
2. Implements `derive_scope_event_distances_v1` or binds the Integrated Replay seam
3. Describes `hysteresis_multiplier` as runtime-bound
4. Describes `transition_state` as consuming `current_*_boundary` as switch threshold
5. Lets profit-protection follow derived switch `up_distance`
6. Treats Cap 6.2 / 6.3 freeze as already excepted
7. Clamps derived distances to frozen `200`, `80`, `120` (Dual Envelope)
8. Cites scenario `_distance_triplet_from_scope_v0` as the MODEL_C formula
9. Rewrites research BPS or Cap 6.5 in this slice
10. Modifies PR `#6270`
11. Implies Live / orders / credentials / execution

## 12. Next stop

```text
NEXT_STOP=AWAIT_OWNER_GO_MODEL_C_FREEZE_EXCEPTION
EARLIEST_UNRESOLVED_MODEL_C_DEPENDENCY=MODEL_C_FREEZE_EXCEPTION
LATER_REQUIRED_GO=PURE_DERIVATION_FUNCTION_AND_GOLDEN_VECTORS
LATER_REQUIRED_GO_AFTER_THAT=MODEL_C_RUNTIME_BIND
```
