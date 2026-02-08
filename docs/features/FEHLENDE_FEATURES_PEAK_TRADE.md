# Peak Trade – Fehlende / geplante Features (Übersicht)

**Stand:** 2026-02-03  
**Zweck:** Vollständige Liste der Features, die in der Architektur/Vision genannt sind oder in Roadmaps/TODOs/Limitations dokumentiert wurden, aber **noch nicht implementiert** sind oder bewusst aus v1.0 ausgenommen wurden.

---

## 1. Kurzfassung

- **Implementiert (v1.0):** Data-Layer, Strategy-Library, Backtest, Research-Pipeline, Regime-Detection, Portfolio-Presets, Live-Gates, Shadow/Testnet, Risk-Limits, Web-Dashboard v0 (read-only), CI/CD, umfangreiche Doku.
- **Fehlend / geplant:** Siehe Abschnitte 2–5 unten.

---

## 2. Architektur-Vision vs. Implementierung (trading_bot_notes / Feature-Engine)

Laut ``src&#47;docs&#47;trading_bot_notes.md`` ist die Zielarchitektur:

```text
Datenquellen → Research & Feature-Engine → Strategie / Signale → Risk Layer → Broker/Exchange
```

**Research & Feature-Engine – aktuell fehlend oder nur teilweise da:**

| Feature (Vision) | Status | Anmerkung |
|------------------|--------|-----------|
| **Feature-Engine als zentrale Schicht** | ❌ Fehlt | ``src&#47;features&#47;`` ist nur Placeholder („wird später mit ECM-Features gefüllt“). Kein dediziertes Modul „Research & Feature-Engine“. |
| **Indikatoren (TA)** | ✅ Teilweise | In Strategien/Regime verteilt (MA, RSI, ATR, Vol-Score etc.), nicht als einheitliche Feature-Pipeline. |
| **Regime-Labels** | ✅ Vorhanden | ``src&#47;regime&#47;``, ``src&#47;core&#47;regime.py``, ``src&#47;analytics&#47;regimes.py``. |
| **Volatilitäts-Cluster** | ✅ Teilweise | Vol-Regime/Labels vorhanden; „Cluster“-Pipeline nicht als eigenes Feature-Modul. |
| **ECM-Fenster / ECM-Features** | ❌ Fehlt | In ``src&#47;features&#47;__init__.py`` als „später“ genannt, nicht implementiert. |
| **Sentiment (News/Makro/Krypto-Onchain)** | ❌ Fehlt | In trading_bot_notes als „optional, später“ genannt. |
| **Orderbuch-/Tickdaten** | ❌ Fehlt | In trading_bot_notes als „später“ genannt. |

---

## 3. Known Limitations (PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)

Bewusst **nicht** in v1.0 enthalten:

| Bereich | Fehlendes Feature |
|---------|-------------------|
| **Live/Execution** | Echte Live-Order-Ausführung (blockiert durch SafetyGuard / LiveNotImplementedError) |
| **Live/Execution** | Testnet ohne Dry-Run (echte Testnet-Orders) |
| **Exchange** | Multi-Exchange (nur Kraken; Binance, Coinbase etc. fehlen) |
| **Web-Dashboard** | Authentifizierung, Access-Control, Benutzerverwaltung |
| **Web-Dashboard** | POST/PUT/DELETE (Order-Erzeugung, Start/Stop aus Web-UI) |
| **Web-Dashboard** | SSE/WebSocket (nur Polling) |
| **Daten** | Real-Time-WebSocket-Streams (nur REST/Polling) |
| **Daten** | Multi-Exchange-Datenquellen / aggregierte Feeds |
| **Strategien** | ML-basierte Strategien, komplexe Multi-Factor-Modelle |
| **Daten/Assets** | Corporate Actions (Splits, Dividenden), Futures/Options (Spot-Fokus) |
| **Risk** | Automatische Position-Liquidation bei Limit-Verletzung |
| **Testing** | 100 % Test-Coverage |
| **Doku** | Automatisch generierte API-Doku (OpenAPI/Swagger) |
| **Infra** | Horizontale Skalierung / Multi-Instance |

---

## 4. Roadmap „bis Finish“ (INSTALLATION_UND_ROADMAP_BIS_FINISH)

Geplante Phasen mit **noch nicht umgesetzten** Features:

| Phase | Thema | Fehlende Features (Auszug) |
|-------|--------|----------------------------|
| **11** | Advanced Strategy Research | Genetic Algorithm, Bayesian Optimization, Adaptive Parameter-Tuning, Multi-Objective, Strategy-Ensemble, Auto-ML Strategy-Selection |
| **12** | Real-Time Data & Streaming | WebSocket-Integration, Real-Time-Signale, Streaming-Backtest-Engine, Latency-Monitoring, Order-Book-Analytics, Tick-Level-Backtests |
| **13** | Production Live-Trading | Live-Orders via CCXT, Multi-Exchange, Order-Routing/Smart-Order-Routing, Fill-Tracking, Live-PnL, Emergency-Stop (Governance-Review) |
| **14** | Advanced Analytics & ML | LSTM/Transformer Predictions, Reinforcement Learning, **Sentiment-Analysis**, **Feature-Engineering-Pipeline**, Model-Training, Online-Learning |
| **15** | Cloud & Scalability | Kubernetes, Docker-Compose, AWS/GCP/Azure, Auto-Scaling, Load-Balancing, Multi-Region |
| **16** | Advanced Risk & Portfolio | VaR/CVaR, Stress-Testing, Portfolio-Optimization (Markowitz, Black-Litterman), Risk-Parity, Factor-Models, Attribution |
| **17** | Community & Open-Source | Open-Source-Release, Contributing-Guide, Plugin-System für Community-Strategien |

