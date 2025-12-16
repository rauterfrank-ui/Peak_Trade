# Peak_Trade – Reference Scenario: `multi_style_moderate`

> **Phase 60** – Vollständiger Golden Path vom Research bis zum Incident-Drill
>
> **Ziel:** Ein durchinszeniertes Referenz-Szenario als Story von A–Z, konkret am Portfolio-Preset `multi_style_moderate`

---

## 1. Einleitung & Ziel

Dieses Dokument ist ein **konkretes Referenz-Szenario** für das Portfolio-Preset `multi_style_moderate`. Es führt durch:

- **Research** (inkl. Portfolio-Robustness)
- **Entscheidungsprozess** mittels Playbook
- **Setup & Betrieb** im Shadow-/Testnet-Modus
- **Status-Reports**
- **Incident-Drill** für genau dieses Portfolio

**Zielgruppe:** Future-You, der nach Monaten wieder einsteigen will und einen vollständigen, praxisnahen Durchlauf benötigt.

**Verwandte Dokumente:**

- [`GETTING_STARTED.md`](GETTING_STARTED.md) – Einstieg in Peak_Trade
- [`PEAK_TRADE_V1_RELEASE_NOTES.md`](PEAK_TRADE_V1_RELEASE_NOTES.md) – v1.0 Release-Notizen
- [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Research → Live Prozess
- [`LIVE_STATUS_REPORTS.md`](LIVE_STATUS_REPORTS.md) – Live-Status-Reports
- [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) – Incident-Drills

---

## 2. Überblick: Portfolio-Preset `multi_style_moderate`

### 2.1 Beschreibung

`multi_style_moderate` ist ein Portfolio-Rezept aus `config/portfolio_recipes.toml`. Es kombiniert mehrere Strategien (RSI-Reversion, MA-Trend, Trend-Following) in einem moderaten Risk-Profil.

**Datei:** `config/portfolio_recipes.toml`
**Abschnitt:** `[portfolio_recipes.multi_style_moderate]`

### 2.2 Portfolio-Zusammensetzung

```toml
[portfolio_recipes.multi_style_moderate]
id = "multi_style_moderate"
portfolio_name = "Multi-Style Moderate"
description = "Mixed-Style BTC/ETH Portfolio (Trend + Mean-Reversion, moderate Risk-Profil)"

strategies = [
  "rsi_reversion_btc_moderate",
  "rsi_reversion_eth_moderate",
  "ma_trend_btc_moderate",
  "trend_following_eth_moderate",
]
weights = [0.25, 0.25, 0.25, 0.25]

run_montecarlo = true
mc_num_runs = 3000

run_stress_tests = true
stress_scenarios = ["single_crash_bar", "vol_spike"]
stress_severity = 0.25

format = "both"
risk_profile = "moderate"
tags = ["multi-style", "trend", "reversion", "moderate", "btc", "eth"]
```

**Strategien im Portfolio:**

1. **`rsi_reversion_btc_moderate`** – RSI-Reversion auf BTC (moderate Parameter)
2. **`rsi_reversion_eth_moderate`** – RSI-Reversion auf ETH (moderate Parameter)
3. **`ma_trend_btc_moderate`** – MA-Trend auf BTC (moderate Parameter)
4. **`trend_following_eth_moderate`** – Trend-Following auf ETH (moderate Parameter)

**Gewichtung:** Gleichverteilt (je 25%)

**Risk-Profil:** `moderate` – ausgewogener Kompromiss aus Return & Drawdown

---

## 3. Schritt 1 – Setup & Voraussetzungen

### 3.1 Voraussetzungen

Für dieses Scenario wird vorausgesetzt:

- ✅ **Repository & venv eingerichtet** (siehe [`GETTING_STARTED.md`](GETTING_STARTED.md))
- ✅ **Tests idealerweise einmal erfolgreich gelaufen** (`pytest -q`)
- ✅ **`config/config.toml` vorhanden** und lauffähig
- ✅ **Testnet-API-Keys** für das Live-/Testnet-Setup (falls im Projekt vorgesehen)

**Hinweis:** Der Fokus dieses Szenarios liegt auf Research, Shadow/Testnet & Status. Es werden **keine echten Live-Orders** ausgeführt.

### 3.2 Repository & Environment (falls noch nicht erledigt)

```bash
# Repository & Environment
git clone <REPO_URL> peak_trade
cd peak_trade
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

### 3.3 Config prüfen

Stelle sicher, dass `config/config.toml` vorhanden ist und die relevanten Strategien konfiguriert sind:

```bash
# Prüfe, ob Config existiert
ls -la config/config.toml

# Prüfe, ob Portfolio-Recipes geladen werden können
python -c "import tomli; print(tomli.load(open('config/portfolio_recipes.toml')))"
```

---

## 4. Schritt 2 – Research-Run (Portfolio-Mode)

### 4.1 Portfolio-Research starten

**Command:**

```bash
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

**Was passiert hier?**

- Das Research-CLI lädt das Portfolio-Preset `multi_style_moderate` aus `config/portfolio_recipes.toml`
- Führt Backtests für alle 4 Strategien im Portfolio durch
- Aggregiert Ergebnisse auf Portfolio-Ebene (gewichtete Summe)
- Generiert Reports (Markdown + HTML) mit Metriken und Plots

**Output-Location:**

- Reports landen typischerweise in `results/reports/portfolio_*` oder `reports/portfolio_*`
- Suche nach Dateien mit Timestamp im Namen (z.B. `portfolio_multi_style_moderate_2025-12-07_0900.md`)

### 4.2 Zentrale Metriken im Report

Im Portfolio-Report solltest du folgende Metriken prüfen:

1. **Gesamtrendite (CAGR / Annualized Return)**
   - Sollte positiv sein
   - Für moderate: Erwartung ca. 8–15% p.a.

2. **Sharpe Ratio**
   - Risk-adjusted Return
   - Für moderate: Ziel ≥ 1.0

3. **Max Drawdown**
   - Größter Verlust vom Peak
   - Für moderate: Ziel ≤ 25–30%

4. **Equity-Curve-Form**
   - Sollte relativ glatt sein (keine extremen Sprünge)
   - Trend sollte überwiegend aufwärts sein

5. **Verteilung der Komponenten**
   - Performance der Einzelstrategien im Portfolio
   - Diversifikation: Strategien sollten nicht zu stark korreliert sein

**Beispiel-Interpretation:**

```text
✅ Portfolio zeigt positive CAGR (10.5% p.a.)
✅ Sharpe Ratio ist gut (1.2)
✅ Max Drawdown ist akzeptabel (22% < 30%)
✅ Equity-Curve zeigt stetigen Aufwärtstrend
✅ Diversifikation: Korrelationen zwischen Strategien < 0.5
→ Portfolio ist ein Kandidat für Portfolio-Robustness-Tests
```

### 4.3 Optional: Erweiterte Parameter

Falls du zusätzliche Filter oder Parameter nutzen möchtest:

```bash
# Mit Top-N-Filter (falls unterstützt)
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both \
  --top-n 3
```

**Hinweis:** Die verfügbaren Parameter hängen von deiner aktuellen CLI-Implementierung ab. Prüfe `python scripts/research_cli.py portfolio --help` für Details.

---

## 5. Schritt 3 – Portfolio-Robustness auf `multi_style_moderate`

### 5.1 Portfolio-Robustness-Run

Nutze das bereits existierende CLI `scripts/run_portfolio_robustness.py`:

**Command:**

```bash
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

**Mit expliziten Robustness-Parametern:**

```bash
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --run-montecarlo \
  --mc-num-runs 3000 \
  --run-stress-tests \
  --stress-scenarios single_crash_bar vol_spike \
  --stress-severity 0.25 \
  --format both
```

### 5.2 Was zusätzlich passiert

**Portfolio-Level Monte-Carlo:**

- 3000 Runs mit zufälligen Variationen der Portfolio-Returns
- Verteilung der Metriken (Sharpe, MaxDD, CAGR) unter verschiedenen Szenarien
- Konfidenzintervalle (z.B. 95% CI für Sharpe)

**Portfolio-Level Stress-Tests:**

- **`single_crash_bar`**: Simuliert einen Crash-Tag (z.B. -20% in einem Bar)
- **`vol_spike`**: Simuliert Volatilitätsspitzen
- **Severity 0.25**: 25% Crash-Simulation

**Zusätzliche Metriken:**

- **Korrelation zwischen Strategien**: Sollte niedrig sein (Diversifikation)
- **Risk-Decomposition**: Welche Strategien tragen wie viel zum Gesamt-Risk bei
- **Portfolio-Level Sharpe (OOS)**: Out-of-Sample Sharpe auf Portfolio-Ebene

### 5.3 Interpretation für das Playbook

**Erwartete Ergebnisse für `moderate` Risk-Profil:**

| Metrik | Schwelle (moderate) | Beispiel-Ergebnis |
|--------|---------------------|-------------------|
| **Sharpe (OOS)** | ≥ 1.0 | 1.15 ✅ |
| **Max Drawdown (Portfolio)** | ≤ 30% | 22% ✅ |
| **Stress-Test (Crash)** | Drawdown ≤ 40% | 32% ✅ |
| **Monte-Carlo (95% CI)** | Sharpe 0.9–1.3 | 0.95–1.35 ✅ |

**Beispiel-Interpretation:**

```text
✅ Portfolio Sharpe (OOS): 1.15 (über Schwelle für moderate ≥ 1.0)
✅ Max Drawdown (Portfolio): 22% (unter Schwelle für moderate ≤ 30%)
✅ Stress-Test (Crash): Drawdown 32% (unter Schwelle für moderate ≤ 40%)
✅ Monte-Carlo: 95% der Runs zeigen Sharpe > 0.9
✅ Diversifikation: Korrelationen zwischen Strategien < 0.5
→ Portfolio ist robust und erfüllt moderate-Kriterien
```

**Verweise:**

- [`PHASE_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md`](PHASE_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md) – Portfolio-Robustness-Details
- [`PORTFOLIO_RECIPES_AND_PRESETS.md`](PORTFOLIO_RECIPES_AND_PRESETS.md) – Portfolio-Recipes-Übersicht

---

## 6. Schritt 4 – Entscheidung mit dem Research → Live Playbook

### 6.1 Einbettung

Wir haben nun Backtest + Robustness für `multi_style_moderate`. Jetzt gehen wir Schritt für Schritt das Playbook durch.

**Verweise:**

- [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Vollständiges Playbook

### 6.2 Schritt: Metriken & Schwellen

**Empfohlene Richtwerte für `moderate` Risk-Profil:**

| Profil | Sharpe (OOS) | Max Drawdown (Portfolio) | Stress-Szenario (Crash) | Bemerkung |
|--------|--------------|--------------------------|-------------------------|-----------|
| **moderate** | ≥ 1.0 – 1.3 | ≤ 25–30% | Drawdown im Crash ≤ 35–40% | Balanced Return vs. Risk |

**Prüfung für `multi_style_moderate`:**

- ✅ **Sharpe (OOS)**: 1.15 (≥ 1.0) → **OK**
- ✅ **Max Drawdown**: 22% (≤ 30%) → **OK**
- ✅ **Stress-Test (Crash)**: 32% (≤ 40%) → **OK**
- ✅ **Monte-Carlo**: 95% CI Sharpe 0.95–1.35 → **OK**
- ✅ **Diversifikation**: Korrelationen < 0.5 → **OK**

**Zusätzliche qualitative Checks:**

1. **Regime-Stabilität**: Portfolio sollte in verschiedenen Markt-Regimen (Trending, Ranging, Volatile) funktionieren
2. **Korrelation**: Strategien im Portfolio sollten nicht zu stark korreliert sein (Diversifikation)
3. **Trade-Frequenz**: Sollte zum Risk-Profil passen (moderate = moderate Trade-Frequenz)

### 6.3 Schritt: Go/No-Go Entscheidung & Dokumentation

**Angenommen, das Portfolio erfüllt unsere Playbook-Kriterien:**

- Sharpe > 1.0 ✅
- MaxDD < 30% ✅
- Robustness okay ✅
- Diversifikation gut ✅

**Entscheidung:** `PROMOTE_TO_SHADOW`

**Dokumentation:**

Erstelle einen Eintrag in `docs/PORTFOLIO_DECISION_LOG.md` (oder ähnlich):

```markdown
## Portfolio: multi_style_moderate
**Datum:** 2025-12-15
**Preset:** multi_style_moderate
**Risk-Profil:** moderate

### Kern-Metriken
- Sharpe (OOS): 1.15
- Max Drawdown: 22%
- Stress-Test (Crash): 32%
- Monte-Carlo (95% CI): Sharpe 0.95 - 1.35

### Entscheidung
**Status:** PROMOTE_TO_SHADOW

**Begründung:**
- Sharpe über Schwelle für moderate (≥ 1.0)
- Max Drawdown akzeptabel (22% < 30%)
- Stress-Test zeigt robustes Verhalten
- Monte-Carlo bestätigt Stabilität
- Diversifikation gut (Korrelationen < 0.5)

### Nächste Schritte
1. Shadow-Run für 2 Wochen
2. Vergleich Shadow-Performance mit Research-Ergebnissen
3. Bei Erfolg → Testnet-Promotion

### Reports
- Portfolio-Robustness-Report: `results/reports/portfolio_robustness_2025-12-15/`
- Research-Pipeline-Report: `results/reports/pipeline_multi_style_moderate_2025-12-15/`
```

**Mögliche Entscheidungs-Status:**

- `REJECT` – Portfolio erfüllt Kriterien nicht, wird verworfen
- `REVISE` – Portfolio muss angepasst werden, zurück zu Schritt 2
- `PROMOTE_TO_SHADOW` – Portfolio ist bereit für Shadow-Run
- `PROMOTE_TO_TESTNET` – Portfolio hat Shadow-Phase erfolgreich durchlaufen
- `PROMOTE_TO_LIVE` – Portfolio ist bereit für Live-Trading (nur nach Testnet-Erfolg)

---

## 7. Schritt 5 – Mapping Research → Live-/Testnet-Konfiguration

### 7.1 Prozessualer Überblick

Stelle sicher, dass alle Strategien aus `multi_style_moderate` in der Live-/Testnet-Konfiguration aktiv sind, und dass die Live-Risk-Limits im `[live_risk]`-Block im Einklang mit dem gewünschten Risiko-Profil stehen.

### 7.2 Strategy-Ebene

**Strategy-Konfigurationen in `config/config.toml`:**

Die Research-Presets verwenden bereits Strategy-Konfigurationen, die direkt in Live genutzt werden können:

```toml
# Beispiel: RSI Reversion BTC Moderate
[strategy.rsi_reversion_btc_moderate]
rsi_window = 14
lower = 30.0
upper = 70.0
# ... weitere Parameter
```

**Sicherstellen:**

- ✅ Dieselben Parameter wie im Research-Setup verwendet werden
- ✅ Timeframes & Symbole identisch sind (oder bewusst angepasst und dokumentiert)
- ✅ Stop-Loss / Take-Profit-Parameter konsistent sind

### 7.3 Portfolio-Ebene

**Mapping der `strategies` + `weights` aus `portfolio_recipes.toml`:**

```toml
# Aus portfolio_recipes.toml:
strategies = [
  "rsi_reversion_btc_moderate",
  "rsi_reversion_eth_moderate",
  "ma_trend_btc_moderate",
  "trend_following_eth_moderate",
]
weights = [0.25, 0.25, 0.25, 0.25]
```

**Hinweis:** Wenn der Live-Layer derzeit nur Strategien einzeln behandelt, muss das Portfolio evtl. "implizit" über mehrere parallele Strategien abgebildet werden. Die Gewichte können dann über Position-Sizing oder Capital-Allocation umgesetzt werden.

### 7.4 Risk-Limits

**Verweise auf `[live_risk]` in `config/config.toml`:**

```toml
[live_risk]
enabled = true
base_currency = "EUR"
max_order_notional = 1000.0
max_symbol_exposure_notional = 2000.0
max_total_exposure_notional = 5000.0
max_open_positions = 5
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
block_on_violation = true
```

**Anpassung an Portfolio:**

| Portfolio-Typ | Empfohlene Limits | Begründung |
|---------------|-------------------|------------|
| **moderate** | Moderate Limits, ausgewogen | Balanced Risk |

**Beispiel-Anpassung für `multi_style_moderate`:**

```toml
[live_risk]
# Moderate Portfolio → moderate Limits
max_order_notional = 1000.0  # Standard
max_symbol_exposure_notional = 2000.0  # Standard
max_total_exposure_notional = 5000.0  # Standard
max_daily_loss_abs = 500.0  # Standard
max_daily_loss_pct = 5.0  # Standard
```

### 7.5 Alerts & Monitoring

**Alerts aktivieren:**

```toml
[live_alerts]
enabled = true
min_level = "warning"
sinks = ["log", "stderr"]  # Optional: "webhook", "slack_webhook"
log_logger_name = "peak_trade.live.alerts"
```

**Testen:**

```bash
# Teste Alert-System
python scripts/live_ops.py health --config config/config.toml
```

**Verweise:**

- [`PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md) – Live-Alerts
- [`PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md`](PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md) – Portfolio-Monitoring
- [`SAFETY_POLICY_TESTNET_AND_LIVE.md`](SAFETY_POLICY_TESTNET_AND_LIVE.md) – Safety-Policies (falls vorhanden)

