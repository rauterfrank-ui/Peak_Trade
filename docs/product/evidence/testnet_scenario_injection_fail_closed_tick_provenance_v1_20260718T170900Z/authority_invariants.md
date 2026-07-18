# Authority Invariants (preserved)

- CANONICAL_SCOPE_STATE_OWNER = `trading.master_v2.double_play_state.RuntimeScopeState`
- CANONICAL_SWITCH_AUTHORITY = `trading.master_v2.double_play_state.transition_state`
- Ordering: DynamicScopeUpdate → ScopeEvent → transition_state
- Injection supplies test ScopeEvent input only; no direct Direction/Side/Switch write
- CHOP remains scope-policy-only
- LIVE_AUTHORIZED=false, ORDERS_ENABLED=false, RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
- Collateral: default minimal chop_guard fixture `transition_allowed` aligned to CHOP policy (`True` = policy applied, SideState unchanged)
