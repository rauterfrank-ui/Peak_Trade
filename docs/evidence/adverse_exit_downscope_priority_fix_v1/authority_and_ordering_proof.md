# Authority and Ordering Proof

## Canonical owners (unchanged)

| Role | Owner |
|------|-------|
| Direction / SideState | `trading.master_v2.double_play_state.transition_state` |
| Composition | `trading.master_v2.double_play_composition_matrix_v1.evaluate_double_play_composition_matrix_v1` |

## Why no second authority

- Generator/adapter only select and map **facts** (`matched_conditions`, event type).
- They do not set final SideState, entry side, or composition outcome.
- Defense-in-depth map only emits `DOWNSCOPE_CANDIDATE` when `downscope` is already matched.
- Sole-authority quarantine tests remain green.

## Ordering (preserved)

```text
DynamicScopeUpdate → ScopeEvent → transition_state
```

Replay maps generator evidence → `ScopeEvent` before `transition_state`. No post-adapter
rewrite of a specific downscope back to `SCOPE_UNKNOWN` when the downscope fact is present.

## Bull / Bear / Long / Short

- Long/Bull adverse nested band: downscope selected; adverse matched → exit signal.
- Short/Bear mirrored fixtures: same dual-dimension contract.
- No LONG-default invented when context is short or unknown.
- Adverse without downscope fact: exit preserved; scope remains fail-closed unknown.

## Bypass / runtime

- No classic-engine bypass introduced.
- `RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`
- `LIVE_AUTHORIZED=false`, `ORDERS=false`
- `entry_side=NONE` remains valid strategy initial state.