---

## 8. Schritt 6 – Shadow-/Testnet-Betrieb & Monitoring mit `live_ops`

### 8.1 Typischer Betriebs-Flow

Beschreibe einen **typischen Betriebs-Flow** für `multi_style_moderate` im Shadow-/Testnet-Modus:

### 8.2 Health-Check vor Start

```bash
# Health-Check
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

### 8.3 Portfolio-Snapshot

```bash
# Portfolio-Snapshot (Text)
python scripts/live_ops.py portfolio --config config/config.toml

# Portfolio-Snapshot (JSON)
python scripts/live_ops.py portfolio --config config/config.toml --json
```

**Was prüfst du im Portfolio-Snapshot für dieses Portfolio?**

1. **Gesamt-Exposure vs. Live-Risk-Limits**
   - `total_notional` sollte unter `max_total_exposure_notional` liegen
   - Pro-Symbol-Exposure sollte unter `max_symbol_exposure_notional` liegen

2. **Per-Symbol-Positionen**
   - Welche Symbole sind offen? (z.B. BTC/EUR, ETH/EUR)
   - Seiten (long/short) pro Symbol
   - Notional pro Position

3. **Grober PnL-Stand**
   - `total_unrealized_pnl` – aktueller unrealisierter PnL
   - Vergleich mit Research-Erwartungen (mit Toleranz für Market-Noise)

**Beispiel-Interpretation:**

```json
{
  "as_of": "2025-12-15T09:00:00Z",
  "mode": "testnet",
  "positions": [
    {
      "symbol": "BTC/EUR",
      "size": 0.1,
      "side": "long",
      "notional": 4500.0,
      "unrealized_pnl": 45.0
    }
  ],
  "totals": {
    "num_open_positions": 1,
    "total_notional": 4500.0,
    "total_unrealized_pnl": 45.0
  },
  "risk": {
    "allowed": true,
    "reasons": []
  }
}
```

**Interpretation:**

- ✅ `total_notional` (4500.0) < `max_total_exposure_notional` (5000.0) → **OK**
- ✅ `risk.allowed` = true → **OK**
- ✅ PnL positiv (45.0) → **OK**

### 8.4 Verweise

- [`LIVE_TESTNET_TRACK_STATUS.md`](LIVE_TESTNET_TRACK_STATUS.md) – Live-/Testnet-Status
- [`PHASE_51_LIVE_OPS_CLI.md`](PHASE_51_LIVE_OPS_CLI.md) – Live-Ops-CLI-Details

**Hinweis:** Falls du bereits ein Script hast, das Shadow-/Paper-Runs ausführt (z.B. `preview_live_orders.py` etc.), könntest du es erwähnen – aber ohne neue Abläufe zu erfinden, nur das nutzen, was schon existiert.

---

## 9. Schritt 7 – Live-Status-Report für das Portfolio

### 9.1 Status-Report generieren

Nutze das Ergebnis aus Phase 57 (`generate_live_status_report.py`):

**Command:**

```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag multi_style_demo
```

**Mit HTML-Format:**

```bash
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format both \
  --tag multi_style_demo
