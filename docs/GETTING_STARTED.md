# Peak_Trade – Getting Started

> **Ziel:** In < 1h ein Gefühl für Peak_Trade bekommen

Dieses Dokument führt dich Schritt für Schritt durch deine erste Stunde mit Peak_Trade. Der Fokus liegt auf:

- Research-Flow (Portfolio-Presets, Robustness)
- Live-/Ops-Flow (Health, Portfolio, Status-Reports)
- **Ohne echte Live-Trades** – alles im Safe-Mode

---

## 1. Voraussetzungen

- **Python 3.11+** (prüfen mit `python --version`)
- `git` (für Repository-Klonen)
- `virtualenv` oder `venv` (meist bereits in Python enthalten)
- Optional: API-Keys für Testnet-Exchange (falls du später Testnet nutzen willst – für den Quickstart nicht nötig)

---

## 2. Setup

### 2.1 Repository klonen & aktivieren

```bash
git clone <REPO_URL> peak_trade
cd peak_trade
```

### 2.2 Virtual Environment erstellen & aktivieren

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2.3 Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2.4 (Optional) Test-Suite prüfen

```bash
pytest -q
```

Dieser Schritt ist optional, aber hilfreich, um sicherzustellen, dass die Test-Suite grundsätzlich grün ist.

---

## 3. Erste Research-Session

### 3.1 Portfolio-Preset auswählen

Peak_Trade kommt mit vordefinierten Portfolio-Presets in `config/portfolio_recipes.toml`. Für den Start empfehlen wir:

- **`rsi_reversion_conservative`** – Konservatives RSI-Reversion-Portfolio (gut für erste Tests)
- **`multi_style_moderate`** – Gemischtes Portfolio (Trend + Mean-Reversion, moderate)

### 3.2 Ersten Research-Run starten

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_conservative \
  --format both
```

**Was passiert hier?**

- Das Research-CLI lädt das Portfolio-Preset
- Führt Backtests für alle Strategien im Portfolio durch
- Generiert Reports (Markdown + HTML) mit Metriken

**Output-Location:**

- Reports landen typischerweise in `reports/portfolio_robustness/` oder ähnlich
- Suche nach Dateien mit Timestamp im Namen (z.B. `portfolio_robustness_2025-12-07_0900.md`)

### 3.3 Metriken anschauen

Die Reports enthalten typischerweise:

- **Return** – Gesamt-Return des Portfolios
- **Sharpe Ratio** – Risk-adjusted Return
- **Max Drawdown** – Maximaler Verlust
- **Portfolio-Exposure** – Gesamt-Exposure pro Symbol
- **Per-Strategy-Breakdown** – Einzelne Strategie-Performance

### 3.4 (Optional) Portfolio-Robustness vertiefen

Für detailliertere Robustness-Analysen:

```bash
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset rsi_reversion_conservative \
  --format both
