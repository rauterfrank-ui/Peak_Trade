---
title: "Futures Dynamic Scope Envelope Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-05-24"
docs_token: "DOCS_TOKEN_FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0"
---

# Futures Dynamic Scope Envelope Contract v0

## 1. Purpose

This contract is the **canonical docs-only owner** for the **Futures Dynamic Scope Envelope**: the pre-authorized, bounded envelope within which **trailing scope bands**, **hysteresis**, **cooldown**, **confirmation**, and **scope drift / scope trail** semantics operate for Master V2 / Double Play on a **single selected future**.

It **consolidates and crosslinks** vocabulary embedded in [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) §5–8 and adjacent governance surfaces. It **does not** implement runtime behavior or authorize execution.

**Gap addressed:** GAP-DSE-001 — manifest §20 references this file; this contract materializes that reference.

**Sequencing lock:** This contract must be defined **before** `FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md` (planned; manifest §20 ordering).

## 2. Non-authority note

This file is **docs-only** and **non-authorizing**. It does **not**:

- grant order placement, execution, or session permission
- authorize Paper, Shadow, Testnet, Live, bounded pilot, or broker/exchange connectivity
- set `live_authorization: true` or imply live readiness
- convert CI green, evidence, archive indexes, or dashboard labels into runtime permission
- replace KillSwitch / Kill-All semantics or bypass Risk/Safety veto layers
- authorize State-Switch **implementation** or hot-path wiring
- modify `src&#47;trading&#47;master_v2&#47;` or any protected trading logic

Clarified mapping wording here is **not** equivalent to runtime materialization.

**Safety posture (unchanged by this contract):**

- **Global HOLD** remains active
- **Preflight** remains **BLOCKED** ([PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md))
- **Evidence** does not authorize runtime
- **Dashboard** does not authorize trades
- **AI** does not authorize execution

## 3. Scope

**In scope:**

- canonical vocabulary for Dynamic Scope Envelope, static hard limits, dynamic scope rules, and lightweight runtime scope state
- scope events (CANDIDATE vs CONFIRMED), trailing bands, hysteresis, cooldown, confirmation_ticks, chop guard, hard guardrails
- crosslinks to Master V2 / Double Play, Scope/Capital, KillSwitch, Execution/Live Gates, AI, Dashboard, Futures Input, Capital Slot, Arithmetic Survival, Pure Stack Readiness
- fail-closed interpretation rules
- machine markers for future static-contract tests (GAP-DSE-STATIC-001)
- implementation staging pointers (separate governed approvals)

**Out of scope:**

- concrete implementation in `src/`, scripts, workflows, adapters, or WebUI routes
- State-Switch side state machine specification (deferred to future contract)
- KillSwitch implementation or gate closure
- golden-vector behavior tests (separate approval)
- Market-Airport work

## 4. Sequencing and canonical owners

Manifest §20 recommended contract order:

```text
1. FUTURES_UNIVERSE_SELECTOR_CONTRACT_V0.md
2. FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md   ← this document
3. FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md  ← future
4. FUTURES_STRATEGY_SUITABILITY_AND_DOUBLE_PLAY_HANDOFF_CONTRACT_V0.md
```

| Surface | Canonical owner | This contract's role |
|---------|-----------------|---------------------|
| Overall Double Play target semantics | Trading Logic Manifest | Defers envelope detail here |
| Dynamic Scope Envelope vocabulary | **This contract** | **Owner** |
| State-Switch side transitions | Future State-Switch contract | **Consumes** confirmed scope events |
| Account/deployable capital layering | Scope/Capital Clarification | **Distinct** upstream layer |
| Kill-All / Emergency Stop | Manifest §3; Risk/Safety docs | **Separate** veto |
| Pure stack model evaluators | Pure Stack Readiness Map §6 | **Reference** only |

## 5. Core concept

The **Dynamic Runtime Envelope** (manifest §7) consists of:

```text
1. Static Hard Limits     — ceilings dynamic rules must never widen
2. Dynamic Scope Rules    — governed trailing, hysteresis, cooldown, confirmation
3. Runtime Scope State    — lightweight hot-path boundary/anchor updates only
```

Applies to **one selected future** with Long/Bull and Short/Bear layers (manifest §2). The envelope governs **scope event eligibility** — not order placement or strategy activation.

## 6. Static hard limits

Static hard limits are pre-authorized ceilings. Dynamic rules **must not** expand them.

Illustrative field vocabulary (manifest §7.1):

```yaml
static_hard_limits:
  max_notional: number
  max_leverage: number
  max_position_size: number
  max_switches_per_window: integer
  min_band_width: number
  max_band_width: number
  kill_all_conditions: list
  live_authorization: false
```

