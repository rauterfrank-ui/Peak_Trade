# Event Truth Table — Bollinger EVENT_ONLY

| Raw Signal | Bollinger Event | Direction | Entry Side | Executable Entry | Authority |
|------------|-----------------|-----------|------------|------------------|-----------|
| `+1` | `ENTRY_EVENT` | `NONE` | `NONE` | no (missing side) | contract + adapter |
| `-1` | `EXIT_EVENT` | `NONE` | `NONE` | n&#47;a (exit event) | contract + adapter |
| `0` | `FLAT_NO_EVENT` | `NONE` | `NONE` | no | contract + adapter |
| missing&#47;NaN&#47;invalid | `UNKNOWN_FAIL_CLOSED` | `NONE` | `NONE` | fail-closed | contract |

```text
SIGNAL_PLUS_ONE_MEANS=ENTRY_EVENT
SIGNAL_MINUS_ONE_MEANS=EXIT_EVENT
SIGNAL_ZERO_MEANS=FLAT_NO_EVENT
STRATEGY_DIRECTION=NONE
ENTRY_SIDE=NONE
```
