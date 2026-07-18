# Option Matrix

## OPTION_A_EXPLICIT_PRODUCER_SIDE

| Field | Assessment |
|-------|------------|
| Meaning | Bollinger producer contract ratifies ENTRY→LONG (and/or SHORT if ever implemented); adapter transports only (TF pattern) |
| Authority owner | Producer contract + adapter ratification list |
| Producer | Align `bollinger.py` docs/geometry to explicit side; optionally emit side metadata |
| Adapter | Add `bollinger_bands` to ratified owners like `trend_following` |
| Agreement | Resolves directional cycle when LONG/SHORT present |
| Long/Short symmetry | Currently LONG-only geometry; SHORT would need new producer rules — **not symmetric today** |
| Second-truth risk | **MEDIUM** if docs remain CP02-contradictory while emitting LONG |
| Hidden direction risk | **LOW** if adapter stays producer-scoped and never uses `+1` alone |
| Productive files | `bollinger.py` (doc/contract), adapter ratification set, possibly governance SSOT |
| Contract tests | LONG ENTRY emit; EXIT→NONE; no `+1` invent; non-Bollinger unchanged; Surface-P regression |
| Migration | Touches only Bollinger + adapter allowlist |
| Backward compat | Historical NONE behavior becomes LONG — intentional GO |
| Fail-closed | Missing/contradictory → still NONE until ratification complete |
| Zero-trade impact | Unblocks DA for ENTRY bars; next blocker likely composition (TF precedent) |
| **Recommendation** | **CONDITIONAL** — only after semantic ratification resolves CP02; **not** now |

## OPTION_B_CANONICAL_STATE_PROJECTION

| Field | Assessment |
|-------|------------|
| Meaning | `entry_side` projected from selected Bull/Bear future; Bollinger only ENTRY/EXIT |
| Authority owner | Would effectively be composition/DP → **wrong** |
| Producer | Unchanged event carrier |
| Adapter | Would invent side from system state |
| Agreement | Tautological self-agreement |
| Long/Short symmetry | Apparent, but fake |
| Second-truth risk | **HIGH** |
| Hidden direction risk | **HIGH** |
| Productive files | Wiring/adapter projection (forbidden pattern) |
| **Recommendation** | **REJECT** |

## OPTION_C_STRATEGY_AND_CANONICAL_AGREEMENT

| Field | Assessment |
|-------|------------|
| Meaning | Explicit strategy intent + fail-closed match vs canonical Double-Play selected future |
| Authority owner | Producer (intent) + DP (state) + agreement gate (match) |
| Producer | Explicit intent after ratification |
| Adapter | Transport intent only |
| Agreement | Accept only on intent↔selected_side match; else fail-closed |
| Long/Short symmetry | Policy can be symmetric; Bollinger still LONG-only until SHORT geometry exists |
| Second-truth risk | **LOW** if roles separated |
| Hidden direction risk | **LOW** |
| Productive files | Producer + adapter + agreement match gate (new/extended contract) |
| Contract tests | Match PASS; mismatch BLOCK; NONE BLOCK; unbound state BLOCK; LONG/SHORT cases |
| Migration | Larger than TF-style A; generalizable to other ENTRY_EXIT owners |
| Backward compat | Need explicit versioning of agreement gate |
| Fail-closed | Strong |
| Zero-trade impact | Unblocks only when intent and DP agree — correct economically |
| **Recommendation** | **CONDITIONAL** — preferred *architecture* after ratification; **not** first without semantic GO |

## OPTION_D_REMAIN_FAIL_CLOSED

| Field | Assessment |
|-------|------------|
| Meaning | Keep `entry_side=NONE`; Bollinger not executable until strategy semantics ratified |
| Authority owner | NONE (intentional) |
| Producer / Adapter | Unchanged |
| Agreement | Continues `BLOCKED_DIRECTIONAL_AGREEMENT` |
| Long/Short symmetry | Symmetric block |
| Second-truth risk | **NONE** |
| Hidden direction risk | **NONE** |
| Productive files | None |
| Contract tests | Existing OBL_B05 / Decision D invariants remain green |
| Migration | None |
| Backward compat | Full |
| Fail-closed | Preserved |
| Zero-trade impact | Unchanged (TRADE_COUNT=0) |
| **Recommendation** | **ACCEPT** (current Operator selection) |

## Summary

| Option | Verdict |
|--------|---------|
| A | CONDITIONAL (post-ratification) |
| B | REJECT |
| C | CONDITIONAL (preferred post-ratification architecture) |
| D | **ACCEPT now** |