```

### 9.2 Report-Location

Reports werden benannt als:
- `live_status_YYYY-MM-DD_HHMM_tag.md`
- `live_status_YYYY-MM-DD_HHMM_tag.html`

**Beispiele:**
- `reports/live_status/live_status_2025-12-15_0900_multi_style_demo.md`
- `reports/live_status/live_status_2025-12-15_0900_multi_style_demo.html`

### 9.3 Welche Sektionen prüfst du speziell für `multi_style_moderate`?

1. **Health-Status**
   - Overall Status (OK/DEGRADED/FAIL)
   - Einzel-Checks (Config, Exchange, Alerts, Live Risk)

2. **Portfolio-Teil**
   - **Equity**: Geschätzte Equity (Startkapital + unrealisierter PnL)
   - **Exposure**: Gesamt-Exposure vs. Limits
   - **Per-Symbol**: Positionen pro Symbol (BTC/EUR, ETH/EUR)

3. **Risk- & Alerts-Sektion**
   - Live-Risk-Limits Status
   - Alert-Hinweise (falls vorhanden)

### 9.4 Tag-Wahl

**Vorschlag:** Wähle den Report-Namen / Tag sinnvoll:

- `multi_style_demo` – für Demo-/Test-Runs
- `testnet` – für Testnet-Runs
- `daily` – für tägliche Reports
- `weekly` – für wöchentliche Reports

**Hinweis:** Für eine "Story" dieses Scenario kannst du eine Serie von Reports über mehrere Tage/Wochen wiederholen.

### 9.5 Verweise

- [`LIVE_STATUS_REPORTS.md`](LIVE_STATUS_REPORTS.md) – Live-Status-Reports-Details

---

## 10. Schritt 8 – Incident-Drill für dieses Portfolio

### 10.1 Szenario-Auswahl

Wähle eines der bestehenden Szenarien aus [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md), z.B.:

- **Szenario 3 – Risk-Limit-Verletzung (Order-/Portfolio-Level)**

### 10.2 Kurze Erinnerung an das Szenario

**Ziel:** Praktisch üben, was passiert, wenn ein **Live-Risk-Limit** greift:
- Wird blockiert?
- Wird ein Alert generiert (inkl. Webhook/Slack)?
- Weißt du, was als Nächstes zu tun ist?

### 10.3 Konkret für `multi_style_moderate` aufsetzen

**Schritt 1: Config sichern (Backup)**

```bash
cp config/config.toml config/config.before_risk_drill.toml
```

**Schritt 2: `live_risk` im config anpassen (temporär)**

```toml
# In config/config.toml:
[live_risk]
enabled = true
max_total_exposure_notional = 10.0  # Sehr niedrig, um Verstoß zu erzwingen
max_order_notional = 5.0            # Noch niedriger
max_daily_loss_abs = 1.0             # Sehr eng
```

**Schritt 3: Drill auslösen über Live-Ops / Preview-CLI**

```bash
# Orders-Preview mit Risk-Check
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml \
  --enforce-live-risk

