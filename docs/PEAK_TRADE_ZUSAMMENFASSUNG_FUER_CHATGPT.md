# Peak Trade – Projektzusammenfassung für ChatGPT

Diese Zusammenfassung beschreibt das Projekt **Peak Trade** knapp und strukturiert, damit ChatGPT (oder andere KI-Assistenten) den Kontext verstehen und gezielt helfen können.

---

## Was ist Peak Trade?

**Peak Trade** ist ein **modulares, research-getriebenes Trading-Framework** mit konsequentem **Safety-First-Ansatz**. Es dient der Entwicklung, dem Backtest und dem kontrollierten Live-Betrieb von **Krypto-Trading-Strategien** (z. B. Kraken/BTC-USDT). Die Architektur trennt klar zwischen **Data**, **Strategy**, **Portfolio**, **Execution** und **Reporting**; Research-Experimente, Shadow-Runs und Testnet-Betrieb sind strikt voneinander getrennt.

- **Technologie:** Python (≥3.9), TOML-Konfiguration, optional FastAPI/Web-UI, MLflow, OpenTelemetry
- **Umfang:** ca. 650.000 Zeilen (Code + Doku + Reports), ~800 Python-Dateien, 35+ Module, hohe Test-Coverage

---

## Ziel

- **Hauptziel:** Ein **produktionsnahes Framework**, mit dem sich Krypto-Strategien fundiert erforschen, robust backtesten und unter klaren Sicherheitsvorgaben im Live-/Testnet-Betrieb ausführen lassen – „dem Future-Ich vertrauen kann“.
- **Konkret:**
  - Strategien und Portfolios **research-getrieben** entwickeln (Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests).
  - **Go/No-Go-Entscheidungen** auf Basis der Research-Pipeline treffen.
  - **Risk-Limits** auf Order- und Portfolio-Level **vor** der Ausführung durchsetzen.
  - **Live-Track** (Shadow, Testnet, ggf. Live) mit Alerts, Monitoring und Governance-Regeln betreiben.

---

## Aufgaben (Was macht Peak Trade?)

1. **Daten & Märkte**
   - Marktdaten laden, normalisieren (OHLCV), cachen (z. B. Parquet).
   - Exchange-Integration (z. B. Kraken), Feeds, Offline-/Live-Daten.

2. **Strategien & Portfolio**
   - **Strategy Registry:** 15+ produktionsnahe Strategien, 6+ R&D-Strategien (z. B. MA-Crossover, RSI-Reversion).
   - Portfolio-Layer: Multi-Strategie-Portfolios, Recipes, Presets (konservativ/moderat/aggressiv).
   - Position Sizing: Fixed-Fraction, Vol-Regime-Overlay, Trend-Strength-Overlay.

3. **Backtest & Research**
   - Bar-für-Bar-Backtest mit **No-Lookahead-Garantie**, Portfolio-State, PnL-Tracking.
   - Research-Pipeline: Sweeps, Walk-Forward, Monte-Carlo, Stress-Tests.
   - Robustness-Checks und fundierte Bewertung von Strategien/Portfolios.

4. **Risk & Safety**
   - Risk-Limits (Max-Drawdown, Equity-Floor, Position-Limits, VaR, Stress-Gates).
   - **Risk-Layer** inkl. **Emergency Kill Switch** (State Machine, Trigger, Recovery, Audit).
   - Governance-Dokumente, Checklisten, Runbooks, Incident-Drills.

5. **Execution & Live**
   - Execution-Pipeline (Order-Erstellung, Exchange-Anbindung).
   - Live-Ops-CLI (`live_ops`: Health, Orders, Portfolio).
   - Klare Trennung: Research → Shadow → Testnet → Live; Live nur über Safety-Gates.

6. **Reporting & Monitoring**
   - Performance-Metriken (Sharpe, Drawdown, etc.), Equity Curves, Research-Reports.
   - Live-Status-Reports (Markdown/HTML), Alerts (Logging, Webhook, Slack).
   - Web-UI/Dashboard, Health-API (`/health`), Prometheus-Metriken.

7. **AI & Knowledge**
   - Vector-DB/RAG für Research-Entscheidungen, Knowledge-Sources-Governance.
   - Autonomer KI-Workflow (Decision Engine, Scheduler).
   - AI-Helper-Guides (Cursor/Claude/ChatGPT), strukturierte Doku für Prompt-Kontext.

8. **Qualität & Ops**
   - Umfangreiche Tests (pytest, Smoke/Full), Audit-System, Pre-Commit.
   - Konfiguration über TOML (`config/`), Secrets über Env/`.env`.

---

## Wie arbeitet Peak Trade? (Ablauf & Architektur)

### Pipeline (vereinfacht)

```
DATA (Feeds, Loader, Cache)
    → STRATEGY (Registry, Signale)
        → SIZING (Position Sizing Overlay)
            → RISK (Limits, Kill Switch, Gates)
                → BACKTEST / EXECUTION
                    → REPORTING & MONITORING
                        → GOVERNANCE & LIVE TRACK
```

### Typische Abläufe

- **Backtest:** Config laden → OHLCV laden → Strategie aus Registry erstellen → BacktestEngine (bar-für-bar) → Metriken & Reports.
- **Research:** Portfolio-Preset wählen → Research-CLI (portfolio/pipeline) → Robustness & Reports prüfen → Playbook „Research → Live“ für Go/No-Go.
- **Live-Track (Shadow/Testnet):** Live-Config & Risk-Limits prüfen → `live_ops` (Health, Portfolio) → Execution-Session (z. B. Shadow) → Live-Status-Reports, Drills.
- **Safety:** Jeder Live-Trade geht durch Risk-Layer; bei Kill-Switch-Auslösung stoppt die Ausführung, Recovery nur mit Approval-Code und Health-Checks.

### Wichtige Verzeichnisse

- **`src/`** – Quellcode: `data/`, `strategies/`, `backtest/`, `risk/`, `risk_layer/`, `live/`, `execution/`, `reporting/`, `governance/`, `webui/`, etc.
- **`config/`** – TOML-Konfiguration (Allgemein, Portfolios, Sweeps, Risk, Scheduler, …).
- **`scripts/`** – CLI-Skripte (Backtest, Research, Live-Ops, Audit, Dev-Workflow, …).
- **`docs/`** – Ausführliche Dokumentation (Architektur, Runbooks, AI-Guides, …).
- **`tests/`** – pytest-Tests, hohe Abdeckung.

### Governance & Sicherheit

- **Kein autonomes Live-Trading** ohne explizite Freigabe; Safety-Gates und Risk-Layer sind nicht umgehbar.
- Research, Shadow, Testnet und Live sind strikt getrennt; Dokumentation und Runbooks regeln den Übergang.

---

## Kurzfassung für den ersten Prompt an ChatGPT

Du kannst ChatGPT z. B. so kontextgeben:

- *„Peak Trade ist ein modulares Python-Trading-Framework für Krypto mit Safety-First: Data → Strategy → Sizing → Risk → Backtest/Execution → Reporting. Es hat ein Strategy Registry, Backtest-Engine ohne Lookahead, Risk-Layer inkl. Kill-Switch, Live-Ops-CLI und strenge Trennung Research/Shadow/Testnet/Live. Ich arbeite an [z. B. neuer Strategie / Risk-Gate / Doku / Test].“*

---

*Stand: Februar 2025. Basis: README.md, project_summary.md, PEAK_TRADE_OVERVIEW.md, ARCHITECTURE_OVERVIEW.md, config/README.md.*