---

## 5. Research-/Strategy-TODO & Tech-Debt

### 5.1 Peak_Trade Research/Strategy ToDo (2025-12-07)

- RSI-Varianten-Sweep (Stochastic RSI, Multi-Timeframe-RSI)
- Sortino-Ratio in Sweep-Ergebnissen
- Standard-Heatmap-Template (2 Parameter × 2 Metriken)
- Unified Pipeline-CLI (`run_sweep_pipeline.py` mit --run/--report/--promote)
- Drawdown-Heatmap (Parameter vs. Max-Drawdown)
- Vol-Regime-Filter als Wrapper für alle Strategien
- Monte-Carlo-Robustness (Bootstrapped Sharpe-Konfidenzintervalle)
- Korrelations-Matrix-Plot (Parameter–Metrik)
- Rolling-Window-Stabilität (Top-Parameter über 6-Monats-Fenster)
- Sweep-Comparison-Tool
- Zusätzliche Metriken: Calmar, Ulcer-Index, Recovery-Factor
- Regime-adaptive Strategien (Parameter-Switching nach Regime)
- Auto-Portfolio-Builder (nicht-korrelierte Top-Strategien)
- Nightly-Sweep-Automation (Cron/Scheduler + Alerts)
- Interaktive Dashboards (Plotly/Web-UI)
- Feature-Importance-Analyse
- Risk-Parity-Integration im Portfolio

### 5.2 Stubs / Phase-begrenzt (ops-Docs)

- Kill-Switch im RiskHook: Phase 0 „not implemented“
- PagerDuty-Eskalation: `pagerduty_stub`, Phase 85
- Adapter-Protocol: WP0C Placeholder
- Einige Research-Strategien: TODO/NotImplementedError (z. B. Ehlers, López de Prado, Bouchaud, Gatheral)

### 5.3 Tech-Debt Backlog (TECH_DEBT_BACKLOG.md)

- Legacy-Funktionen in `macd.py` / `bollinger.py` entfernen (nach Umstellung auf OOP)
- Ggf. weitere Dummy-Adapter durch echte Kraken/Exchange-Integration ersetzen (je nach Script)

### 5.4 Futures/Continuous (docs/markets)

- **RATIO_ADJUST** für Continuous Contracts: reserviert, nicht implementiert (nur NONE, BACK_ADJUST).
- Runbook: Risk-Gates, Observability, Paper-Broker-Adapter für Futures als offene Punkte genannt.

---

## 6. Feature-Engine & López de Prado (konkret im Code)

- **``src&#47;features&#47;``:** Nur Placeholder; keine ECM- oder allgemeine Feature-Pipeline.
- **Meta-Labeling-Strategie:**  
  - `compute_triple_barrier_labels`: TODO, Placeholder (gibt Nullen zurück).  
  - `_extract_features`: TODO (Fractional Differentiation, Volatility-adjusted Returns, Regime-Indikatoren); gibt leeres DataFrame zurück.

---

## 7. Einordnung

| Kategorie | Bedeutung |
|-----------|-----------|
| **Architektur-Vision** | Feature-Engine, Sentiment, Orderbuch/Tick, ECM – in Vision/Docs genannt, nicht als durchgängige Schicht umgesetzt. |
| **v1.0 bewusst ausgenommen** | Live-Execution, Multi-Exchange, Web-Auth, WebSocket, ML-Strategien, Auto-Liquidation, 100 % Coverage, API-Doku, Skalierung. |
| **Roadmap 2026** | Phasen 11–17 (Optimization, Streaming, Live, ML, Cloud, Risk-Parity, Community). |
| **Research-Track** | Sweeps, Metriken, Heatmaps, Vol-Regime-Wrapper, Regime-adaptive Strategien, Auto-Portfolio, Nightly-Sweeps, Feature-Importance. |
| **Stubs/Placeholder** | Kill-Switch RiskHook, PagerDuty, WP0C-Adapter, einige R&D-Strategien, ``src&#47;features``, Meta-Labeling Feature-Engineering. |

---

**Referenzen:**

- ``docs&#47;PEAK_TRADE_V1_RELEASE_NOTES.md`` – Kern-Features v1.0  
- ``docs&#47;PEAK_TRADE_V1_KNOWN_LIMITATIONS.md`` – bewusst nicht implementiert  
- `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md` – Roadmap Teil 4  
- ``src&#47;docs&#47;trading_bot_notes.md`` – Architektur & Feature-Engine-Vision  
- ``docs&#47;Peak_Trade_Research_Strategy_TODO_2025-12-07.md`` – Research-TODO  
- ``docs&#47;TECH_DEBT_BACKLOG.md`` – Tech-Debt  
- ``docs&#47;ops&#47;UEBERSICHT_DATEN_GATES_DOCKER_GITHUB.md`` – Stubs/Optional
