# OBL_B05 Trend-Following Entry-Side Ratification v1 — Audit

## Contract proof

| Raw | Meaning | entry_side |
|---|---|---|
| +1 | LONG ENTRY (ADX strong, +DI &gt; -DI) | LONG |
| -1 | EXIT (not SHORT) | NONE |
| 0 | FLAT &#47; no change | NONE |

`short_entry_condition_present=false` — no productive SHORT-ENTRY.

## Adapter emission probe (synthetic ENTRY&#47;FLAT&#47;EXIT)

| producer | entry_side counts | directional |
|---|---|---|
| trend_following | LONG:1 NONE:2 | +1 on ENTRY else None |
| bollinger_bands | NONE:3 | None |
| macd | NONE:3 | None |
| all other ENTRY_EXIT | NONE:3 | None |

## Bollinger panel&#47;eval diagnostic (unchanged)

Eval instrument before == after (adapter swap compare on same HEAD tree):

- entry_bar_count: 1 → 1
- entry_side (Bollinger): NONE → NONE
- first_failed_stage: directional_agreement → directional_agreement
- taxonomy: BLOCKED_DIRECTIONAL_AGREEMENT → BLOCKED_DIRECTIONAL_AGREEMENT
- suitability: bull=pass;bear=pass (unchanged)
- composition: observe (unchanged)
- final_decision: observe (unchanged)
- ENTER&#47;HOLD&#47;EXIT: 0 → 0
- price_path: flat mark→mark (unchanged)

Panel baseline from prior durable diagnostic remains 185 ENTRY bars on Bollinger;
this slice does not activate Bollinger side emission.
