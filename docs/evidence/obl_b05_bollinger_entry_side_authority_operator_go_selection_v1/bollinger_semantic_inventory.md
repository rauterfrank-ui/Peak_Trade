# Bollinger Semantic Inventory (Forensic)

**Rule:** No semantics guessed from market folklore. Only repo evidence.

## Primary productive producer

| Field | Value |
|-------|-------|
| File | `src/strategies/bollinger.py` |
| Class | `BollingerBandsStrategy` |
| KEY / Config-ID | `bollinger_bands` / `strategy.bollinger_bands` |
| Function | `generate_signals` |
| Registry | `src/strategies/registry.py` → `"bollinger_bands"` → description `"Bollinger Bands Mean-Reversion"` |

### Geometry (code, not docs alone)

| Event | Condition | Signal value |
|-------|-----------|--------------|
| ENTRY | Close crosses `entry_level = lower * entry_threshold` from above to below | `+1` |
| EXIT | Close crosses `middle` from below to above | `-1` |
| Neutral | else | `0` |

- **Upper-band SHORT entry:** not implemented (`short_entry_condition_present=false` per SSOT).
- **Mean-reversion tags:** metadata `tags=["mean-reversion", "volatility", "bollinger"]`, `regime="ranging"`.
- **Strategy class (geometry):** **MEAN_REVERSION** (lower-band entry → middle exit). Not breakout/trend geometry.

### Documented contradictions (CP02 / Decision D)

| Layer | Statement | Conflict |
|-------|-----------|----------|
| Module docstring | “Long-Entry: Preis berührt untere Band” | Implies LONG |
| Class docstring Signals | `1 (long)` | Implies LONG |
| Method `generate_signals` Returns | `1=entry, -1=exit` | Event-only; not LONG |
| Decision D / adapter | `+1` is ENTRY only; never LONG authority | Fail-closed NONE |
| Registry capability | `supported_sides=("long","short")` default for fleet specs (CP03) | Capability ≠ emission; SHORT not in geometry |
| BaseStrategy vocab (CP01) | ±1 long/short position language | vs ENTRY_EXIT encoding |

**Active SSOT:** `BOLLINGER_DECISION=CONTRACT_REMAINS_AMBIGUOUS`, `bollinger_entry_side_decision=BLOCKED_AMBIGUITY`, `ENTRY_SIDE_CURRENT=NONE`, `BOLLINGER_SIDE_ACTIVATED=false`.

## Encoding / adapter path

| Field | Value |
|-------|-------|
| Encoding class | `ENTRY_EXIT_EVENT_V1` (owner set includes `bollinger_bands`) |
| Side resolver | `strategy_signal_suitability_agreement_adapter_v1.py::_resolve_entry_side_carrier_v1` |
| Bollinger result | Always `StrategyEntrySideCarrierV1.NONE` (only `trend_following` ratified) |
| Consumer | `mv2_research_wiring_v1.py::resolve_agreement_bound_directional_cycle_v1` → `None` when `entry_side=NONE` |
| Upstream explicit side? | **No** — producer emits only ±1/0 series; no `entry_side` field on strategy output |
| Unguided carrier only? | **Yes** — ENTRY/EXIT events without ratified side |

## Long / Short support

| Question | Answer (repo evidence) |
|----------|------------------------|
| LONG ENTRY geometry present? | Lower-band cross only — **long-leaning mean-reversion geometry** in comments/code path |
| SHORT ENTRY geometry present? | **No** |
| LONG/SHORT symmetric emission? | **No** — only one-sided entry geometry; EXIT never SHORT |
| Adapter Long/Short for Bollinger? | Both fail-closed to NONE (symmetric *block*, asymmetric *potential* LONG-only if later ratified like TF) |

## Quantitative baseline (frozen prior evidence)

Panel (`obl_b05_bollinger_long_semantic_decision_v1`): 185 ENTRY `+1`, all `entry_side=NONE`, all `BLOCKED_DIRECTIONAL_AGREEMENT`, 0 ENTER.

## Related producers (not Bollinger authority)

| Key | Relation |
|-----|----------|
| `mean_reversion` / `mean_reversion_channel` | Separate strategies; channel largely unwired |
| `trend_following` | Only ratified ENTRY_EXIT side owner (LONG on ENTRY) |
| `macd` | ENTRY_EXIT owner; side not activated |

## Semantics confirmation

| Question | Verdict |
|----------|---------|
| Mean-reversion vs breakout vs trend geometry | **MEAN_REVERSION confirmed** by productive geometry + registry description |
| Whether ENTRY authorizes LONG vs event-only | **UNRESOLVED** (`CONTRACT_REMAINS_AMBIGUOUS`) |
| Whether SHORT is part of Bollinger contract | **No productive SHORT**; docs claim long-leaning but method says entry |

→ `BOLLINGER_STRATEGY_CLASS=MEAN_REVERSION`  
→ `BOLLINGER_SEMANTICS_CONFIRMED=false` (authority/contract for `entry_side` not ratified)
