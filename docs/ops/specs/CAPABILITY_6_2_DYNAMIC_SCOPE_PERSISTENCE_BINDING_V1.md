---
docs_token: DOCS_TOKEN_CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1
status: active
scope: productive Dynamic Scope RuntimeScopeState persistence + restart; no activation
capability: CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-02
---

# Capability 6.2 — Dynamic Scope Persistence Binding V1

## Goal

Carry the existing canonical `RuntimeScopeState` continuously through productive
cycles and restart without changing Dynamic Scope rules or numeric values.

```text
CORE_LOGIC_CHANGE=false
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```

## Target graph

```text
Confirmed Directional State
→ Previous Canonical RuntimeScopeState
→ Dynamic Scope Transition
→ New Canonical RuntimeScopeState
→ kanonischer State Commit
→ nächster produktiver Zyklus
→ Restart Reload
→ deterministisch identische Fortsetzung
```

## Productive owners

| Surface | Owner |
| --- | --- |
| Trailing SSOT | `trading.master_v2.double_play_state.RuntimeScopeState` |
| Identity snapshot | `CanonicalScopeSnapshotV1` |
| Transition | `transition_state` / `update_dynamic_boundaries` |
| Decision | `run_integrated_offline_trading_logic_replay_v1` |
| Host binding | `ops.dynamic_scope_persistence_binding_v1` |
| Cap 6.1 handoff | `ops.stateful_confirmation_and_c1_productive_binding_v1` |
| Productive host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` |

## Persistence

Schema is derived from `RuntimeScopeState` and `CanonicalScopeSnapshotV1` only.
No parallel scope decision authority. No change to
`up_distance=200.0`, `adverse_exit_distance=80.0`, `reversal_distance=120.0`.

## Reset semantics

Silent `existing_scope=None` reinitialization is eliminated on the productive
path except for classified resets:

- `FIRST_EVER_STATE`
- `OWNER_AUTHORIZED_RESET`
- `INSTRUMENT_IDENTITY_CHANGE`
- `CANONICAL_INVALIDATION_TRANSITION`
- `STATE_VERSION_MIGRATION`
- `GOVERNED_RECOVERY`

## Activation

```text
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```
