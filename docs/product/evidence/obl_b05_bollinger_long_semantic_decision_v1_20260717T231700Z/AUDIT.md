# AUDIT — Bollinger Long-Semantic Decision v1

## Decision

`BOLLINGER_DECISION=CONTRACT_REMAINS_AMBIGUOUS`

- Variant A rejected: productive docs&#47;adapter&#47;parent SSOT not consistently long-only.
- Variant B rejected: producer not ratified as side-neutral authority class.
- No productive `src/` mutation. `entry_side` remains NONE.

## Quantitative panel baseline

| Metric | Value |
|---|---:|
| total bars | 348454 |
| Bollinger ENTRY (`+1`) | 185 |
| Bollinger EXIT (`-1`) | 20754 |
| entry_side NONE on ENTRY | 185 |
| first_failed_stage DA | 185 |
| ENTER outcomes | 0 |
| SHORT reference (`rsi_reversion` `-1`) | 53870 |

## Invariants verified

- `-1` never interpreted as SHORT for Bollinger
- EXIT never emits LONG&#47;SHORT
- MACD&#47;other producers unchanged
- LIVE&#47;ORDERS false
