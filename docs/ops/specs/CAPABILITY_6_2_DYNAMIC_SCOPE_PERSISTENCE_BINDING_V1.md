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

## Target residual owner (docs-only; not a runtime bind)

Master Runbook §9.2.3 and
`docs/ops/specs/CAP63_CAP62_DIGEST_AND_CAP65_ADVERSE_RESIDUAL_OWNER_CONTRACT_V1.md`
record the TARGET Cap 6.2 `dynamic_scope_config_digest_v1` identity after
later Cap-6.3 generator-input retirement: digest surface remains Cap 6.2;
material retargets to `derive_scope_event_distances_v1` plus OQ-C2 policy
identity; not retired Cap 6.3 generator numerics; not cycle-varying floats.

That persist does **not** change productive `200.0` / `80.0` / `120.0`,
bind MODEL_C, or authorize a freeze-exception.

Master Runbook §9.2.4 and
`docs/ops/specs/CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_PRECONDITIONS_V1.md`
record freeze-exception **preconditions** (docs-only). A later freeze-exception
would have to name this Cap 6.2 generator-alias freeze explicitly. That
persist does **not** grant the exception, bind MODEL_C, or change productive
distances.

Master Runbook §9.2.5 and
`docs/ops/specs/CAP63_DYNAMIC_DERIVATION_FREEZE_EXCEPTION_V1.md`
record freeze-exception **authority** for this Cap 6.2 generator-alias freeze
(docs-only). That persist does **not** mutate productive `200.0` / `80.0` /
`120.0`, bind MODEL_C, or retire generator inputs.

Master Runbook §9.2.6 and
`docs/ops/specs/CAP63_DYNAMIC_DERIVATION_PURE_FUNCTION_AND_GOLDEN_VECTORS_V1.md`
record the unbound pure function `derive_scope_event_distances_v1`. That
persist does **not** bind this Cap 6.2 package to the function, mutate
productive distances, or retire generator inputs.
