# Knowledge Sources Registry

## Übersicht

Dieses Dokument registriert alle externen Wissensquellen, die in die Peak_Trade Knowledge Databases integriert sind.

**Letzte Aktualisierung:** Dezember 2024

---

## Aktive Datenquellen

### 1. Interne Backtest-Reports

**Status:** ✅ Aktiv  
**Kategorie:** Intern (High Trust)  
**Beschreibung:** Eigene Backtest-Ergebnisse aus der Research-Pipeline  

**Details:**
- **Quelle:** `results&#47;` Directory
- **Format:** Text/JSON Reports
- **Update-Frequenz:** Nach jedem Research-Run
- **Integration:** Vector DB (ChromaDB)
- **Metadaten-Tags:** `internal_backtest`, `strategy`, `performance`
- **Ingestion-Script:** `scripts&#47;ingest_backtest_reports.py` (illustrative) <!-- pt:ref-target-ignore -->

**Verantwortlich:** Data Owner  
**Review-Status:** Approved  
**Nächste Review:** -

---

### 2. Portfolio Performance Histories

**Status:** ✅ Aktiv  
**Kategorie:** Intern (High Trust)  
**Beschreibung:** Historische Portfolio-Performance-Daten

**Details:**
- **Quelle:** `src/portfolio/` Module
- **Format:** Pandas DataFrame / Parquet
- **Update-Frequenz:** Täglich (für Live/Testnet)
- **Integration:** Time-Series DB (Parquet)
- **Metadaten-Tags:** `portfolio`, `performance`, `equity_curve`
- **Ingestion-Script:** Automatisch via `src.knowledge.timeseries_db`

**Verantwortlich:** Data Owner  
**Review-Status:** Approved  
**Nächste Review:** -

---

### 3. Strategy Metadata & Descriptions

**Status:** ✅ Aktiv  
**Kategorie:** Intern (High Trust)  
**Beschreibung:** Strategie-Definitionen, Parameter, Beschreibungen

**Details:**
- **Quelle:** `src/strategies/` Module, Docstrings
- **Format:** Python Docstrings / Markdown
- **Update-Frequenz:** Bei Code-Änderungen
- **Integration:** Vector DB (ChromaDB)
- **Metadaten-Tags:** `strategy`, `definition`, `parameters`
- **Ingestion-Script:** `scripts&#47;ingest_strategy_docs.py` (illustrative) <!-- pt:ref-target-ignore -->

**Verantwortlich:** Developer  
**Review-Status:** Approved  
**Nächste Review:** Q1 2025

---

## Geplante Datenquellen

### 1. Kraken OHLCV Market Data

**Status:** 📋 Geplant  
**Kategorie:** Marktdaten (Medium-High Trust)  
**Beschreibung:** Exchange-OHLCV-Daten von Kraken

**Details:**
- **Quelle:** Kraken API / Cache (`data&#47;cache`)
- **Format:** Parquet
- **Update-Frequenz:** Stündlich
- **Integration:** Time-Series DB (Parquet)
- **Metadaten-Tags:** `market_data`, `ohlcv`, `kraken`
- **Ingestion-Script:** Zu entwickeln

**Verantwortlich:** Developer  
**Review-Status:** Planning  
**Nächste Review:** Q1 2025

---

### 2. On-Chain Metrics (Glassnode/CoinMetrics)

**Status:** 📋 Geplant  
**Kategorie:** Marktdaten (Medium-High Trust)  
**Beschreibung:** On-Chain-Metriken für BTC/ETH

**Details:**
- **Quelle:** Glassnode API (kostenpflichtig)
- **Format:** JSON → Parquet
- **Update-Frequenz:** Täglich
- **Integration:** Time-Series DB (InfluxDB oder Parquet)
- **Metadaten-Tags:** `on_chain`, `glassnode`, `btc`, `eth`
- **Ingestion-Script:** Zu entwickeln

