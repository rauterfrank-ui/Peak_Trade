# Contract Before / After

## Before

| Dimension | Behavior |
|-----------|----------|
| Generator select | nested adverse+downscope → `ADVERSE_EXIT` wins |
| Canonical event | `ADVERSE_EXIT_CANDIDATE` |
| ScopeEvent map | always `SCOPE_UNKNOWN` |
| PolicySignal | `triggered=True` (exit preserved) |
| `transition_state` | no `DOWNSCOPE_*` → SideState frozen |

## After

| Dimension | Behavior |
|-----------|----------|
| Generator select | `DOWNSCOPE` / `UPSCOPE` before `ADVERSE_EXIT` |
| Canonical event | nested → `DOWNSCOPE_*` (or `UPSCOPE_*`); adverse-only → `ADVERSE_EXIT_CANDIDATE` |
| matched_conditions | still contains `adverse_exit` when band matched |
| ScopeEvent map | `ADVERSE_EXIT_CANDIDATE` + matched `downscope` → `DOWNSCOPE_CANDIDATE`; else `SCOPE_UNKNOWN` |
| PolicySignal | still derived from event type **or** matched `adverse_exit` |
| `transition_state` | receives specific `DOWNSCOPE_*` when fact present |

## Dual-dimension invariant

```text
policy_signal  = ADVERSE_EXIT   (PolicySignal / exit consumer)
scope_event    = DOWNSCOPE_*    (ScopeEvent → transition_state)
```

Neither dimension overwrites the other. No new enums/contracts.
