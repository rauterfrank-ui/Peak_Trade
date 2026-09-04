---
title: "MODEL_C Dynamic Scope Derived Switch-Event Thresholds Contract v1"
status: "DRAFT"
owner: "ops"
last_updated: "2026-09-04"
docs_token: "DOCS_TOKEN_MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1"
---

# MODEL_C Dynamic Scope Derived Switch-Event Thresholds Contract v1

## 1. Purpose

Record the **Owner-adjudicated architectural target** for aligning Dual Envelope:

```text
ARCHITECTURAL_TARGET=
  DYNAMIC_SCOPE remains the stateful trailing SSOT
  AND becomes the numeric source from which SWITCH EVENT THRESHOLDS are derived
```

This file is the **docs-only, non-authorizing** contract for that target (WP1).

It does **not**:

- implement MODEL_C
- runtime-bind a derivation formula
- authorize a Cap 6.2 / 6.3 / 6.5 freeze exception
- bind `hysteresis_multiplier` at runtime
- modify `transition_state`, `update_dynamic_boundaries`, or Integrated Replay
- modify PR `#6270`

**Current productive baseline remains MODEL_B** until a separate freeze-exception GO plus runtime-bind GO are granted and proven.

Formula and policy (OQ-C1..C6) are recorded docs-only in
[MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md](MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md).
That sibling does **not** authorize runtime, freeze-exception, profit-protection
rewrite, research rewrite, or `hysteresis_multiplier` runtime.

## 2. Non-authority note

```text
DOCUMENT_CLASS=DOCS_ONLY_NON_AUTHORIZING_CONTRACT
MODEL_C_ARCHITECTURE_TARGET=AUTHORIZED
MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
MODEL_C_FORMULA=ADJUDICATED_DOCS_ONLY_NOT_RUNTIME_BOUND
MODEL_C_FORMULA_AUTHORIZED=false
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
LIVE_AUTHORIZED=false
ORDERS_AUTHORIZED=false
RUNTIME_BRIDGE_ACTIVATION=false
CORE_LOGIC_CHANGE=false
```

Clarified mapping wording here is **not** runtime materialization.

Safety posture unchanged:

- Global HOLD / no-order program boundary unchanged
- Cap 6.3 frozen distances remain the productive numeric owner
- Evidence does not authorize runtime
- Dashboard does not authorize trades or side switches

## 3. Owner decisions frozen by this contract

| Model | Status |
|-------|--------|
| MODEL_A — price vs `current_*_boundary` inside / beside `transition_state` | **REJECTED** as a direct implementation path |
| MODEL_B — Dual Envelope (trailing band fields vs caller/config distances) | **PRESERVE** as current productive baseline |
| MODEL_C — derive generator distances from Dynamic Scope SSOT; keep Event SM | **AUTHORIZED for contract only** |

```text
MODEL_A_STATUS=REJECT_AS_DIRECT_IMPLEMENTATION_PATH
MODEL_B_STATUS=PRESERVE_AS_CURRENT_BASELINE_UNTIL_MODEL_C_POLICY_IS_SEPARATELY_PROVEN_AND_AUTHORIZED
MODEL_C_STATUS=AUTHORIZED_FOR_CONTRACT_AND_IMPACT_ADJUDICATION_ONLY
```

## 4. Current baseline (MODEL_B) — do not rewrite here

Proven productive split (forensic; not a new SSOT):

**Envelope A — Dynamic Scope trailing SSOT**

- Owner: `trading.master_v2.double_play_state.RuntimeScopeState`
- Update: `update_dynamic_boundaries`
- Fields: `anchor_price`, `current_downscope_boundary`, `current_upscope_boundary`, `current_hysteresis_band`
- Persistence: Cap 6.2
- Continuity: [CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md](CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md)

**Envelope B — Switch-event distances**

- Generator: `generate_deterministic_scope_event`
- Inputs: `trailing_anchor` (from RuntimeScopeState after trailing repair) **plus** caller/config `up_distance` / `adverse_exit_distance` / `reversal_distance`
- Productive numeric owner: Cap 6.3 TOML [`config/ops/canonical_decision_runtime_config_v1.toml`](../../../config/ops/canonical_decision_runtime_config_v1.toml) (`up_distance=200.0`, `adverse_exit_distance=80.0`, `reversal_distance=120.0`, `confirmation_epochs=2`)
- Switch owner: `transition_state` consumes `ScopeEvent`, **not** boundary fields as a price threshold

