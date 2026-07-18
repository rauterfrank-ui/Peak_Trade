# Canonical Dynamic Scope Trailing State Continuity Repair v1

**Evidence ID:** `canonical_dynamic_scope_trailing_state_continuity_repair_v1_20260718T144407Z`  
**Base HEAD:** `6a92163f492b9dfce3a32ab94b66f90a7982a5a6`

## Verdict

Repair binds RuntimeScopeState as trailing SSOT on the canonical Integrated/Backtest path. CanonicalScopeSnapshotV1 remains identity-only. Per-cycle empty SM input removed. Wiring projects runtime_scope_state_after and derives scope_direction_state from side state. CHOP remains NOT_BOUND_FAIL_CLOSED_GAP. No Live/Orders/Runtime activation.

## Ownership split

| Surface | Owner |
|---------|-------|
| Identity snapshot | CanonicalScopeSnapshotV1 |
| Trailing envelope | RuntimeScopeState + update_dynamic_boundaries + transition_state |
| Orchestrator | run_integrated_offline_trading_logic_replay_v1 |
| Bar continuity | mv2_research_wiring_v1 sequence state |

## Tests

135 passed (8 new continuity + integrated + research wiring).

## Non-goals preserved

Bollinger entry_side, composition semantics, risk/sizing, execution, dashboard untouched.