```

Dies führt zusätzlich Monte-Carlo-Simulationen und Stress-Tests durch.

---

## 4. Erste Live-/Testnet-Interaktion (nur Status)

> **Wichtig:** Dieser Schritt ist primär **Read-Only / Status** – keine echten Orders werden ausgeführt.

### 4.1 Health-Check

```bash
python scripts/live_ops.py health --config config/config.toml
```

**Was prüft `health`?**

- **Config**: Config-Datei geladen & konsistent?
- **Exchange**: Exchange-Client initialisierbar?
- **Alerts**: Alert-System konfiguriert?
- **Live Risk**: Risk-Limits geladen & konsistent?

**Erwartete Ausgabe:**

```
🏥 Peak_Trade Live/Testnet Health Check
======================================================================
Config: ✅ OK
Exchange: ✅ OK
Alerts: ✅ OK (2 Sink(s) konfiguriert)
Live Risk: ✅ OK
Overall Status: OK
```

### 4.2 Portfolio-Snapshot

```bash
python scripts/live_ops.py portfolio --config config/config.toml --json
```

**Was zeigt `portfolio`?**

- **Mode**: Umgebung (shadow/testnet/live)
- **Positions**: Offene Positionen (Symbol, Size, Side, Notional, PnL)
- **Totals**: Gesamt-Exposure, Unrealized PnL
- **Risk**: Risk-Check-Ergebnis (falls aktiv)

**JSON-Output-Struktur:**

```json
{
  "as_of": "2025-12-07T09:00:00Z",
  "mode": "testnet",
  "positions": [...],
  "totals": {
    "num_open_positions": 0,
    "total_notional": 0.0,
    "total_unrealized_pnl": 0.0
  },
  "risk": {
    "allowed": true,
    "reasons": []
  }
}
```

---

## 5. Live-Status-Report generieren

### 5.1 Ersten Daily-Report erstellen

```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag daily
```

**Was passiert?**

- Das Script sammelt Health- und Portfolio-Daten via `live_ops`
- Generiert einen strukturierten Markdown-Report
- Speichert ihn in `reports/live_status/` mit Timestamp

**Report-Location:**

- `reports/live_status/live_status_YYYY-MM-DD_HHMM_daily.md`

### 5.2 Report-Inhalt

Der Report enthält vier Hauptsektionen:

1. **Health Overview**
   - Overall Status (OK/DEGRADED/FAIL)
   - Einzel-Checks (Config, Exchange, Alerts, Live Risk)

2. **Portfolio Snapshot**
   - Mode, Aggregate (Equity, Exposure, Free Cash)
   - Per-Symbol Exposure (Tabelle mit Positionen)

3. **Risk & Alerts**
   - Live-Risk Limits Status
   - Alert-Hinweise

4. **Notes (Operator)**
   - Optionaler Freitext für TODOs, Follow-Ups

**Siehe auch:** [`docs/LIVE_STATUS_REPORTS.md`](LIVE_STATUS_REPORTS.md) für Details.

---

## 6. Nächste Schritte

### 6.1 Research-Flow vertiefen

- **Portfolio-Recipes & Presets**  
  [`docs/PORTFOLIO_RECIPES_AND_PRESETS.md`](PORTFOLIO_RECIPES_AND_PRESETS.md)

- **Research → Live Playbook**  
  [`docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)

### 6.2 Live-/Ops-Flow vertiefen

- **Live-Status-Reports**  
  [`docs/LIVE_STATUS_REPORTS.md`](LIVE_STATUS_REPORTS.md)

- **Live-/Testnet-Status**  
  [`docs/LIVE_TESTNET_TRACK_STATUS.md`](LIVE_TESTNET_TRACK_STATUS.md)

- **Live-Ops CLI**  
  [`docs/CLI_CHEATSHEET.md`](CLI_CHEATSHEET.md) – Abschnitt "Live-Ops CLI"

### 6.3 Safety & Drills

- **Incident-Drills**  
  [`docs/INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md)

- **Runbooks & Incident-Handling**  
  [`docs/RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md)

- **Governance & Safety**  
  [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md)

### 6.4 AI-Assistenz

- **Claude Guide**  
  [`docs/ai/CLAUDE_GUIDE.md`](ai/CLAUDE_GUIDE.md)

### 6.5 Architektur & Status

- **Architektur-Übersicht**  
  [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md)

- **Projekt-Status**  
  [`docs/PEAK_TRADE_STATUS_OVERVIEW.md`](PEAK_TRADE_STATUS_OVERVIEW.md)

### 6.6 Reference Scenario (empfohlen nach der ersten Stunde)

- **Reference Scenario `multi_style_moderate`**  
  Ein vollständiger Golden Path vom Research über Portfolio-Robustheit bis zum Live-/Testnet-Status und einem Incident-Drill findest du in  
  [`docs/REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md`](REFERENCE_SCENARIO_MULTI_STYLE_MODERATE.md).

### 6.7 Weiterführende Gesamtübersicht

- **Vollständige v1.0-Übersicht**  
  Wenn du die wichtigsten CLI-Flows ausprobiert hast, bietet  
  [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md)  
  eine vertiefte v1.0-Übersicht mit Rollen- und Flow-Perspektive.

---

## 7. Häufige Fragen

### Wie füge ich eine neue Strategie hinzu?

Siehe [`docs/DEV_GUIDE_ADD_STRATEGY.md`](DEV_GUIDE_ADD_STRATEGY.md)

### Wie konfiguriere ich Live-Risk-Limits?

Siehe [`docs/LIVE_RISK_LIMITS.md`](LIVE_RISK_LIMITS.md) und [`docs/DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md`](DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md)

### Wie erstelle ich ein neues Portfolio-Recipe?

Siehe [`docs/DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md`](DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md)

### Wo finde ich alle CLI-Commands?

Siehe [`docs/CLI_CHEATSHEET.md`](CLI_CHEATSHEET.md)

---

**Built with ❤️ and safety-first architecture**