Cap 6.2 explicitly froze those distances while persisting RuntimeScopeState. Cap 6.3 gate `EFFECTIVE_NUMERIC_VALUES_UNCHANGED` still applies.

Research path `mv2_research_wiring_v1` uses a **parallel** producer (mark-relative 100 bps). That is not this contract's formula and is not retired here.

## 5. MODEL_C target semantics (formula recorded, runtime unbound)

When (and only when) a later runtime-bind GO materializes the mapping
recorded in
[MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md](MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md):

```text
RuntimeScopeState_after_update_dynamic_boundaries
  → derived (up_distance, adverse_exit_distance, reversal_distance)
  → generate_deterministic_scope_event
  → mapped ScopeEvent
  → transition_state
```

Invariants of the target (independent of runtime-bind status):

1. Dynamic Scope remains stateful trailing SSOT (`SCOPE(t) → SCOPE(t+1)`).
2. Switch remains event-driven. `transition_state` **must not** compare mark price to `current_downscope_boundary` / `current_upscope_boundary`.
3. Derived distances are **not** a second numeric authority once bound; they are outputs of the Scope SSOT.
4. Confirmation, four-step pipeline, cooldown, max-switches, and CHOP remain separate protective layers.

**Rejected (MODEL_A):** reading `current_*_boundary` as the switch criterion inside `transition_state`.

## 6. Authorized derivation seam (location only)

If later bound, the **only** canonical seam is:

```text
update_dynamic_boundaries
  → [UNBOUND derive_scope_event_distances_v1]  # mapping recorded; seam must not exist yet
  → generate_deterministic_scope_event
```

Orchestrator: `run_integrated_offline_trading_logic_replay_v1`, after `runtime_scope_pre` / `trailing_anchor_used` and **before** the generator call.

Not authorized as seams:

- `transition_state`
- `step_switch_gate`
- silent mutation of Cap 6.3 TOML values without freeze-exception GO
- scenario-adapter fallback `_distance_triplet_from_scope_v0` (TEST/SCENARIO only; not productive host; **not** the MODEL_C formula)

Until a later runtime-bind GO: the seam **must not exist** in runtime code. Productive host continues to pass Cap 6.3 frozen distances into the generator.

## 7. Formula status

```text
MODEL_C_FORMULA=ADJUDICATED_DOCS_ONLY_NOT_RUNTIME_BOUND
MODEL_C_FORMULA_AUTHORIZED=false
FORMULA_OWNER=docs/ops/specs/MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md
```

Recorded mapping (docs-only; not runtime-bound) lives in the sibling
adjudication. This architecture contract still does **not** authorize
implementation.

Still forbidden here and in runtime:

- treating the recorded mapping as already bound
- any ATR multiplier or `hysteresis_multiplier`
- using the scenario-adapter `{1.0, 0.8, 2.0}` triplet as MODEL_C
- inventing a different mapping in implementation, tests, or comments

## 8. Mandatory dual-use split (implemented; numeric coincidence preserved)

```text
MANDATORY_CONTRACT_REQUIREMENT=
  UP_DISTANCE_SWITCH_EVENT_ROLE_AND_PROFIT_PROTECTION_ROLE_MUST_BE_SEPARATED_BEFORE_ANY_MODEL_C_RUNTIME_BINDING
DUAL_USE_SPLIT_IMPLEMENTED=true
```

Owner persist:
[MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md](MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1.md).

Cap 6.5 no longer aliases Cap 6.3 `up_distance` as `profit_protection_distance`:

- `FROZEN_PROFIT_PROTECTION_DISTANCE = 200.0` (Cap 6.5 own owner)
- productive bridges pass `profit_protection_distance=FROZEN_PROFIT_PROTECTION_DISTANCE`
- Cap 6.3 switch-event `up_distance` remains `200.0`

Those remain **different roles**:

| Role | Meaning | Must remain distinct before MODEL_C bind |
|------|---------|------------------------------------------|
| Switch-event `up_distance` | Generator threshold vs trailing_anchor | MODEL_C derivation target |
| Profit-protection distance | Cap 6.5 / Entry-Exit profit-protection producer | **Must not** silently follow derived switch distances |