**Invariant:** `STATIC_HARD_LIMITS_NEVER_WIDENED_BY_DYNAMIC_RULES=true`  
**Invariant:** `LIVE_AUTHORIZATION_REMAINS_FALSE_IN_ENVELOPE=true`

## 7. Dynamic scope rules

Governed parameters for trailing and anti-flip-flop behavior (manifest §7.2). Dynamic work is allowed **only inside** static hard limits.

```yaml
dynamic_scope_rules:
  trailing_enabled: true
  anchor_update_mode: trend_extreme
  volatility_model: atr_or_realized_volatility
  downscope_band_multiplier: number
  upscope_band_multiplier: number
  min_band_width: number
  max_band_width: number
  hysteresis_multiplier: number
  boundary_update_rate_limit: number
  min_scope_hold_ms: integer
  min_switch_cooldown_ms: integer
  confirmation_ticks: integer
  freeze_conditions: list
  chop_guard_conditions: list
```

## 8. Runtime dynamic scope state

Lightweight hot-path state fields (manifest §7.3). Mutations must be O(1) and pre-authorized — no heavy recompute.

```yaml
runtime_dynamic_scope_state:
  active_side: LONG | SHORT | NEUTRAL
  anchor_price: number
  current_upscope_boundary: number
  current_downscope_boundary: number
  current_hysteresis_band: number
  current_volatility_estimate: number
  last_switch_utc: timestamp
  switch_count_window: integer
  freshness_state: fresh | stale | unknown
  chop_score: number
  boundary_frozen: boolean
```

## 9. Scope events and confirmation pipeline

Scope events (manifest §5):

| Event | Role |
|-------|------|
| `DOWNSCOPE_CANDIDATE` | Provisional downscope; **does not** alone authorize State-Switch |
| `DOWNSCOPE_CONFIRMED` | Confirmed downscope; **input** to State-Switch (future contract) |
| `UPSCOPE_CANDIDATE` | Provisional upscope; **does not** alone authorize State-Switch |
| `UPSCOPE_CONFIRMED` | Confirmed upscope; **input** to State-Switch (future contract) |
| `CHOP_DETECTED` | Flip-flop / noisy market guard |
| `SCOPE_UNKNOWN` | Fail-closed: scope cannot be determined reliably |
| `KILL_ALL_REQUIRED` | Crosslink to Kill-All; **not** normal scope trail |

**Invariant:** `CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT=true`  
**Invariant:** `STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY=true`

## 10. Trailing scope bands and anchor modes

Fixed price thresholds are insufficient in strong trends (manifest §6). **Trailing scope bands** trail anchor extremes within clamped band width:

- **Long context:** anchor ratchets to new highs; downscope boundary trails below anchor.
- **Short context:** anchor ratchets to new lows; upscope boundary trails above anchor.

**Scope drift / scope trail:** controlled boundary migration following anchor updates — **not** arbitrary scope expansion.

**Invariant:** `TRAILING_SCOPE_BANDS_VOCABULARY_PRESENT=true`

## 11. Hysteresis, cooldown, and confirmation

Anti-flip-flop controls (manifest §5):

| Control | Purpose |
|---------|---------|
| **Hysteresis** | Minimum separation band; may use `hysteresis_multiplier` × band width |
| **Cooldown** | Minimum time/ticks between completed side switches |
| **Confirmation ticks** | Sustained scope signal before CANDIDATE → CONFIRMED |
| **Chop guard** | Blocks switching when flip-flop risk exceeds threshold |
| **Scope stability** | Tick/window count condition holds before confirmation |

**Invariant:** `HYSTERESIS_COOLDOWN_VOCABULARY_PRESENT=true`  
**Invariant:** `CONFIRMATION_TICKS_VOCABULARY_PRESENT=true`

## 12. Band width and volatility models

Band width must not be arbitrary (manifest §8):

```text
dynamic_band_width = clamp(
  atr_or_realized_volatility * multiplier,
  min_band_width,
  max_band_width
)
```

**Governance choice (open):** primary volatility metric — ATR vs realized volatility vs rolling range (OQ-001). If unset, fail-closed for operational interpretation.

Futures Input Snapshot may supply vol proxies; snapshot **cannot widen** static hard limits ([MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md) §14).

## 13. Futures input integration

| Input | Role |
|-------|------|
| `ready_for_dynamic_scope` | Readiness flag; incomplete volatility → fail-closed ([MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md)) |
| Volatility / liquidity proxies | May inform band or cooldown interpretation only when governance maps them |
| Opportunity / inactivity | Data-only; not standalone trading authority |

