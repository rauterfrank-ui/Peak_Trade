# OBL_B05 Trend-Following Entry-Side Ratification v1

---
docs_token: DOCS_TOKEN_OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1
STATUS: TREND_FOLLOWING_SIDE_RATIFIED
scope: producer-scoped entry_side emission for trend_following only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
TREND_FOLLOWING_SIDE_RATIFIED: true
PRODUCTIVE_TREND_FOLLOWING_SIDE_EMISSION_CHANGED: true
OTHER_PRODUCER_SIDE_EMISSION_CHANGED: false
BOLLINGER_SIDE_ACTIVATED: false
MACD_SIDE_ACTIVATED: false
---

> Ratifies the **existing** productive `trend_following` LONG-entry contract onto
> the optional `entry_side` carrier. Does **not** invent SHORT entries, does
> **not** activate Bollinger&#47;MACD&#47;other producers, and does **not** authorize
> runtime, orders, capital, or live.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1` |
| `BASE_SHA` | `589099fed2445920531066cd89549e1c4391301e` |
| `TREND_FOLLOWING_SIDE_RATIFIED` | `true` |
| `PRODUCTIVE_TREND_FOLLOWING_SIDE_EMISSION_CHANGED` | `true` |
| `OTHER_PRODUCER_SIDE_EMISSION_CHANGED` | `false` |
| `BOLLINGER_SIDE_ACTIVATED` | `false` |
| `MACD_SIDE_ACTIVATED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `SSOT_JSON` | `config&#47;governance&#47;obl_b05_trend_following_entry_side_ratification_v1.json` |

## B. Productive contract proof

Owner: `src&#47;strategies&#47;trend_following.py`

| Raw output | Productive meaning | `entry_side` |
|---|---|---|
| `+1` | LONG entry (ADX &gt; threshold and +DI &gt; -DI; optional MA filter) | `LONG` |
| `-1` | EXIT (ADX &lt; exit_threshold or -DI &gt; +DI) | `NONE` |
| `0` | no change &#47; flat | `NONE` |

- `short_entry_condition_present=false` — no productive SHORT-ENTRY path.
- EXIT&#47;downtrend must **not** be read as SHORT.
- Parent audit class was `RATIFIABLE_PRODUCER_SEMANTICS` with candidate LONG.

## C. Emission owner (reuse)

`src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py`
→ `_resolve_entry_side_carrier_v1`

Fail-closed mapping:

1. Only `executed_strategy_id == trend_following`
2. Only `ENTRY_EXIT_EVENT_V1` + `event_kind == ENTRY` + `cycle_signal_value == 1` → `LONG`
3. All other cases (EXIT&#47;FLAT&#47;other producers) → `NONE`
4. No heuristic name&#47;sign&#47;class derivation for Bollinger, MACD, or others

## D. Non-goals

- No strategy parameter or signal-formula change
- No composition &#47; risk &#47; sizing &#47; execution policy change
- No runtime &#47; testnet &#47; scheduler &#47; capital &#47; live activation
- No Bollinger or MACD side activation

## E. Owners

| Surface | Owner |
|---|---|
| Ratification SSOT JSON | `config&#47;governance&#47;obl_b05_trend_following_entry_side_ratification_v1.json` |
| Governance narrative | this document |
| Side emission | adapter `_resolve_entry_side_carrier_v1` |
| Static &#47; focused tests | `tests&#47;backtest&#47;test_trend_following_entry_side_ratification_v1.py` |
| Parent authority decision | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md` |
| Parent carrier contract | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1.md` |
| Follow-on impact diagnostic | `docs&#47;governance&#47;OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1.md` |