# Oder Portfolio-Snapshot (Portfolio-Level Risk)
python scripts/live_ops.py portfolio \
  --config config/config.toml
```

**Erwartetes Verhalten:**

- ✅ `LiveRiskLimits.check_orders()` schlägt an
- ✅ Alerts-System erzeugt mindestens einen WARNING/CRITICAL-Alert
- ✅ Webhook/Slack-Sinks (sofern konfiguriert) feuern
- ✅ Orders werden blockiert oder klar als "nicht erlaubt" markiert

### 10.4 Erfolgskriterien

**Das System:**

- ✅ Blockiert Orders oder markiert sie klar als "nicht erlaubt" (je nach Config)
- ✅ Ein Alert wird ausgelöst:
  - Im Log
  - Auf stderr
  - Ggf. via Webhook/Slack

**Du kannst:**

- ✅ Das entsprechende **Risk-/Incident-Runbook** anwenden:
  - Trade-/Strategy-Pause?
  - Config zurücksetzen?
  - Post-Mortem-Eintrag?

### 10.5 Dokumentation in `INCIDENT_DRILL_LOG.md`

**Beispiel-Eintrag:**

```markdown
## Drill: Risk-Limit-Verletzung für multi_style_moderate
**Datum:** 2025-12-15
**Szenario:** Szenario 3 – Risk-Limit-Verletzung (Order-/Portfolio-Level)
**Portfolio:** multi_style_moderate

