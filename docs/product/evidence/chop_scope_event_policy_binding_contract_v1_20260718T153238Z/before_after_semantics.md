# Before / After — CHOP Scope Event Policy Binding

## Before
- CHOP_BINDING_STATUS=NOT_BOUND_FAIL_CLOSED
- ScopeEvent.CHOP_DETECTED → SideState.CHOP_GUARD_BLOCK (SideState mutation)
- Composition both_sides_confirmed → chop_guard_status=CHOP_GUARD_BLOCK (second CHOP-named truth)
- DUPLICATE_AUTHORITY_REMAINDER deferred

## After
- CHOP_BINDING_STATUS=BOUND_AS_SCOPE_POLICY
- ScopeEvent.CHOP_DETECTED → RuntimeScopeState.chop_latched (SideState unchanged)
- Active latch blocks arming/activation/switch confirmations via transition_state gate
- Trailing freeze while latched
- Composition consumes scope_chop_policy_active as projection only
- both_sides_confirmed = COMPOSITION_CONFLICT_NOT_SCOPE_CHOP_SSOT (chop_guard_status=NONE)
- UNKNOWN remains NOT_BOUND_FAIL_CLOSED
- CHOP_SEMANTIC_SSOT_COUNT=1
