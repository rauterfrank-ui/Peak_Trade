# Peak_Trade Product Documentation

> **Zweck:** Kanonische, versionierte Produkt- und Implementierungsdokumentation.  
> **Runtime-Wirkung:** keine.  
> **Trading-/Risk-/Authority-/Economic-/Decision-Ownership:** keine.

---

## Market Dashboard

**Canonical Landscape V2 planning/execution runbook (read-only consumer; no runtime/trading authorization):**  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Previous product surface / legacy `market_surface`: fully removed
(`REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS`; not an architectural component;
no tombstone route/module/path exists). See
[`docs/webui/MARKET_DASHBOARD_REMOVED.md`](../webui/MARKET_DASHBOARD_REMOVED.md).

Historical Architecture Reset & Rebuild planning SSOT (non-Landscape-V2; not a second implementation authority):  
[`Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md`](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md)

Independent domain producers (trading, risk, execution, economic, diagnostics, market-data) remain domain-owned and are not a UI product. Phase 3 Landscape Shell requires a separate operator GO.
