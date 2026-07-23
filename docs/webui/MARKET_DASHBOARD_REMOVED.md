# Market Dashboard — Legacy Product Removed / Landscape V2 Successor

The Peak Trade **legacy** Market Dashboard product was intentionally removed and completely deleted.

- Legacy packages, templates, Chart.js market shells, OHLCV/depth APIs, and reset-shell markers remain deleted.
- Legacy aliases (`/market/double-play`, `/market/futures`, `/api/market/ohlcv`, `/api/market/depth`) remain absent (normal not-found).
- Independent domain producers (trading, risk, execution, economic, diagnostics, market-data) remain domain-owned.

**Successor surface (authorized Phase 3 Landscape Shell only):**  
`GET /market` is restored as the **Market Dashboard Landscape V2** read-only consumer shell.

- Pure read-only GET route; no write/action/order/runtime controls.
- Consumes Phase 2 Landscape projection contracts; unbound producers render as `NOT_BOUND`.
- Does **not** authorize Phase 4 producer binding, runtime activation, orders, scheduler, shadow/paper/testnet, capital changes, or live trading.
- Operator product approval for the skeleton remains `PENDING` until screenshots are reviewed.

Canonical planning/execution authority:  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Do not resurrect deleted legacy Dashboard code from Git history without explicit operator authorization.
