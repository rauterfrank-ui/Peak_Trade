# Market Dashboard Product Recovery v1 — Discovery

UTC: 2026-07-17T04:55:39Z  
Mode: Forensic Phase 0 (read-only) then bounded implementation  
SSOT: `docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md` PART I

## Verdict against prior completeness claim

`PRODUCT_COMPLETENESS=COMPLETE` is **refuted** by operator viewing evidence:
empty dominant chart, repeated unavailable typography, misleading ACTIVE vs Blocked,
locale mix, and recovery env spam as primary content.

## Route owners

| Layer | Owner |
|---|---|
| Route | `src/webui/market_surface.py` `GET /market` |
| Template | `templates/peak_trade_dashboard/market_v0.html` |
| Chart | `partials/market_primary_close_chart_v1.html` |
| CSS | `static/css/peak_trade_dashboard_{design_tokens,layout,utilities}_v1.css` |

## Why review server shows empty

`scripts/webui/review_server.sh` exports only `LIVE_AUTHORIZED=false` / `ORDERS_ALLOWED=false`.
It does **not** bind `PEAK_TRADE_MARKET_*` bundle roots. Canonical `/market` is futures-first fail-closed.

Real fixtures exist:
- `tests/fixtures/market_ranking_funnel_readmodel_v0/complete_minimal/ranking_funnel.json`
- `tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal/futures_ohlcv.json`

Optional archive path via `scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh` (port 8765).

## Reference screenshots

- `artifacts/market_dashboard_operator_viewing_readonly_20260717T043328Z/screenshots/`
- `artifacts/market_dashboard_product_review_v13_readonly_20260717T042547Z/screenshots/`