**Invariant:** `FUTURES_INPUT_READY_FOR_DYNAMIC_SCOPE_CROSSLINK=true`

Cross-layer handoff from `ready_for_dynamic_scope` to pure state transitions is **specified here as fail-closed**; behavior-test enforcement is a separate governed slice (OQ-003).

## 14. Relation to Scope/Capital envelope

[MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md) defines capital-path layering: Account Equity → Tradable Scope → Deployable Scope → downstream Risk and Exposure Caps.

This contract defines **instrument-level price/structure boundaries** (trailing bands) within an already-governed deployable context.

| Concept | Must not collapse with |
|---------|------------------------|
| Dynamic price boundary | Deployable capital allowance |
| Deployable scope | Max notional / leverage caps |
| Envelope compliance | Scope correctness alone |

**Invariant:** `DYNAMIC_SCOPE_ENVELOPE_DISTINCT_FROM_DEPLOYABLE_CAPITAL=true`

## 15. Relation to Capital Slot

[MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) §15: State-Switch and dynamic scope govern side transitions **within** the same selected future; slot size bounds and ratchet eligibility must stay **consistent** with pre-authorized envelopes defined here. Capital-slot semantics must not bypass envelope governance.

## 16. Relation to Arithmetic / Sequence Survival

[MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) §4, §8: the **Double Play Survival Envelope** joins Dynamic Scope Envelope + arithmetic kernel + sequence survival. Arithmetic and sequence layers are **pre-arm / governance** inputs — not hot-path heavy recompute (§12–13 survival contract).

## 17. Relation to State-Switch (future contract)

| Dynamic Scope Envelope | State-Switch (future) |
|------------------------|----------------------|
| When boundaries move; when events confirm | How side states transition given **confirmed** events |
| Produces/constrains scope events | Consumes `*_CONFIRMED` events for LONG↔SHORT pipelines |
| **First** in manifest §20 order | **Third** in manifest §20 order |

This contract **does not** specify the State-Switch state machine. Do not draft State-Switch contract before this file is repo-canonical.

## 18. Kill-All and Safety boundary

- **Kill-All / Emergency Stop** is **outside** normal scope trail (manifest §3).
- Envelope may reference `kill_all_conditions` in static hard limits but **does not** implement KillSwitch.
- Normal scope trail or side eligibility **≠** KillSwitch flip.

**Invariant:** `DYNAMIC_SCOPE_TRAIL_NOT_KILLSWITCH=true`

State-Switch ≠ KillSwitch crosslink owner remains PR #3648 static contract — **do not duplicate** that test body under GAP-DSE-STATIC-001.

## 19. Execution / Live Gates boundary

Envelope satisfaction is **necessary for coherent semantics** but **not sufficient** for execution. GLB blockers remain OPEN/BLOCKED by default ([MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md)). Preflight remains BLOCKED. `live_authorization` stays **false** ([MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md)).

**Invariant:** `ENVELOPE_COMPLIANCE_NOT_LIVE_AUTHORIZATION=true`

## 20. AI / Dashboard / Strategy registry boundary

- **AI:** context only; no hot-path envelope recomputation ([MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md](MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md) §10; manifest §14).
- **Dashboard:** may display boundary/chop/freshness labels read-only; display ≠ Freigabe.
- **Strategy registry:** metadata ≠ Master V2 trading authority ([STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)).

## 21. Hot-path boundary

| Allowed (lightweight) | Forbidden |
|-----------------------|-----------|
| Read pre-authorized static limits | Widening static limits dynamically |
| Update anchor/boundaries per governed formulas | Full vol recompute from raw history each tick |
| Emit/consume scope events per rules | AI / selector / governance recompute |
| O(1) fail-closed envelope checks | Backtest, evidence writes, exchange I/O |

**Invariant:** `HOT_PATH_NO_HEAVY_RECOMPUTE=true`

## 22. Fail-closed semantics

Fail closed (no new scope confirmation / no new side activation eligibility) when:

- envelope or rules invalid
- `SCOPE_UNKNOWN`
- stale data (`freshness_state: stale`) — boundary updates frozen
- missing volatility for `ready_for_dynamic_scope`
- contradictory governance inputs
- missing pre-authorized envelope

Exact runtime mapping to neutral/observe or block arming is governed wiring — **not** authorization from this doc alone.

## 23. Pure stack reference boundary

[MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) §6: pure `transition_state` semantics aligned with manifest; **not** a running runtime state machine. Pure stack tests prove model-only eligibility — **not** runtime integration readiness.