A MODEL_C runtime bind that derives switch `up_distance` from a trailing band **without** this split would mutate Exit numerics. That remains **forbidden**.

Profit-protection keeps the frozen `200.0` as its own owner. It must not follow derived switch-event thresholds.

## 9. Mandatory preservations

These must survive any future MODEL_C bind. This contract does not authorize changing them.

| Invariant | Current owner |
|-----------|----------------|
| `confirmation_epochs` | Cap 6.3 (`2`); not derived from the band |
| Four-step pipeline LONG↔SHORT | `transition_state` |
| Cooldown | `RuntimeScopeState.last_completed_side_switch_tick` |
| Max switches | `RuntimeScopeState.switches_in_window` |
| CHOP latch / trailing freeze | `chop_latched` / CHOP scope policy |
| Persistence continuity | Cap 6.2 RuntimeScopeState |
| Instrument identity reseed | Integrated Replay resolver |
| Deterministic replay | Integrated Replay + wiring |
| Sole switch authority | `transition_state` only |
| Entry/Exit consumes resulting SideState | `evaluate_double_play_entry_exit_policy_v0` |

`hysteresis_multiplier` remains docs vocabulary in the Manifest / DSE contract. It is **not** a RuntimeScopeState field and **must not** be introduced as one without a separate GO.

## 10. Freeze and config gates (still in force)

Until a **separate** freeze-exception GO:

```text
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

Still binding:

- Cap 6.2: no change to productive `up_distance=200.0` / `adverse_exit_distance=80.0` / `reversal_distance=120.0` while persisting scope
- Cap 6.3: [`docs/ops/CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md`](../CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md) — one config owner; effective values unchanged
- Tests and parity modules that assert `CANONICAL_UP_DISTANCE == 200.0`

This contract **does not** grant an exception. Formula GO alone is also insufficient without an explicit freeze-exception GO.

## 11. Parallel producers (not retired here)

| Producer | Status under this contract |
|----------|----------------------------|
| Cap 6.3 TOML distances | Productive SSOT until Formula + freeze-exception |
| Research 100 bps (`mv2_research_wiring_v1`) | Remains a parallel research producer; retirement needs Formula GO |
| Scenario injected ScopeEvents | TEST_ONLY / SCENARIO_NON_PRODUCTIVE |
| Scenario `_distance_triplet_from_scope_v0` fallback | Not productive MODEL_C |

Leaving Research BPS in place after a productive MODEL_C bind would re-create Dual Envelope on the research path. OQ-C4 is now adjudicated docs-only: same derivation at later bind; no rewrite now.

## 12. Open questions (adjudicated docs-only; runtime still unbound)

Owner:
[MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md](MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md).

| ID | Question | Adjudicated policy (docs-only) |
|----|----------|--------------------------------|
| OQ-C1 | Mapping from RuntimeScopeState band/boundaries to `up_distance` | `up_distance = current_hysteresis_band` |
| OQ-C2 | Mapping for `adverse_exit_distance` and `reversal_distance` | Cap 6.3 ratios `0.4` / `0.6` on derived `up_distance` |
| OQ-C3 | Cap 6.3 distances after bind: retire vs clamp vs floor | Freeze remains now; **retire** as generator inputs after a later freeze-exception; **no clamp** to `200`, `80`, `120` |
| OQ-C4 | Research BPS: replace with same derivation or keep exception | Dual producer remains now; same derivation at later productive bind |
| OQ-C5 | Profit-protection: forever freeze `200.0` vs own policy | **Identity split implemented**; keep frozen `200.0` as Cap 6.5 own owner |
| OQ-C6 | When trailing freezes (`volatility_estimate` missing / `chop_latched`): last derived vs fail-closed vs Cap 6.3 fallback | Last derived if prior band valid; else fail-closed; **no** Cap 6.3 fallback |

## 13. Relation to existing authorities

| Document | Relation |
|----------|----------|
| [CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md](CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1.md) | Trailing SSOT; MODEL_C consumes it, does not replace it |
| [FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md](FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md) | Docs-only DSE vocabulary; `hysteresis_multiplier` remains unbound |
| [FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md](FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md) | Switch consumes confirmed scope events; MODEL_C does not move that into `transition_state` price checks |
| [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) | Target vocabulary (trailing, confirmation, no naive static thresholds); not a formula bind |
| [CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1.md](CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1.md) | Persistence + distance freeze |
| [`docs/ops/CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md`](../CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1.md) | Productive distance config owner |
| [CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1.md](CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1.md) | Dual-use split implemented: Cap 6.5 own `200.0` profit-protection owner |
| Canonical Master Runbook | Unchanged by this file; this contract does not rewrite SSOT path labels |

Master Runbook §1 path labels and Map of Truth `TRADING_DECISION_CORE` remain **navigation / path labels**, not Intra-Zyklus-Formel. This contract does not “fix” those labels.

## 14. PR isolation

```text
PR_6270_MODIFICATION_AUTHORIZED=false
PR_6270_MUST_REMAIN_UNTOUCHED=true
PR_6270_TOUCHES_DUAL_ENVELOPE_SEMANTICS=false
```

MODEL_C docs and any later implementation **must not** land on `feat&#47;full-core-live-path-composition-root-v1`.

