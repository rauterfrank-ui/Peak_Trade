# Classic vs Integrated Interpretation — Bollinger

## Verdict

```text
CLASSIC_INTEGRATED_SEMANTICS_ALIGNED=false
```

Same raw series from `BollingerBandsStrategy.generate_signals`, **different consumer meaning** for `+1`.

## Side-by-side

| Signal | Classic `BacktestEngine.run_realistic` | Integrated Adapter → MV2 |
|--------|----------------------------------------|---------------------------|
| `+1` | **LONG ENTRY** (opens long if flat) — `engine.py` ~654–655 | **ENTRY event**, `entry_side=NONE` → no directional cycle |
| `-1` | **EXIT** open long — ~835–837 (doc “Sell” = exit, not short open) | **EXIT event**, never SHORT; suitability demotion |
| `0` | Hold | `event_kind=NONE` / NEUTRAL |

## Why this blocks ratification

Ratifying `entry_side=LONG` would align Integrated with Classic’s long-only treatment **without** resolving producer CP02 (class `1 (long)` vs method `1=entry`) and without an Operator-GO that declares Classic’s reinterpretation either:

- **canonical Strategy Intent**, or
- **legacy non-authority** relative to Decision D / ENTRY_EXIT carrier law.

Until that GO exists, Integrated correctly remains fail-closed (`NONE`).

## Double Play / Legacy

| Path | Affects Bollinger `entry_side`? |
|------|----------------------------------|
| `compose_double_play_decision` | **false** |
| Adapter `_resolve_entry_side_carrier_v1` | **true** (forces `NONE` for Bollinger) |
| Classic engine | Reinterprets signal as long-only trades; **not** `entry_side` carrier |

## Suitability consumer note (not side authority)

`suitability_binding_v1.py` ENTRY impulse “agrees only with LONG DA” is a **consumer bias** for agreement scoring when an ENTRY event is present. It does **not** emit or invent `entry_side=LONG` for Bollinger.
