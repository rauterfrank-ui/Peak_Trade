# Recommended Operator Selection

## Selected option

```text
RECOMMENDED_OPTION=OPTION_D_REMAIN_FAIL_CLOSED
```

## Why (must-hold criteria)

| Criterion | How D satisfies |
|-----------|-----------------|
| Master V2 / Double Play remains system authority | No new side emission; DP untouched |
| Strategy intent ≠ system state | No projection; no invented agreement |
| Long/Short symmetric | Both blocked via NONE |
| `cycle_signal_value` not hidden direction | Preserved (`+1`≠LONG) |
| Missing/contradictory side fail-closed | Current law |
| No legacy authority activation | Unchanged |
| Generalizable | Pattern: keep NONE until producer-scoped ratification |
| Smallest productive follow-on | **No code now**; next is semantic ratification GO |

## Why not A/B/C now

- **A:** Geometry leans LONG mean-reversion, but **authority contract is still AMBIGUOUS** (CP02 class `1 (long)` vs method `1=entry`; parent `BLOCKED_AMBIGUITY`). Emitting LONG before ratification would paper over contradiction.
- **B:** Competing/circular authority — rejected by SSOT analysis.
- **C:** Best long-term architecture, but still requires the same semantic ratification first; implementing the match gate before clarifying producer meaning is premature.

## Repo rule trigger

User rule: if Direction-Semantik not uniquely proven → recommend D + require strategy-semantic ratification.  
Active SSOT: `CONTRACT_REMAINS_AMBIGUOUS` / `BLOCKED_AMBIGUITY` → trigger applies to **entry_side authority**, even though strategy **class** is MEAN_REVERSION.

## Authority owner (now)

```text
RECOMMENDED_AUTHORITY_OWNER=NONE
```

(Future candidates after ratification — not activated here:)

- Intent emission: `src/strategies/bollinger.py::generate_signals` (+ docs)
- Transport: `src/backtest/strategy_signal_suitability_agreement_adapter_v1.py::_resolve_entry_side_carrier_v1`
- System state: `double_play_state.py::transition_state` / composition matrix (unchanged)

## Operator-GO required

```text
OPERATOR_GO_REQUIRED=true
NEXT_RECOMMENDED_ACTION=STRATEGY_SEMANTIC_RATIFICATION_REQUIRED
```

Named ratification candidates (choose exactly one in a later GO; do not auto-select here):

1. `OBL_B05_BOLLINGER_ENTRY_SIDE_LONG_ONLY_SEMANTIC_RATIFICATION_V1` → then TF-style OPTION_A activation
2. `OBL_B05_BOLLINGER_EVENT_ONLY_NO_SIDE_AUTHORITY_RATIFICATION_V1` → freeze event-only forever
3. `OBL_B05_BOLLINGER_STRATEGY_INTENT_AND_DP_AGREEMENT_GATE_V1` → OPTION_C implementation after LONG/SHORT intent defined

## Non-goals of this slice

- No `entry_side` activation
- No productive/test/config mutation
- No PR
- No overwrite of prior reaudit evidence
