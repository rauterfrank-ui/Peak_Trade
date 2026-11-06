# Fill-Conversion Classification

## Legend

| Class | Meaning |
|-------|---------|
| CONVERTED | ≥1 offline trade materialized |
| NO_ENTRY_INTENT | no `enter_long`/`enter_short` |
| INTENT_TO_MAPPED_SIGNAL_DROP | enter present but mapped signal 0 (**mechanical**) |
| MAPPED_TO_ENGINE_SIGNAL_DROP | mapped nonzero lost before engine series (**mechanical**) |
| ENGINE_SIGNAL_PRESENT_LEDGER_ZERO_TRADE | engine nonzero bars but `total_trades=0` |
| FUNNEL_ENGINE_ALIGNMENT_ANOMALY | mapped ≠ engine series (**mechanical**) |

## Result

- **CONVERTED**: 63
- **ENGINE_SIGNAL_PRESENT_LEDGER_ZERO_TRADE**: 52
- **NO_ENTRY_INTENT**: 3
- Mechanical classes: **0**

## First drop boundary (panel-level)

For the 52 enter+zero-trade instruments:

`PRIMARY_DROP_BOUNDARY=backtest_engine_fill_or_roundtrip_ledger`

Observed pattern: enter intents map 1:1 to engine nonzero bars; median impulse
length is 1 bar. Round-trip ledger materialization remains sparse. This is
**not** Intent→Map adapter loss and **not** a second-authority / classic bypass.

## Cross-cutting

| Question | Answer |
|----------|--------|
| Mechanical Intent→Map defect? | No (`enter_map_mismatch_count` sum = 0) |
| Mechanical Map→Engine defect? | No (`enter_engine_mismatch_count` sum = 0) |
| Funnel/engine alignment? | Yes on all 118 |
| Classic bypass / 2nd authority? | No |
| Systemwide zero-trade? | No (69 trades / 63 instruments) |
| Dominant enter side | SHORT (4157 vs LONG 69) |
