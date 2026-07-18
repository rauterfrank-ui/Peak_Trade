# Authority Recheck (post-change)

| Surface | Ehlers | Bouchaud |
|---|---|---|
| Research-only / `IS_LIVE_READY` | true / false | true / false |
| Execution eligible | false | false |
| Canonical MV2 bound | false | false |
| Direct Long/Short system authority | false (signals only if selected offline) | false |
| Dynamic Scope / Switch | false | false |
| Agreement/CRS/Order Intent force | false | false |
| Risk/Sizing/Execution | false | false |
| Combined aggregator | none | none |

Callers of strategy classes remain: package `__init__`, `registry.py`, STEP29M research/backtest admissibility adapters — **no** `src/trading/master_v2` references.

- COMPETING_AUTHORITY_COUNT_AFTER=0
- LEGACY_PRODUCTIVE_COUNT_AFTER=0
- MASTER_V2_CHANGED=false
- DOUBLE_PLAY_CHANGED=false
- RISK_SIZING_EXECUTION_CHANGED=false