## 15. Implementation staging (none authorized by this PR)

1. **This docs contract** (WP1) — closed on `e9bd94965` (PR `#6271`)
2. **Owner Formula and Policy adjudication** — recorded in [MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md](MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md)
3. Dual-use split (switch-event vs profit-protection) — **implemented** (identity split; numeric remains `200.0`)
4. Freeze-exception Cap 6.2 / 6.3 / 6.5 — **`NEXT_STOP`**
5. Pure derivation function + golden vectors vs MODEL_B — separate GO
6. Runtime bind at the Integrated Replay seam — separate GO

## 16. Machine markers

```text
MARKER: MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1_EXISTS
MARKER: DOCS_ONLY
MARKER: NON_AUTHORIZING_POSTURE
MARKER: MODEL_C_ARCHITECTURE_TARGET=AUTHORIZED
MARKER: MODEL_C_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
MARKER: MODEL_C_FORMULA_AUTHORIZED=false
MARKER: MODEL_C_FORMULA=ADJUDICATED_DOCS_ONLY_NOT_RUNTIME_BOUND
MARKER: MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
MARKER: HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
MARKER: MODEL_A_REJECTED_AS_DIRECT_IMPLEMENTATION_PATH
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: SWITCH_OWNER_REMAINS_TRANSITION_STATE
MARKER: TRANSITION_STATE_MUST_NOT_READ_BOUNDARY_FIELDS_AS_PRICE_THRESHOLD
MARKER: DERIVATION_SEAM_UNBOUND
MARKER: UP_DISTANCE_SWITCH_EVENT_ROLE_AND_PROFIT_PROTECTION_ROLE_MUST_BE_SEPARATED_BEFORE_RUNTIME
MARKER: DUAL_USE_SPLIT_IMPLEMENTED=true
MARKER: CONFIRMATION_EPOCHS_NOT_DERIVED_FROM_BAND
MARKER: FOUR_STEP_PIPELINE_PRESERVED
MARKER: LIVE_AUTHORIZED=false
MARKER: NEXT_STOP=AWAIT_OWNER_GO_MODEL_C_FREEZE_EXCEPTION
```

## 17. STOP conditions

Stop immediately (no runtime, no second formula) if:

1. Text implies `MODEL_C_FORMULA_AUTHORIZED=true` or treats the recorded mapping as runtime-bound
2. `hysteresis_multiplier` is described as runtime-bound
3. `transition_state` is described as consuming `current_*_boundary` as switch threshold
4. Profit-protection is allowed to follow derived switch `up_distance` without a split
5. Cap 6.2 / 6.3 freeze is treated as already excepted
6. PR `#6270` is modified
7. Live / orders / credentials / execution are implied
8. Scenario-adapter fallback is cited as the MODEL_C formula
9. A mapping other than the sibling adjudication is invented in implementation, tests, or comments

## 18. Next stop

```text
NEXT_STOP=AWAIT_OWNER_GO_MODEL_C_FREEZE_EXCEPTION
```

Dual-use identity split is implemented (both values remain `200.0`). Freeze-exception remains required before any MODEL_C runtime bind.
