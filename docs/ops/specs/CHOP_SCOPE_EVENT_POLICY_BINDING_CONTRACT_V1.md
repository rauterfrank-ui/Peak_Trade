---
title: "CHOP Scope Event Policy Binding Contract v1"
status: "ACTIVE"
owner: "trading.master_v2"
last_updated: "2026-07-18"
docs_token: "DOCS_TOKEN_CHOP_SCOPE_EVENT_POLICY_BINDING_CONTRACT_V1"
---

# CHOP Scope Event Policy Binding Contract v1

## 1. Problem

CHOP existed as two related but separate semantics:

1. **Scope-CHOP** — `ScopeEvent.CHOP_DETECTED` processed inside `transition_state`,
   historically writing `SideState.CHOP_GUARD_BLOCK`.
2. **Composition-CHOP** — `both_sides_confirmed` in the composition matrix emitting
   `CompositionStatus.CHOP_GUARD_BLOCK` / `CompositionChopGuardStatus.CHOP_GUARD_BLOCK`
   independently of any ScopeEvent.

Binding status was `NOT_BOUND_FAIL_CLOSED`. The deferred remainder was classified as
`DEFERRED_DUPLICATE_SEMANTIC_NOT_SWITCH_AUTHORITY`.

## 2. Previous semantic duplication

| Surface | Former role | Problem |
|---------|-------------|---------|
| `ScopeEvent.CHOP_DETECTED` → `SideState.CHOP_GUARD_BLOCK` | SideState rewrite via CHOP | CHOP mutated SideState |
| Matrix `both_sides_confirmed` → `chop_guard_*` | Independent "CHOP" label | Second CHOP-named truth |
| Generator `CHOP_POLICY_STATUS=NOT_BOUND` | No emission heuristic | Consumption unbound |

## 3. Canonical owner

| Role | Owner |
|------|-------|
| CHOP input event | `ScopeEvent.CHOP_DETECTED` |
| CHOP scope-policy binding | `apply_chop_scope_event_policy_v1` |
| Trailing Scope State SSOT | `RuntimeScopeState` (`chop_latched`) |
| Bull/Bear SideState + Switch | `transition_state` (unchanged sole owner) |
| Composition CHOP label | Consumer projection only |

`CHOP_BINDING_STATUS=BOUND_AS_SCOPE_POLICY`
`CHOP_SEMANTIC_SSOT_COUNT=1`

## 4. Event / Policy / Consumer separation

```text
ScopeEvent.CHOP_DETECTED
  → apply_chop_scope_event_policy_v1
  → RuntimeScopeState(t+1).chop_latched = true   (defensive scope policy)
  → SideState unchanged
  → Composition may project chop_guard from scope_chop_policy_active
```

- **Input:** ScopeEvent (not an owner).
- **Policy result:** `ChopScopePolicyStatus` + `chop_latched` (not Direction / Switch).
- **Consumer:** Composition matrix via `scope_chop_policy_active` projection.
- **Conflict (not Scope-CHOP):** `both_sides_confirmed` →
  `COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT`.

## 5. Allowed CHOP behaviour

- Latch / freeze / defensively constrain Dynamic Scope (`chop_latched`, trailing freeze).
- Block entry / composition directional selection via projection.
- Appear as ScopeEvent evidence and policy reason codes.
- Persist across cycles via RuntimeScopeState continuity.
- Clear only via canonical recovery (`NOOP` while latched).

## 6. Forbidden CHOP behaviour

- Create LONG or SHORT / invent Direction.
- Select Bull or Bear.
- Replace `transition_state`.
- Trigger a Bull↔Bear switch.
- Rewrite an existing SideState (including writing `CHOP_GUARD_BLOCK`).
- Become a second Switch / SideState / Scope-State authority.
- Be permissively overridden by Composition, Adapter, Scenario, Ops, or Legacy paths.

## 7. UNKNOWN boundary

`UNKNOWN_BINDING_STATUS=NOT_BOUND_FAIL_CLOSED`

- No productive UNKNOWN binding in this slice.
- `SCOPE_UNKNOWN` remains fail-closed (no SideState change, no Direction, no Switch).

## 8. Multi-cycle behaviour

- `RuntimeScopeState(t+1)` carries `chop_latched` forward.
- No reset to empty scope on CHOP.
- Idempotent re-application of `CHOP_DETECTED` keeps latch true.
- Recovery: `NOOP` clears latch without SideState rewrite.

## 9. Fail-closed rules

Missing / contradictory / unbound CHOP context:

- no Direction
- no Switch
- no entry release
- no permissive composition fallback
- deterministic `FAIL_CLOSED` / block-observe reason codes

## 10. Authority invariants

```text
SOLE_SCOPE_STATE_OWNER=RuntimeScopeState
SOLE_BULL_BEAR_STATE_OWNER=transition_state
SOLE_SWITCH_AUTHORITY=transition_state
COMPOSITION_CHOP_STATUS=CONSUMER_PROJECTION_ONLY
CHOP_CAN_CREATE_DIRECTION=false
CHOP_CAN_TRIGGER_SWITCH=false
CHOP_CAN_MUTATE_SIDE_STATE=false
CHOP_CAN_BYPASS_TRANSITION_STATE=false
PRODUCTIVE_CHOP_BYPASS_PATHS=0
PRODUCTIVE_COMPETING_AUTHORITIES=0
DYNAMIC_SCOPE_PRECEDES_SWITCH=true
MULTI_CYCLE_SCOPE_CONTINUITY=true
BACKTEST_RUNTIME_AUTHORITY_PARITY=FULL
```

Scenario injection remains `TEST_ONLY_GUARDED`.
Backtest feedback remains `OBSERVATION_ONLY`.
Ops remains `PROJECTION_DIAGNOSTIC_ONLY`.

## 11. Test matrix

| Case | Expectation |
|------|-------------|
| Non-CHOP Bull / Bear | Unchanged SideState transitions |
| CHOP at Bull / Bear | No auto-switch; no new Direction; latch + entry block |
| CHOP without SideState | No invented SideState |
| Multi-cycle CHOP | Latch continuity; trailing freeze |
| CHOP → Non-CHOP (NOOP) | Latch clear only via scope policy |
| UNKNOWN | Still NOT_BOUND_FAIL_CLOSED |
| Scenario injection | TEST_ONLY only |
| Composition | Consumer projection; both_sides = conflict not Scope-CHOP |
| Missing context | Fail-closed |

Focused owner: `tests&#47;trading&#47;master_v2&#47;test_chop_scope_event_policy_binding_contract_v1.py`

## 12. Runtime / Live non-activation

`LIVE_AUTHORIZED=false`
`ORDERS_ENABLED=false`
`RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`

No Live, Testnet, Orders, Scheduler, Capital, or Runtime-Bridge activation.

## 13. Code owners

- `src&#47;trading&#47;master_v2&#47;chop_scope_event_policy_binding_v1.py`
- `src&#47;trading&#47;master_v2&#47;double_play_state.py` (binding call sites)
- `src&#47;trading&#47;master_v2&#47;double_play_composition_matrix_v1.py` (consumer projection)
EOF
