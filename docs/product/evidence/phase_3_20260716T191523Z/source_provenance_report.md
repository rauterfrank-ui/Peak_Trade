# Phase 3 Source Provenance Report

```text
SOURCE_PROVENANCE_VERIFIED=true
DASHBOARD_ROLE=CONSUMER_ONLY
DATA_PRODUCER_EFFECT=NONE
REQUEST_TIME_VENUE_NETWORK=false
CANDLE_CHART_REAL_DATA=true
VOLUME_REAL_DATA=true
SYNTHETIC_CANDLES=false
SPOT_FALLBACK=false
BITCOIN_DIRECTION=false
```

## Provenance chain

1. Futures OHLCV read-model bundle → `src/webui/market_futures_ohlcv_runtime_v0.py`
2. Series resolve for selected symbol/timeframe → `resolve_futures_ohlcv_series_for_symbol`
3. Market payload bars → `src/webui/market_surface.py`
4. Presentation VM → `src/webui/market_visual_operator_surface_v1/chart_display_v1.py` (`chart_phase_3`)
5. SSR SVG render → `templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html`

## Evidence fixtures (local verification)

- Ranking: `tests/fixtures/market_ranking_funnel_readmodel_v0/complete_minimal`
- OHLCV: `tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal` (`timeframe=1d`)
- F5 dashboard: `tests/fixtures/futures_read_only_market_dashboard_v0/complete_minimal`

## HTML snapshot

- `docs/product/evidence/phase_3_20260716T191523Z/proofs/html_contract_snapshot.json`

Selected symbol observed: `ETHUSDT` (fixture-bound).
