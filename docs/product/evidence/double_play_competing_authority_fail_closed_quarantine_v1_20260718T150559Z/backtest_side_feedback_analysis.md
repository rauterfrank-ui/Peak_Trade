# Backtest Side Feedback Analysis

## Before

`capture_backtest_engine_position_feedback_v1` mapped:

- open trade → `SideState.LONG_ACTIVE` + LONG direction
- flat → `SideState.LONG_ARMED` + LONG direction

`apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1` overwrote
`side_state`, `direction_state`, and `scope_direction_state` — competing with
`transition_state` continuity.

## After

- Capture emits **NEUTRAL** SideState/direction placeholders and position
  observation (`ExistingPositionSide`, `PositionState`, `venue_flat`,
  `position_management_context`) with `authority_role=OBSERVATION_ONLY`.
- Apply overlays **only** position/reconciliation/venue/management fields.
- Does **not** overwrite SideState, direction_state, scope_direction_state, or
  RuntimeScopeState.
- Flat/NONE remains NONE for position side; no Direction invention from flat.
- Open position reports LONG as **position observation** (legacy engine is
  long-only) without writing Bull SideState authority.

## Status

`BACKTEST_SIDE_FEEDBACK_STATUS=OBSERVATION_ONLY`  
`SINGLE_CYCLE_BEHAVIOR_CHANGED=true` (feedback no longer forces LONG_* SideState)  
`MULTI_CYCLE_TRAILING_BEHAVIOR_PRESERVED=true` (RuntimeScopeState trail unchanged)
EOF