**Kosten:** ~$500/Monat (Studio Plan)  
**Verantwortlich:** Data Owner  
**Review-Status:** Cost-Benefit Analysis pending  
**Nächste Review:** Q1 2025

---

### 3. Trading Research Papers (arXiv, SSRN)

**Status:** 📋 Geplant  
**Kategorie:** Research (Medium Trust)  
**Beschreibung:** Academic Papers zu Trading, ML, Quantitative Finance

**Details:**
- **Quelle:** arXiv.org, SSRN
- **Format:** PDF → Text (OCR)
- **Update-Frequenz:** Monatlich (manuelle Selektion)
- **Integration:** Vector DB (ChromaDB)
- **Metadaten-Tags:** `research`, `paper`, `arxiv`, `ssrn`
- **Ingestion-Script:** Manuell + `scripts&#47;ingest_research_paper.py` (illustrative) <!-- pt:ref-target-ignore -->

**Lizenz:** CC-BY-4.0 (arXiv), SSRN (Check per Paper)  
**Verantwortlich:** Researcher  
**Review-Status:** In Evaluation  
**Nächste Review:** Q1 2025

---

## Deaktivierte Datenquellen

### 1. Twitter Sentiment (Deprecated)

**Status:** ❌ Deaktiviert  
**Kategorie:** Community (Low Trust)  
**Beschreibung:** Twitter/X Sentiment-Analyse

**Grund für Deaktivierung:**
- Zu viel Noise, geringe Qualität
- Twitter API Kosten zu hoch
- Keine konsistente Korrelation mit Trading-Signalen

**Deaktiviert am:** Dezember 2024  
**Archiviert:** Keine Daten archiviert

---

## Metadaten-Schema (Standard)

Alle Datenquellen müssen folgende Metadaten enthalten:

```python
{
    "source": str,           # Name der Quelle
    "timestamp": str,        # ISO 8601 Timestamp
    "category": str,         # "research" | "market_data" | "strategy" | "community"
    "version": str,          # Versionsnummer
    "author": str,           # Autor/System
    "tags": List[str],       # Schlagworte
}
```

---

## API-Keys & Credentials (Environment Variables)

**WICHTIG:** Niemals API-Keys in diesem Dokument oder im Code committen!

Benötigte Environment Variables:

```bash
# Vector DB (optional für Cloud-Provider)
# PINECONE_API_KEY=your_key_here
# QDRANT_API_KEY=your_key_here

# Time-Series DB (optional für InfluxDB)
# INFLUXDB_TOKEN=your_token_here
# INFLUXDB_URL=http://localhost:8086
# INFLUXDB_ORG=peak_trade
# INFLUXDB_BUCKET=market_data

# External APIs (planned)
# GLASSNODE_API_KEY=your_key_here
# COINMETRICS_API_KEY=your_key_here
```

**Key-Management:** Siehe `src.knowledge.api_manager.APIManager`

---

## Monitoring & Alerts

### Key-Performance-Indicators (KPIs)

- **Ingestion Success Rate:** > 99%
- **Query Response Time:** < 500ms (p95)
- **Data Freshness:** Max 24h alt
- **API Rate Limit Usage:** < 80%

### Alerts

- ⚠️  Ingestion-Fehler > 3 in 1h
- ⚠️  Query-Latenz > 1s (p95)
- ⚠️  API Rate Limit > 90%
- ⚠️  API-Key-Rotation überfällig (> 90 Tage)

---

## Change Log

| Datum | Änderung | Autor |
|-------|----------|-------|
| 2024-12-20 | Initial Registry erstellt | System |
| - | - | - |

---

## Nächste Schritte

- [ ] Kraken OHLCV Ingestion implementieren
- [ ] Glassnode API evaluieren (Kosten/Nutzen)
- [ ] Research Paper Ingestion Workflow testen
- [ ] Monitoring Dashboard aufsetzen
- [ ] Quarterly Review Q1 2025 planen

---

**Maintained by:** Data Owner  
**Version:** 1.0  
**Nächste Review:** Q1 2025
