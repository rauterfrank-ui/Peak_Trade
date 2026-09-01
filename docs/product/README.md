# Peak_Trade Product Documentation

> **Zweck:** Kanonische, versionierte Produkt- und Implementierungsdokumentation.  
> **Runtime-Wirkung:** keine.  
> **Trading-/Risk-/Authority-/Economic-/Decision-Ownership:** keine.

---

## Market Dashboard

**Canonical Landscape V2 planning/execution runbook (read-only consumer; no runtime/trading authorization):**  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Previous product surface / legacy `market_surface` is historical evidence only
(`DOCUMENT_CLASS=HISTORICAL_EVIDENCE_ONLY`; not a current architectural
component; not a current tombstone or negative non-regression contract). See
[`docs/webui/MARKET_DASHBOARD_REMOVED.md`](../webui/MARKET_DASHBOARD_REMOVED.md).

Historical Architecture Reset & Rebuild planning SSOT (non-Landscape-V2; not a second implementation authority):  
[`Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md`](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md)

Independent domain producers (trading, risk, execution, economic, diagnostics, market-data) remain domain-owned and are not a UI product. Phase 3 Landscape Shell requires a separate operator GO.
