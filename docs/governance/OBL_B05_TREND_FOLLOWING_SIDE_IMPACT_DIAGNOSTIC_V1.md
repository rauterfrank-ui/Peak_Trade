# OBL_B05 Trend-Following Side-Impact Diagnostic v1

---
docs_token: DOCS_TOKEN_OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1
STATUS: TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_COMPLETE
scope: read-only A/B impact diagnostic after PR #5318 ratification
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_COMPLETE: true
PRODUCTIVE_SEMANTICS_CHANGED: false
ADDITIONAL_PRODUCER_ACTIVATED: false
BOLLINGER_SIDE_ACTIVATED: false
MACD_SIDE_ACTIVATED: false
---

> Read-only Vorher→Nachher-Diagnose der ratifizierten `trend_following`
> `entry_side`-Emission. Keine produktive Semantikänderung, keine weitere
> Producer-Aktivierung, keine Runtime&#47;Orders&#47;Live-Autorisierung.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1` |
| `BASE_SHA` | `190d6a9f6d29f807318904012dc0cc638debc45a` |
| `IMPACT_CLASSIFICATION` | `DIRECTIONAL_AGREEMENT_UNBLOCKED` + `SHIFTED_TO_COMPOSITION` |
| `CONTROL_DOMINANT_FIRST_FAILED_STAGE` | `directional_agreement` |
| `RATIFIED_DOMINANT_FIRST_FAILED_STAGE` | `composition` |
| `NEXT_DOMINANT_BLOCKER` | composition &#47; `CompositionStatus.OBSERVE` |
| `ENTER_OUTCOME_OBSERVED` | `false` |
| `PRODUCTIVE_SEMANTICS_CHANGED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `SSOT_JSON` | `config&#47;governance&#47;obl_b05_trend_following_side_impact_diagnostic_v1.json` |

## B. Method (A/B, identical inputs)

| Mode | Injection |
|---|---|
| Control A | diagnostic monkeypatch `_resolve_entry_side_carrier_v1 → NONE` |
| Ratified B | productive adapter emission (`entry_side=LONG` on TF ENTRY) |

Inputs reused from durable full-canonical panel scratch + MV2 runtime config,
with `economic_evaluation_v1.strategy_id=trend_following` overlay only inside
the diagnostic runner (no productive config mutation).

Runner: `scripts&#47;ops&#47;run_obl_b05_trend_following_side_impact_diagnostic_v1.py`

## C. Counts (summary)

### Eval (`okx:linear_perpetual:1INCH:USDT:USDT:perp`)

| Metric | Control | Ratified |
|---|---:|---:|
| ENTRY bars | 40 | 40 |
| entry_side NONE | 40 | 0 |
| entry_side LONG | 0 | 40 |
| first_failed DA | 40 | 0 |
| first_failed composition | 0 | 40 |
| ENTER&#47;HOLD&#47;EXIT | 0 | 0 |

### Panel (118 instruments)

| Metric | Control | Ratified |
|---|---:|---:|
| total bars | 348454 | 348454 |
| ENTRY bars | 5121 | 5121 |
| changed by TF side emission | 5054 | 5054 |
| warmup unchanged | 67 | 67 |
| entry_side LONG | 0 | 5054 |
| dominant stage | directional_agreement | composition |
| ENTER | 0 | 0 |

### Non-trend_following (Bollinger eval)

`force_none` == productive path; `entry_side=NONE`; DA remains blocked.
`ADDITIONAL_PRODUCER_ACTIVATED=false`, `BOLLINGER_SIDE_ACTIVATED=false`.

## D. Classification

1. `DIRECTIONAL_AGREEMENT_UNBLOCKED` — explicit LONG carrier enables DA candidate path.
2. `SHIFTED_TO_COMPOSITION` — next fail-closed stage is composition (`observe`).
3. Not observed: `ENTER_OUTCOME_OBSERVED`, later-stage ENTER&#47;HOLD&#47;EXIT success.

## E. Next dominant blocker (no repair in this slice)

- Stage: `composition`
- Contract: `CompositionStatus.OBSERVE` (double-play composition matrix owner)
- Panel count: 5054 ENTRY bars still blocked at composition after DA unblock

## F. Owners / navigation

| Surface | Owner |
|---|---|
| SSOT JSON | `config&#47;governance&#47;obl_b05_trend_following_side_impact_diagnostic_v1.json` |
| Governance narrative | this document |
| Diagnostic runner | `scripts&#47;ops&#47;run_obl_b05_trend_following_side_impact_diagnostic_v1.py` |
| Tests | `tests&#47;backtest&#47;test_obl_b05_trend_following_side_impact_diagnostic_v1.py` |
| Parent ratification | `docs&#47;governance&#47;OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1.md` |
| Evidence pointer | `docs&#47;product&#47;evidence&#47;obl_b05_trend_following_side_impact_diagnostic_v1_20260717T225700Z&#47;` |
