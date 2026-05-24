---
title: "Futures Double Play State-Switch Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-05-24"
docs_token: "DOCS_TOKEN_FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0"
---

# Futures Double Play State-Switch Contract v0

## 1. Purpose

This contract is the **canonical docs-only owner** for **Master V2 / Double Play State-Switch** governance: how **Long/Bull ↔ Short/Bear** side-state transitions are specified on a **single selected future**, given **confirmed** Dynamic Scope Envelope inputs.

It **consolidates and crosslinks** side-switch vocabulary embedded in [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) §3–4. It **does not** implement State-Switch runtime behavior or authorize execution.

**Gap addressed:** GAP-SS-001 — manifest §20 references this file; this contract materializes that reference.

**Predecessor required:** [FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md](FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md) must be repo-canonical before this contract is authoritative (sequencing satisfied on main).

## 2. Non-authority note

This file is **docs-only** and **non-authorizing**. It does **not**:

- implement State-Switch or hot-path side-switch wiring
- grant order placement, execution, or session permission
- authorize Paper, Shadow, Testnet, Live, bounded pilot, or broker/exchange connectivity
- set `live_authorization: true` or imply live readiness
- convert CI green, evidence, archive indexes, or dashboard labels into runtime permission
- replace KillSwitch / Kill-All semantics or bypass Risk/Safety veto layers
- modify `src&#47;trading&#47;master_v2&#47;` or any protected trading logic

Clarified mapping wording here is **not** equivalent to runtime materialization.

**Safety posture (unchanged by this contract):**

- **Global HOLD** remains active
- **Preflight** remains **BLOCKED** ([PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md))
- **Evidence** does not authorize runtime
- **Dashboard** does not authorize trades or side switches
- **AI** does not authorize execution or side switches

## 3. Scope

**In scope:**

- canonical vocabulary for side states, switch pipelines, and switch events (candidate vs confirmed)
- relation to Dynamic Scope Envelope as **input producer** (scope events only)
- fail-closed interpretation rules for side-switch eligibility
- boundaries with Scope/Capital, KillSwitch, Execution/Live Gates, AI, Dashboard, Pure Stack
- machine markers for future static-contract tests (GAP-SS-STATIC-001)
- implementation staging pointers (separate governed approvals)

**Out of scope:**

