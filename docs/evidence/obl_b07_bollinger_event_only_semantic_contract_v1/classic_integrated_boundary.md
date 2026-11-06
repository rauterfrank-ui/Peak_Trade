# Classic vs Integrated Boundary

```text
CLASSIC_LONG_IS_CANONICAL=false
CLASSIC_LONG_PROPAGATES_TO_INTEGRATED=false
```

## Classic

`BacktestEngine.run_realistic` may treat strategy `signal==1` as LONG ENTRY and
`signal==-1` as EXIT of an open long. That is a **legacy engine reinterpretation**,
not the Bollinger Strategy-Intent contract ratified here.

## Integrated &#47; MV2

- Bollinger `+1` → `event_kind=ENTRY`, `entry_side=NONE`
- `resolve_agreement_bound_directional_cycle_v1` → `None` (not executable)
- No Classic-LONG carrier is invented or forwarded

## This slice

- Does **not** change Classic engine behavior
- Does **block** any reading of Classic-LONG as Integrated Bollinger Intent
  by binding Bollinger through the EVENT_ONLY contract with forced `NONE` side