### Setup
- Temporär `max_total_exposure_notional` auf 10.0 gesenkt
- Temporär `max_order_notional` auf 5.0 gesenkt
- Temporär `max_daily_loss_abs` auf 1.0 gesenkt

### Ergebnis
**Status:** ✅ OK

**Beobachtungen:**
- ✅ `LiveRiskLimits.check_orders()` hat korrekt blockiert
- ✅ Alert wurde ausgelöst (WARNING-Level)
- ✅ Alert wurde im Log und auf stderr ausgegeben
- ✅ Webhook/Slack-Sinks haben gefeuert (falls konfiguriert)

### Erkenntnisse
- Risk-Limits funktionieren wie erwartet
- Alert-System reagiert korrekt auf Violations
- Runbook-Schritte sind klar dokumentiert

### Follow-Ups
- Keine

### Cleanup
- Config aus Backup wiederhergestellt
```

### 10.6 Cleanup

```bash
# Config aus Backup wiederherstellen
mv config/config.before_risk_drill.toml config/config.toml
```

### 10.7 Wichtige Hinweise

**Betone klar:**

- ✅ **Drill nur in Testnet/Shadow/Paper-Umgebung**, nie in echtem Live mit Kapital
- ✅ Das Ziel ist Training & Validierung der Runbooks, nicht "Chaos erzeugen"

### 10.8 Verweise

- [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) – Incident-Drills
- [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md) – Drill-Log
- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Runbooks

---

## 11. Zusammenfassung & Learnings

### 11.1 Was dieses Scenario gezeigt hat

Dieses Referenz-Szenario hat gezeigt, wie:

1. **Research, Robustness, Playbook, Live-/Testnet & Drills zusammenspielen**
   - Von Portfolio-Preset bis zum Incident-Drill
   - Jeder Schritt ist dokumentiert und reproduzierbar

2. **Metriken-basierte Entscheidungen** funktionieren
   - Klare Go/No-Go-Kriterien
   - Dokumentierte Entscheidungsprozesse

3. **Live-/Testnet-Operations** strukturiert ablaufen
   - Health-Checks, Portfolio-Snapshots, Status-Reports
   - Monitoring & Alerts

4. **Incident-Drills** praktisch geübt werden können
   - Risk-Limit-Verletzungen
   - Alert-System-Validierung

### 11.2 Warum `multi_style_moderate` ein guter "Golden Path" ist

- **Mehrere Strategien**: Demonstriert Portfolio-Diversifikation
- **Moderates Risiko**: Ausgewogener Kompromiss aus Return & Drawdown
- **Gute Demonstration der Infrastruktur**: Zeigt alle Komponenten (Research, Robustness, Live-Ops, Drills)

### 11.3 Ausblick

**Analog können weitere Presets durch denselben Flow geschickt werden:**

- `rsi_reversion_conservative` – für konservatives Trading
- `rsi_reversion_aggressive` – für aggressives Trading
- `multi_style_aggressive` – für aggressive Multi-Style-Portfolios

**Jeder Preset kann durch denselben Prozess:**

1. Research-Run
2. Portfolio-Robustness
3. Playbook-Entscheidung
4. Mapping → Live-Konfiguration
5. Shadow-/Testnet-Betrieb
6. Status-Reports
7. Incident-Drills

---

## 12. Quick-Reference: Commands für `multi_style_moderate`

### Research

```bash
# Portfolio-Research
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both

# Portfolio-Robustness
python scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

### Live-Ops

```bash
# Health-Check
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Snapshot
python scripts/live_ops.py portfolio --config config/config.toml --json
```

### Status-Reports

```bash
# Status-Report generieren
python scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format markdown \
  --tag multi_style_demo
```

### Incident-Drill

```bash
# Config sichern
cp config/config.toml config/config.before_risk_drill.toml

# Risk-Limits temporär senken (in config.toml)
# ... dann Drill auslösen ...

# Config wiederherstellen
mv config/config.before_risk_drill.toml config/config.toml
```

---

**Built with ❤️ and safety-first architecture**








