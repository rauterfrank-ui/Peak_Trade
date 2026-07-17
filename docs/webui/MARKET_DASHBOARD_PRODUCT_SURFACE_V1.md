# Market Dashboard Product Surface v1 (PR-D)

Ownership:

- Page aggregate: `src/webui/market_dashboard_readmodels_v1/page_builder.py`
- Presenter: `src/webui/market_dashboard_product_surface_v1/presenter.py`
- Route composition: `src/webui/market_dashboard_product_surface_v1/route_composition.py`
- Template: `templates/peak_trade_dashboard/market_dashboard_product_v1.html`

## Path

```text
GET /market
  → optional env-gated OHLCV/ranking readmodels (source_loader)
  → PR-C adapters via page_builder
  → MarketDashboardPageSnapshotV1
  → presenter (display-only)
  → market_dashboard_product_v1.html
```

## Safety / Authority

Until a consolidated canonical producer exists, `adapt_safety_authority_snapshot_v1(None)`
yields `NOT_BOUND`. The UI must show **NOT BOUND** and must not claim execution safe,
allowed, blocked, risk passed, or kill-switch inactive.

## Optional env sources

- `PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED=1` + `PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT`
- `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1` + `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT`
- `PEAK_TRADE_MARKET_DASHBOARD_VENUE` (required to bind market instrument when OHLCV present)

Default productive route remains fail-closed with explicit SOURCE MISSING / NOT BOUND sections.

## Gates

- `TECHNICAL_GATE_PASS` may be set by automated checks.
- `PRODUCT_GATE_PASS=false` until operator Chrome review.
