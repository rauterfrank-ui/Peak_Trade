# OBL_B05 Trend-Following Side-Impact Diagnostic v1 — Audit

## Method

- Identical panel inputs (118 members, full-canonical scratch bars + MV2 runtime cfg overlay strategy=`trend_following`).
- Control A: diagnostic monkeypatch `_resolve_entry_side_carrier_v1 -> NONE`.
- Ratified B: productive adapter emission.
- No productive `src/` mutation in this slice.

## Eval (1INCH)

| | Control | Ratified |
|---|---|---|
| ENTRY bars | 40 | 40 |
| entry_side | NONE×40 | LONG×40 |
| first_failed_stage | directional_agreement×40 | composition×40 |
| taxonomy | BLOCKED_DA×40 | BLOCKED_COMPOSITION×40 |
| ENTER/HOLD/EXIT | 0 | 0 |

## Panel (118)

| | Control | Ratified |
|---|---|---|
| ENTRY bars | 5121 | 5121 |
| changed by side emission | 5054 | 5054 |
| warmup unchanged | 67 | 67 |
| entry_side | NONE×5121 | LONG×5054 + NONE×67 |
| dominant stage | directional_agreement | composition |
| ENTER | 0 | 0 |

## Non-TF control

Bollinger eval force_none == productive path (entry_side NONE; DA block). Unchanged.

## Classification

- `DIRECTIONAL_AGREEMENT_UNBLOCKED`
- `SHIFTED_TO_COMPOSITION`
- Next dominant blocker: composition observe
