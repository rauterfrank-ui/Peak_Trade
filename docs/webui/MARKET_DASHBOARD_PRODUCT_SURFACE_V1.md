# Market Dashboard Product Surface v1 (PR-D; active after merge)

Ownership:

- Page aggregate: `src&#47;webui&#47;market_dashboard_readmodels_v1&#47;page_builder.py`
- Presenter: `src&#47;webui&#47;market_dashboard_product_surface_v1&#47;presenter.py`
- Route composition: `src&#47;webui&#47;market_dashboard_product_surface_v1&#47;route_composition.py`
- Template: `templates&#47;peak_trade_dashboard&#47;market_dashboard_product_v1.html`

Authority / SSOT reference (do not duplicate):

- `docs&#47;product&#47;Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md`

## Path

```text
GET /market
  → optional env-gated OHLCV/ranking readmodels (source_loader)
  → PR-C adapters via page_builder
  → MarketDashboardPageSnapshotV1
  → presenter (display-only)
  → market_dashboard_product_v1.html
```

Active route owner: product surface only. The PR-A reset shell and legacy
`market_v0` composition are not the active `&#47;market` product route.
Standalone legacy shells `double_play_market_dashboard_v0.html` and
`futures_read_only_market_dashboard_v0.html` were removed in PR-E (routes remain
redirects to `&#47;market` anchors).

## Safety / Authority

Until a consolidated canonical producer exists, `adapt_safety_authority_snapshot_v1(None)`
yields `NOT_BOUND`. The UI must show **NOT BOUND** and must not claim execution safe,
allowed, blocked, risk passed, or kill-switch inactive. PR-E closeout does **not**
invent a consolidated Safety&#47;Authority producer.

## Optional env sources

- `PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED=1` + `PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT`
- `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1` + `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT`
- `PEAK_TRADE_MARKET_DASHBOARD_VENUE` (required to bind market instrument when OHLCV present)

Default productive route remains fail-closed with explicit SOURCE MISSING / NOT BOUND sections.

## Gates

- `TECHNICAL_GATE_PASS` may be set by automated checks.
- Operator `PRODUCT_GATE_PASS=true` applies only to the reviewed PR-D head that was
  squash-merged (Chrome product review). It does **not** generalize to later
  dashboard feature work; new features need a new bounded PR.
- Chrome&#47;Playwright remains the primary evidence path; Safari is not required for
  primary product approval.
- No trading authority and no order controls on `&#47;market`.

## PR-E closeout scope

PR-E finalizes static guards, deletes only proven-dead unrendered legacy shells,
updates docs&#47;evidence, and records Definition of Done residuals. It is not a
product redesign and must not reopen PR-D visual design.
