---
title: "Canonical Dynamic Scope Trailing State Continuity Contract v1"
status: "ACTIVE"
owner: "trading.master_v2"
last_updated: "2026-07-18"
docs_token: "DOCS_TOKEN_CANONICAL_DYNAMIC_SCOPE_TRAILING_STATE_CONTINUITY_CONTRACT_V1"
---

# Canonical Dynamic Scope Trailing State Continuity Contract v1

## 1. Purpose

Freeze a **single** ownership split for Dynamic Scope on the **canonical offline / backtest** path so that:

```text
SCOPE(t) + finalized_market_event(t+1) → SCOPE(t+1)
SCOPE(t+1) → current trailing envelope of the next decision cycle
```

This contract is **docs + code-aligned**. It does **not** authorize Live, Testnet, Orders, or Runtime-Bridge activation.

## 2. Ownership split (no second truth)

| Surface | Owner | Role |
|---------|-------|------|
| Identity / evidence snapshot | `CanonicalScopeSnapshotV1` via `initialize_canonical_scope` | Immutable identity carrier; **not** the moving trailing envelope |
| Trailing envelope SSOT | `RuntimeScopeState` via `update_dynamic_boundaries` + `transition_state` | Stateful SCOPE(t)→SCOPE(t+1) on one instrument |
| Scope events | `generate_deterministic_scope_event` | Consumes **trailing_anchor from RuntimeScopeState**; does not mutate snapshot |
| Orchestrator | `run_integrated_offline_trading_logic_replay_v1` | Seeds/continues RuntimeScopeState; returns `runtime_scope_state_after` |
| Bar continuity | `mv2_research_wiring_v1` sequence state | Feeds `runtime_scope_state_after` into next bar |

**Forbidden:** per-cycle `_EMPTY_SCOPE_STATE` as SM input; treating `CanonicalScopeSnapshot.trailing_anchor` as the sole moving envelope; discarding `transition_state` scope return.

## 3. Initialization / reset

Re-initialize RuntimeScopeState **only** when:

1. First cycle for an instrument (`runtime_scope_state is None`), or
2. `explicit_runtime_scope_reset=true`, or
3. Instrument mismatch (`runtime_scope_bound_instrument_id != instrument_id`) — fail-closed re-seed.

## 4. CHOP

`CHOP_BINDING_STATUS=BOUND_AS_SCOPE_POLICY` via
`chop_scope_event_policy_binding_v1` / `RuntimeScopeState.chop_latched`.

The deterministic generator still has **no market emission heuristic** for
`CHOP_DETECTED` (`CHOP_POLICY_STATUS=BOUND_AS_SCOPE_POLICY_NO_EMISSION_HEURISTIC`).
When a CHOP event is present (e.g. TEST_ONLY injection), it binds as scope policy
only — never as Direction or Switch.

## 5. Non-authority

`LIVE_AUTHORIZED=false`, no orders, Runtime Bridge remains `BOUND_NOT_ACTIVATED`.