- concrete implementation in `src/`, scripts, workflows, adapters, or WebUI routes
- Dynamic Scope Envelope vocabulary redefinition (owned by DSE contract)
- KillSwitch implementation or gate closure
- State-Switch vs KillSwitch crosslink test body (owned by PR #3648 authority static contract)
- Pure stack readiness inventory headlines (owned by PR #3649 pure stack static contract)
- golden-vector behavior tests (separate approval)
- Market-Airport work

## 4. Sequencing and canonical owners

Manifest §20 recommended contract order:

```text
1. FUTURES_UNIVERSE_SELECTOR_CONTRACT_V0.md
2. FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md   ← predecessor (on main)
3. FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md   ← this document
4. FUTURES_STRATEGY_SUITABILITY_AND_DOUBLE_PLAY_HANDOFF_CONTRACT_V0.md
```

| Surface | Canonical owner | This contract's role |
|---------|-----------------|---------------------|
| Overall Double Play target semantics | Trading Logic Manifest | Defers side-switch detail here |
| Dynamic Scope Envelope / scope events | [FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md](FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md) | **Predecessor input producer** |
| State-Switch side-state governance | **This contract** | **Owner** |
| State-Switch ≠ KillSwitch crosslink tests | PR #3648 authority static contract | **Pointer only — do not duplicate** |
| Pure stack transition_state inventory | Pure Stack Readiness Map + #3649 tests | **Reference only** |
| Account/deployable capital layering | Scope/Capital Clarification | **Distinct** upstream layer |

## 5. Master V2 / Double Play context

Applies to **one selected future** with:

- **Long/Bull layer** — strategies suited to rising price context
- **Short/Bear layer** — strategies suited to falling price context
- **State-Switch logic** — normal side transition between layers

**Core invariant (manifest §2):**

```text
LONG_ACTIVE and SHORT_ACTIVE must not both be active on the same future
```

Hedge mode, if ever allowed, requires a **separate** governance path. Default posture: **exactly one active side**.

## 6. Relation to Dynamic Scope Envelope (predecessor)

**Division of responsibility:**

| Dynamic Scope Envelope (DSE) | State-Switch (this contract) |
|------------------------------|------------------------------|
| When boundaries move; when scope events confirm | How side states transition given **confirmed** scope events |
| Produces/constrains scope events | Consumes `*_CONFIRMED` for LONG↔SHORT pipelines |
| Owns trailing bands, hysteresis, cooldown, confirmation_ticks at scope layer | Inherits anti-flip-flop prerequisites; applies switch-level gating |

**Invariant:** `DSE_PREDECESSOR_REQUIRED=true`  
**Invariant:** `STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY=true`

This contract **does not** redefine DSE vocabulary. Crosslink to DSE §9 for scope event definitions.

## 7. Allowed DSE inputs and rejected candidates

### Allowed scope inputs for side-switch eligibility

| DSE input | Side-switch role |
|-----------|------------------|
| `DOWNSCOPE_CONFIRMED` | **Required** prerequisite for Long→Short switch pipeline |
| `UPSCOPE_CONFIRMED` | **Required** prerequisite for Short→Long switch pipeline |

**Invariant:** `DOWNSCOPE_CONFIRMED_REQUIRED_FOR_LONG_TO_SHORT=true`  
**Invariant:** `UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG=true`

### Explicitly rejected as sufficient alone

| DSE input | Posture |
|-----------|---------|
| `DOWNSCOPE_CANDIDATE` | **Does not** authorize side switch |
| `UPSCOPE_CANDIDATE` | **Does not** authorize side switch |

**Invariant:** `CANDIDATE_EVENTS_DO_NOT_AUTHORIZE_SIDE_SWITCH=true`  
**Invariant:** `CANDIDATE_VS_CONFIRMED_SWITCH_EVENTS_DISTINCT=true`

Additional DSE guard inputs that **block** new side-switch eligibility:

- `CHOP_DETECTED` → chop guard block
- `SCOPE_UNKNOWN` → fail-closed
- stale/frozen boundary (`freshness_state: stale`, `boundary_frozen: true`)
- `KILL_ALL_REQUIRED` → Kill-All override (see §14)

## 8. Side-state vocabulary (Long/Bull ↔ Short/Bear)

Target side states (manifest §4):

```text
NEUTRAL_OBSERVE
LONG_ARMED
LONG_ACTIVE
LONG_BLOCKED
SHORT_ARMED
SHORT_ACTIVE
SHORT_BLOCKED
SWITCH_LONG_TO_SHORT_PENDING
SWITCH_SHORT_TO_LONG_PENDING
CHOP_GUARD_BLOCK
KILL_ALL
```

| Term | Meaning |
|------|---------|
| **Long/Bull side** | Long-oriented strategy layer on the selected future |
| **Short/Bear side** | Short-oriented strategy layer on the selected future |
| **Armed** | Side prepared within pre-authorized envelope; not yet active |
| **Active** | Side currently active (only one side active at a time) |
| **Blocked** | Side may not receive new activation |
| **Pending switch** | Transition in progress; not yet confirmed complete |

## 9. Normal switch pipelines

### Downscope pipeline (Long → Short)

Requires `DOWNSCOPE_CONFIRMED` from DSE.

```text
LONG_ACTIVE
  → SWITCH_LONG_TO_SHORT_PENDING
  → LONG_BLOCKED
  → SHORT_ARMED
  → SHORT_ACTIVE
```

### Upscope pipeline (Short → Long)

Requires `UPSCOPE_CONFIRMED` from DSE.

```text
SHORT_ACTIVE
  → SWITCH_SHORT_TO_LONG_PENDING
  → SHORT_BLOCKED
  → LONG_ARMED
  → LONG_ACTIVE
```

### Neutral start

```text
NEUTRAL_OBSERVE
  → LONG_ARMED → LONG_ACTIVE
  or
  → SHORT_ARMED → SHORT_ACTIVE
```

Exact runtime mapping is governed wiring — **not** authorization from this doc alone.

## 10. Switch events: candidate vs confirmed

**Layer 1 — Scope events (DSE owner):** CANDIDATE → CONFIRMED promotion per DSE §9–11.

**Layer 2 — Side switch (this contract):**

| Event | Role |
|-------|------|
| `SIDE_SWITCH_CANDIDATE` | Pending transition entered (e.g. `SWITCH_*_PENDING`); **does not** alone complete side change |
| `SIDE_SWITCH_CONFIRMED` | Active side changed; prior side blocked per pipeline |
| `SIDE_SWITCH_BLOCKED` | Chop guard, cooldown, Kill-All, or fail-closed guard prevented completion |

Confirmed scope event enables **eligibility only**. Side switch still requires passing switch-level gates (§11).

## 11. Inherited anti-flip-flop controls (from DSE)

State-Switch **inherits** these prerequisites from DSE; it does not weaken them:

| Control | Source | SS application |
|---------|--------|----------------|
| **Hysteresis** | DSE §11 | Minimum separation before switch eligibility |
| **Cooldown** | DSE §11; `min_switch_cooldown_ms` | Minimum time between **completed** side switches |
| **Confirmation ticks** | DSE §11 | Scope CANDIDATE→CONFIRMED before switch input |
| **Chop guard** | DSE §11; manifest §4 | `CHOP_GUARD_BLOCK` — no new switch |
| **Scope stability** | DSE §11 | Sustained signal before confirmation |
| **max_switches_per_window** | DSE static hard limits | Switch count ceiling — fail-closed when exceeded |

Missing or invalid DSE envelope → **fail-closed** (observe/neutral only).

## 12. Fail-closed semantics

Fail closed (no new side-switch eligibility / no new activation) when:

- DSE envelope or rules invalid
- only CANDIDATE scope events present (no `*_CONFIRMED`)
- `SCOPE_UNKNOWN` or stale/frozen boundary
- `CHOP_DETECTED` active
- chop guard or switch cooldown not satisfied
- `max_switches_per_window` exceeded
- missing pre-authorized envelope
- contradictory governance inputs
- Kill-All active or required

Default operational posture: **observe/neutral** until all gates pass.

## 13. Relation to Scope/Capital

[MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md) defines capital-path layering upstream of instrument-level semantics.

This contract governs **side-state transitions within** an already-governed deployable context. It **does not**:

- mutate capital-slot runtime state
- change ratchet or release behavior
- grant live allocation authority
- collapse deployable capital into side-switch semantics

**Invariant:** `SCOPE_CAPITAL_RUNTIME_UNCHANGED=true`

[MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) §15: slot bounds must stay **consistent** with pre-authorized envelopes; side switch must not bypass slot governance.

## 14. KillSwitch / Kill-All boundary

- **Kill-All / Emergency Stop** is **superior** to normal State-Switch (manifest §3–4).
- Kill-All is **not** routine Long↔Short side change.
- State-Switch **cannot override** Kill-All or KillSwitch veto layers.
- `any_state → KILL_ALL` when Kill-All required.

**Invariant:** `KILLSWITCH_SUPERIOR=true`  
**Invariant:** `STATE_SWITCH_NOT_KILLSWITCH_FLIP=true`

State-Switch ≠ KillSwitch static crosslink **owner** remains PR #3648 (`test_master_v2_decision_authority_map_static_crosslink_contract_v0.py`) — **do not duplicate** that test body under GAP-SS-STATIC-001.

## 15. Execution / Live Gates boundary

State-Switch compliance is **necessary for coherent semantics** but **not sufficient** for execution. GLB blockers remain OPEN/BLOCKED by default ([MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md)). Preflight remains BLOCKED. `live_authorization` stays **false**.

**Invariant:** `EXECUTION_LIVE_GATE_UNCHANGED=true`  
**Invariant:** `SWITCH_COMPLIANCE_NOT_LIVE_AUTHORIZATION=true`  
**Invariant:** `LIVE_AUTHORIZATION_REMAINS_FALSE_IN_STATE_SWITCH=true`

No order authorization, session start, or Paper/Shadow/Testnet/Live promotion is implied.

## 16. AI / Dashboard / Strategy registry boundary

- **AI:** context only; **does not** authorize side switch ([MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md) §10).
- **Dashboard:** may display side/state labels read-only; display ≠ Freigabe.
- **Evidence / metrics:** inputs for review only; **not** switch authority.
- **Strategy registry:** metadata ≠ Master V2 trading authority ([STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)).

**Invariant:** `AI_AUTHORITY=false`  
**Invariant:** `DASHBOARD_AUTHORITY=false`  
**Invariant:** `EVIDENCE_DOES_NOT_AUTHORIZE_SIDE_SWITCH=true`

## 17. Relation to Arithmetic / Sequence Survival

[MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md): pre-arm stress and order-sensitive path analysis may inform **whether** a switch sequence is survivable — **not** hot-path switch authorization.

## 18. Pure stack reference boundary

[MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) §6: pure `transition_state` semantics aligned with manifest; **not** a running runtime state machine. Pure stack static tests prove model-only inventory — **not** runtime integration readiness. **Do not duplicate** #3649 pure stack static owner under GAP-SS-STATIC-001.

## 19. Hot-path boundary

| Allowed (lightweight) | Forbidden |
|-----------------------|-----------|
| Read confirmed scope events from DSE state | Recompute full DSE envelope from raw history |
| Update side-state fields per governed pipelines | AI / governance / evidence I/O on switch tick |
| O(1) fail-closed switch eligibility checks | Order placement, exchange I/O, session start |

**Invariant:** `HOT_PATH_NO_HEAVY_RECOMPUTE_ON_SWITCH=true`

## 20. Validation / future tests pointer

Future static-contract tests: **GAP-SS-STATIC-001** — separate operator approval; after this docs contract merge. Illustrative module: `tests&#47;ops&#47;test_master_v2_state_switch_contract_static_v0.py` (~18–22 tests).

Future behavior tests (separate approval) may include manifest §19 invariants subset for side switching without Exchange/Live (manifest §22 OQ #8).

## 21. Implementation staging

1. **This docs contract** (current slice) — governance/spec only
2. **Static-contract tests** — GAP-SS-STATIC-001; separate operator approval
3. **Pure-stack handoff alignment** — separate approval; no hot-path wiring by default
4. **Protected runtime State-Switch implementation** — separate approval; `src&#47;trading&#47;master_v2&#47;` — **not** authorized by this doc

## 22. Machine markers (for GAP-SS-STATIC-001)

```text
MARKER: FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0_EXISTS
MARKER: STATE_SWITCH_CONTRACT_V0
MARKER: STATE_SWITCH_IMPLEMENTED=false
MARKER: DOCS_ONLY
MARKER: NON_AUTHORIZING_POSTURE
MARKER: GLOBAL_HOLD_REMAINS_ACTIVE
MARKER: PREFLIGHT_REMAINS_BLOCKED
MARKER: EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME
MARKER: DSE_PREDECESSOR_REQUIRED
MARKER: DOWNSCOPE_CONFIRMED_REQUIRED_FOR_LONG_TO_SHORT
MARKER: UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG
MARKER: CANDIDATE_EVENTS_DO_NOT_AUTHORIZE_SIDE_SWITCH
MARKER: CANDIDATE_VS_CONFIRMED_SWITCH_EVENTS_DISTINCT
MARKER: KILLSWITCH_SUPERIOR
MARKER: STATE_SWITCH_NOT_KILLSWITCH_FLIP
MARKER: EXECUTION_LIVE_GATE_UNCHANGED
MARKER: SCOPE_CAPITAL_RUNTIME_UNCHANGED
MARKER: AI_AUTHORITY=false
MARKER: DASHBOARD_AUTHORITY=false
MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_STATE_SWITCH
MARKER: SWITCH_COMPLIANCE_NOT_LIVE_AUTHORIZATION
MARKER: GAP_SS_001_CLOSED_BY_THIS_DOC
MARKER: GAP_SS_STATIC_001_FUTURE_TESTS_ONLY
MARKER: NO_DUPLICATION_OF_PR3648_STATE_SWITCH_VS_KILLSWITCH_OWNER
MARKER: NO_DUPLICATION_OF_PR3649_PURE_STACK_READINESS_OWNER
MARKER: MANIFEST_SECTION_20_CROSSLINK_TO_THIS_CONTRACT
```

## 23. Open questions

| ID | Question | Default posture |
|----|----------|-----------------|
| OQ-SS-001 | Universe Selector contract before SS runtime? | Manifest §20 #1 soft dependency; DSE sequencing lock satisfied |
| OQ-SS-002 | Distinct switch cooldown vs DSE scope cooldown? | Document both; fail-closed if unset |
| OQ-SS-003 | Unify switch_gate with master_v2 side model? | Defer (see DSE OQ-002) |
| OQ-SS-004 | Manifest Related specs crosslink update? | Recommended follow-on docs touch |
| OQ-SS-005 | Side-switch behavior tests without exchange? | Separate approval; manifest §22 #8 |

## 24. Non-goals

- No State-Switch **implementation** or hot-path wiring
- No execution authorization, order placement, or session start
- No live / testnet / paper / shadow readiness promotion
- No broker or exchange connectivity semantics
- No runtime behavior change in `src&#47;trading&#47;master_v2&#47;`
- No KillSwitch / Kill-All implementation or replacement
- No Scope/Capital runtime behavior change
- No capital-slot ratchet/release mutation
- No dashboard feature implementation
- No Market-Airport work
- No evidence → authorization conversion
- No GLB blocker closure or Preflight unblock
- No static-contract tests in this docs-only slice

## 25. STOP conditions

Stop immediately if:

1. Contract text implies `live_authorization: true` or live readiness
2. Candidate scope events alone authorize side switch
3. Kill-All conflated with normal Long↔Short switch
4. AI, dashboard, evidence, or strategy registry granted switch authority
5. DSE vocabulary redefined instead of crosslinked
6. Duplicate #3648 or #3649 static test owners re-pinned without new gap ID
7. Repo change attempted outside approved docs-only slice
8. Scope/Capital or KillSwitch runtime behavior implied as changed
9. Operator protected-scope approval missing for tests or implementation slices
10. State-Switch contract drafted before DSE contract repo-canonical (already satisfied — do not revert)

## 26. Cross-references

- [FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md](FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md) — **predecessor**; scope events
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md)
- [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md)
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md)
- [MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md)
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)
- [MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md)
- [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md)

When this file changes, run `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot` as for sibling ops specs.
