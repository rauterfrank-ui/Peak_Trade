# Market Dashboard — Removed

The Peak Trade Market Dashboard product was intentionally and completely removed.

- GET /market is intentionally absent (normal application not-found behavior).
- No Market Dashboard UI, reset shell, placeholder, redirect, quarantine, or alternate route remains.
- Independent domain producers (trading, risk, execution, economic, diagnostics, market-data) remain domain-owned and are not a UI product.
- Do not resurrect or copy deleted Dashboard code from Git history without explicit operator authorization.

**Successor planning authority (Landscape V2; docs-only until separately authorized):**  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)  
This runbook does **not** by itself authorize UI/route reconstruction, runtime activation, orders, or live trading. Phase 3 Landscape Shell requires a separate operator GO.
