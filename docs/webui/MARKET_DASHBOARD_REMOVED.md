# Market Dashboard — Legacy Product Removed / Landscape V2 Successor

The Peak Trade **legacy** Market Dashboard product was intentionally removed and completely deleted.

- Legacy packages, templates, Chart.js market shells, OHLCV/depth APIs, and reset-shell markers remain deleted.
- Legacy aliases (`&#47;market&#47;double-play`, `&#47;market&#47;futures`, `&#47;api&#47;market&#47;ohlcv`, `&#47;api&#47;market&#47;depth`) remain intentionally absent (normal not-found).
- Independent domain producers (trading, risk, execution, economic, diagnostics, market-data) remain domain-owned.

**Current authorized read-only surface (already on main):**  
`GET &#47;market` remains the **Market Dashboard Landscape V2** read-only consumer shell. Exact route/template/static/bindings stay owned by the canonical Landscape V2 master runbook; this tombstone does **not** redefine them.

- Pure read-only GET route; no write/action/order/runtime controls.
- Unbound or missing producers render as `NOT_BOUND` / `MISSING` / `STALE` / `INVALID`.
- Does **not** authorize runtime activation, orders, scheduler, shadow/paper/testnet, capital changes, promotion, or live trading.
- `OPERATOR_PRODUCT_GATE` remains `PENDING` until explicit operator ratification. Technical or Chrome evidence must **not** be inferred as Product PASS.

Canonical planning/execution authority:  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Do not resurrect deleted legacy Dashboard code from Git history without explicit operator authorization.
