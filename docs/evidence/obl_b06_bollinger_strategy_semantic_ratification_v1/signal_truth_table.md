# Signal Truth Table — Bollinger (OBL_B06)

Rule: no meaning from folklore; only productive geometry + adapter/engine contracts.

| Rohsignal | Marktbedingung (productive) | Strategy Intent | Entry Side | Exit Intent | System State Dependency | Authority-Quelle | Ratification Status |
|-----------|----------------------------|-----------------|------------|-------------|-------------------------|------------------|---------------------|
| `+1` | Close kreuzt `lower * entry_threshold` von oben nach unten | **AMBIGUOUS** (ENTRY event vs LONG-leaning docs; no SHORT) | `NONE` | none | none (must not derive) | Producer geometry + adapter ENTRY; classic engine LONG reinterpretation **non-canonical for MV2** | **NOT_RATIFIED** for LONG Intent / entry_side |
| `-1` | Close kreuzt `middle` von unten nach oben | EXIT / close-long-candidate (event) | `NONE` | **EXIT** | none | Producer `signals[cross_exit]=-1` + adapter `event_kind=EXIT` + B05 SSOT | **CONFIRMED** as EXIT (never SHORT) |
| `0` | weder Entry- noch Exit-Kreuzung | FLAT / NO_ENTRY event | `NONE` | none | none | Producer default 0 + adapter `event_kind=NONE` | **CONFIRMED** as neutral/FLAT event |
| *(absent)* | Preis am oberen Band / Overbought | — | — | — | — | No productive SHORT geometry | **NOT_IMPLEMENTED** |
| Missing signal | binding/epoch invalid | fail-closed | `NONE` | — | — | Adapter raises / consumer flat | **FAIL_CLOSED** |
| Direction conflict | entry_side missing vs DA | unresolved agreement | `NONE` | — | DA separate | MV2 directional_agreement block | **FAIL_CLOSED** |

## Summary encodings

```text
SIGNAL_PLUS_ONE_MEANS=AMBIGUOUS
SIGNAL_MINUS_ONE_MEANS=EXIT
SIGNAL_ZERO_MEANS=FLAT
ENTRY_SIDE_CURRENT=NONE
BOLLINGER_SHORT_EMISSION=false
GENERIC_SIGN_HEURISTIC=false
```

## Hypothesis rejection notes

1. **Lower-band → LONG Intent:** plausible in module/class docs and classic engine, but **blocked** by method contract (`1=entry`), Decision D, and B05 Decision C (`CONTRACT_REMAINS_AMBIGUOUS`).
2. **Upper-band → SHORT Intent:** **rejected** — no productive condition.
3. **Neutral → FLAT:** accepted as event-level NO_ENTRY (`0`), not as ratified positional flat authority.
