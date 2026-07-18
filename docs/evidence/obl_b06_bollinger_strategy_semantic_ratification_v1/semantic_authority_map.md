# Semantic Authority Map — Bollinger (OBL_B06)

## Layers (must stay distinct)

| Layer | Bollinger status | Authority |
|-------|------------------|-----------|
| Mathematical raw signal | **CONFIRMED** `{-1,0,+1}` series | `src/strategies/bollinger.py::generate_signals` |
| Strategy Intent (LONG/SHORT/FLAT) | **NOT RATIFIED** for LONG/SHORT | `NONE` — CP02 / Decision C |
| Desired Entry Side carrier | **FAIL-CLOSED `NONE`** | Adapter `_resolve_entry_side_carrier_v1` (only TF ratified) |
| System / Bull-Bear state | Separate; unchanged | Master V2 / Double Play |
| Exit / Close Intent | **CONFIRMED** as EXIT on `-1` | Producer + adapter event_kind |
| Position Target | Not emitted by Bollinger | N/A (sizing/execution out of scope) |

## Productive emission geometry

```
close cross lower*entry_threshold down  →  +1
close cross middle up                   →  -1
else                                    →   0
upper-band short entry                  →  ABSENT
```

## Doc / contract contradictions blocking LONG ratification

| ID | Conflict |
|----|----------|
| CP02 | Class doc `1 (long)` vs method return `1=entry` |
| CP01 | BaseStrategy ±1 long/short vocab vs ENTRY_EXIT encoding |
| CP03 | Registry `supported_sides=(long,short)` vs one-sided geometry |
| Decision D | `+1` is ENTRY event, never automatic LONG authority |
| Parent SSOT | `bollinger_entry_side_decision=BLOCKED_AMBIGUITY` |
| Path split | Classic engine treats `+1` as LONG buy; Integrated keeps `entry_side=NONE` |

## Ratification criterion applied

A semantics claim is confirmed only with **productive authority + matching tests / repo-wide contract chain**.

| Claim | Result |
|-------|--------|
| `-1` = EXIT event (never SHORT) | **CONFIRMED** |
| `+1` = ENTRY event kind | **CONFIRMED** (adapter) |
| `+1` = LONG Strategy Intent / entry_side LONG | **NOT CONFIRMED** |
| `+1` = SHORT | **FALSE** |
| Upper-band → SHORT Intent | **FALSE** (no geometry) |
| Classic ≡ Integrated side meaning | **NOT ALIGNED** |

## Missing authority (blocker)

```text
RATIFICATION_BLOCKER=BOLLINGER_STRATEGY_INTENT_LONG_SHORT_AUTHORITY_MISSING
MISSING=
  1) Explicit Operator-GO choosing exactly one of:
     - LONG_ONLY_ENTRY_EXIT (producer docs + method aligned; activate entry_side=LONG on ENTRY)
     - EVENT_ONLY_NO_SIDE_AUTHORITY (freeze forever; document classic-engine reinterpretation as non-canonical)
     - SYMMETRIC_LONG_SHORT_MEAN_REVERSION (requires NEW upper-band SHORT geometry — out of this slice)
  2) Productive producer contract text that removes CP02 (class vs method)
  3) Path-equivalence decision: classic engine LONG reinterpretation vs Integrated ENTRY_EXIT NONE
```

## Forbidden inferences (held)

- No cycle / Bull-Bear / position-derived side
- No generic `sign(signal)` heuristic for Bollinger
- No competing authority via `compose_double_play_decision`
