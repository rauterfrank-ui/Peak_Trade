# First Real Blocker

## Classification

```text
FIRST_REAL_BLOCKER = AGREEMENT_NOT_BOUND
```

Not chosen (reason):

| Candidate | Why rejected |
|-----------|--------------|
| `SIGNAL_ABSENT` | ENTRY signals present (panel 185 ENTRY `+1`) |
| `COMPOSITION_OBSERVE` | Downstream symptom of unresolved agreement |
| `DIRECTION_NOT_SELECTED` | Effect of agreement fail; stage SSOT is agreement carrier |
| `RUNTIME_BRIDGE_NOT_ACTIVATED` | Live/policy state; not offline economic funnel first fail |
| `CRS_NOT_BOUND` / `ORDER_INTENT_NOT_BOUND` / `QUANTITY_BLOCK` / `EXECUTION_ELIGIBILITY_BLOCK` | NOT_REACHED on this funnel |

## Owner

`src/backtest/strategy_signal_suitability_agreement_adapter_v1.py` (`_resolve_entry_side_carrier_v1`)  
→ consumed by `src/backtest/mv2_research_wiring_v1.py` (`resolve_agreement_bound_directional_cycle_v1`)

## Concrete condition

`ENTRY_EXIT_EVENT_V1` ENTRY with `entry_side == NONE` because producer is not the ratified `trend_following` entry-side owner (Bollinger remains ambiguous / non-ratified).

```python
# _resolve_entry_side_carrier_v1
if executed_strategy_id != _TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER:
    return StrategyEntrySideCarrierV1.NONE
```

```python
# resolve_agreement_bound_directional_cycle_v1 (ENTRY_EXIT ENTRY)
# LONG → +1, SHORT → -1, NONE → None (no sign invention from cycle_signal_value)
```

## Actual vs expected

| Field | Actual | Expected to clear this stage |
|-------|--------|------------------------------|
| `entry_side` | `NONE` (185/185 panel ENTRY bars in prior diagnostic) | `LONG` or `SHORT` explicit carrier |
| Agreement direction | `unresolved` / taxonomy `BLOCKED_DIRECTIONAL_AGREEMENT` | Resolved ±1 directional cycle |
| Agreement-bound price path | Flat `(mark, mark)` | Impulse path when direction resolved |
| Composition | `observe` / `selected_side=none` | Actionable selected side when upstream clears |

## Causal chain

1. **Upstream:** Strategy emits ENTRY `cycle_signal_value=+1`, but Bollinger producer-scoped carrier stays `NONE` (`BOLLINGER_DECISION=CONTRACT_REMAINS_AMBIGUOUS` / prior OBL-B05 evidence).
2. **This stage:** `resolve_agreement_bound_directional_cycle_v1` returns `None` → fail-closed flat path.
3. **Downstream:** DA not candidate → composition observe → CRS/OI/qty/eligibility **NOT_REACHED** → `TRADE_COUNT=0`.

## Long / Short symmetry

- **Bollinger:** Symmetric fail-closed — neither LONG nor SHORT ratified (`entry_side=NONE` for both).
- **Contrast (not competing authority):** Ratified `trend_following` may emit LONG only by producer contract; EXIT/`-1` never invents SHORT. That is intentional producer asymmetry, not Double-Play SideState competition.

## Evidence anchors

- `docs/product/evidence/read_only_canonical_chain_and_zero_trade_blocker_reaudit_v1_20260717T235727Z/decision.json`
- `docs/product/evidence/obl_b05_bollinger_long_semantic_decision_v1_20260717T231700Z/`
- `docs/product/evidence/obl_b05_bollinger_entry_side_doc_alignment_v1_20260717T234000Z/`
- Code at HEAD `43558204` confirms same carrier/resolution semantics unchanged by #5327/#5328 (test/assert/smoke only).
