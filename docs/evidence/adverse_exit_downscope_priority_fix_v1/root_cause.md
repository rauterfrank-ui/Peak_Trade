# Root Cause

## First value-loss boundary

`src&#47;trading&#47;master_v2&#47;deterministic_scope_event_generator_v1.py` → `_select_directional_kind`

Under research geometry `adverse_exit_distance < up_distance`, a deep adverse move matches
both `ADVERSE_EXIT` and `DOWNSCOPE`. The previous selector preferred `ADVERSE_EXIT`.

## Cascading loss

1. Selected kind = `ADVERSE_EXIT` → `CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE`
2. `integrated_offline_trading_logic_replay_v1._canonical_scope_event_to_scope_event`
   mapped that type unconditionally to `ScopeEvent.SCOPE_UNKNOWN`
3. `transition_state` fail-closes / no-ops on `SCOPE_UNKNOWN` → no SideState downscope path
4. Exit PolicySignal still derived from matched/`ADVERSE_EXIT_CANDIDATE` → exit dimension OK,
   scope/state dimension lost (class-F shadowing)

## Why not invent direction

No LONG/SHORT/ENTRY derivation was added. Only transport of an already-matched `downscope`
fact as `DOWNSCOPE_*`. Without that fact, mapping remains `SCOPE_UNKNOWN` (fail-closed).