## 24. ops/switch_gate distinction (deferred)

[MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md](MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) references `src/ops/gates/switch_gate.py` hysteresis/cooldown as a **separate** primitive. This contract **does not unify** switch_gate with master_v2 pure state models in v0 (OQ-002). Ownership of unification is **TBD**.

## 25. Validation / future tests pointer

Future behavior tests (separate approval) may include manifest §19 invariants subset:

- trailing behaves correctly in trends
- hard limits never widened dynamically
- confirmation prevents one-tick switching
- chop guard blocks noisy switching
- stale data freezes boundary updates
- Kill-All overrides normal scope trail

Future static-contract tests: **GAP-DSE-STATIC-001** — `tests&#47;ops&#47;test_futures_dynamic_scope_envelope_contract_static_crosslink_contract_v0.py` (~18–22 tests).

## 26. Implementation staging

1. **This docs contract** (current slice) — governance/spec only
2. **Static-contract tests** — GAP-DSE-STATIC-001; separate operator approval; after this merge
3. **Pure-stack handoff alignment** — separate approval; no hot-path wiring by default
4. **State-Switch contract** — after this contract is canonical

## 27. Machine markers (for GAP-DSE-STATIC-001)

```text
MARKER: FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0_EXISTS
MARKER: DYNAMIC_SCOPE_ENVELOPE_DISTINCT_FROM_DEPLOYABLE_CAPITAL
MARKER: STATIC_HARD_LIMITS_NEVER_WIDENED_BY_DYNAMIC_RULES
MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_ENVELOPE
MARKER: DYNAMIC_SCOPE_TRAIL_NOT_KILLSWITCH
MARKER: STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY
MARKER: ENVELOPE_COMPLIANCE_NOT_LIVE_AUTHORIZATION
MARKER: CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT
MARKER: CONFIRMATION_TICKS_VOCABULARY_PRESENT
MARKER: HYSTERESIS_COOLDOWN_VOCABULARY_PRESENT
MARKER: TRAILING_SCOPE_BANDS_VOCABULARY_PRESENT
MARKER: FUTURES_INPUT_READY_FOR_DYNAMIC_SCOPE_CROSSLINK
MARKER: HOT_PATH_NO_HEAVY_RECOMPUTE
MARKER: MANIFEST_SECTION_20_CROSSLINK_TO_THIS_CONTRACT
MARKER: SEQUENCING_BEFORE_STATE_SWITCH_CONTRACT
MARKER: NON_AUTHORIZING_POSTURE
MARKER: NO_DUPLICATION_OF_PR3648_STATE_SWITCH_VS_KILLSWITCH_OWNER
```

## 28. Open questions

| ID | Question | Default posture |
|----|----------|-----------------|
| OQ-001 | Primary volatility metric: ATR vs realized vol vs rolling range? | Governance choice field; fail-closed if unset |
| OQ-002 | Unify switch_gate with master_v2 hysteresis model? | Defer in v0 (§24) |
| OQ-003 | Gate pure `transition_state` on `ready_for_dynamic_scope`? | Fail-closed handoff specified §13; tests separate |
| OQ-004 | Update manifest Related specs crosslink? | Recommended follow-on docs touch |
| OQ-005 | Manifest crosslink in static tests vs manifest edit? | Static tests may pin manifest §20 filename reference |

## 29. Non-goals

- No execution authorization, order placement, or session start
- No live / testnet / paper / shadow readiness promotion
- No broker or exchange connectivity semantics
- No runtime behavior change or hot-path wiring
- No KillSwitch / Kill-All implementation or replacement
- No State-Switch side state machine in this contract
- No `src&#47;trading&#47;master_v2&#47;` changes
- No dashboard feature implementation
- No Market-Airport work
- No evidence → authorization conversion
- No GLB blocker closure or Preflight unblock

## 30. STOP conditions

Stop immediately if:

1. Contract text implies `live_authorization: true` or live readiness
2. Dynamic rules described as widening static hard limits
3. Kill-All conflated with normal scope trail or side switch
4. AI, dashboard, or strategy registry granted envelope authority
5. State-Switch contract drafted before this contract merged
6. Duplicate #3648/#3649 static owners re-pinned without new gap ID
7. Repo change attempted outside approved docs-only slice
8. Scope/Capital clarification collapsed into price-boundary semantics without distinction table
9. Operator protected-scope approval missing for tests or implementation slices

## 31. Cross-references

- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)
- [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md)
- [MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md)
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md)
- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md)
- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md)
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md)
- [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md)
- [MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md)
- [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md)

When this file changes, run `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot` as for sibling ops specs.
