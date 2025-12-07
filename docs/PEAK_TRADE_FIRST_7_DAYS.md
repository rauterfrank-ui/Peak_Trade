# Peak_Trade – First 7 Days Onboarding Guide

**Version:** v1.0
**Ziel:** Neue Nutzer (oder du selbst in 6 Monaten) kommen in **7 Tagen** von „null Kontext" zu:
- lauffähiger Umgebung,
- ersten Backtests & Reports,
- ersten Shadow/Testnet-Runs,
- Verständnis für Monitoring & Alerts,
- einer eigenen kleinen Mini-Research-Idee.

---

## 1. Zielgruppe & Voraussetzungen

### Zielgruppe

- Neue **Researcher**, die Strategien entwickeln, testen und auswerten wollen.
- **Operatoren**, die Shadow-/Testnet-Runs starten und überwachen.
- **Reviewer**, die verstehen wollen, was Peak_Trade v1.0 kann – ohne direkt Code zu schreiben.

### Technische Voraussetzungen

- Grundlegende Erfahrung mit:
  - Git
  - Python 3.x
  - Terminal
- Lokale Umgebung (empfohlen):
  - macOS oder Linux
  - Python-Umgebung mit `venv` oder ähnlichem
- Empfohlen: vorher einmal **`docs/GETTING_STARTED.md`** durchgehen.

---

## 2. Überblick – 7 Tage in der Draufsicht

| Tag | Rolle (primär) | Fokus                         | Ergebnis                                                   |
|-----|----------------|-------------------------------|------------------------------------------------------------|
| 1   | Alle           | Setup & Tests                 | Repo läuft lokal, `pytest` grün                           |
| 2   | Researcher     | Erste Backtests               | Erste Backtest-Runs + Verständnis für Daten & Config      |
| 3   | Researcher     | Strategien verstehen/anpassen | Kleine Strategie-Anpassung + erneuter Backtest           |
| 4   | Researcher     | Research-Pipeline v2          | Sweep + Monte-Carlo + Stress-Test durch Pipeline          |
| 5   | Operator       | Shadow-/Testnet-Orchestrator  | Erster Shadow-/Testnet-Run via CLI                        |
| 6   | Operator       | Monitoring & Alerts & Web-UI  | CLI-Monitoring, Alerts-Checks, Web-Dashboard v0           |
| 7   | Mixed          | Mini-Projekt & Doku           | Eigene kleine Mini-Research-Story inkl. Ergebnis-Notizen  |

---

## 3. Tag 1 – Setup & Test-Suite

**Ziel:**
Projekt clonen, Umgebung aufsetzen, sicherstellen, dass die Test-Suite auf deiner Maschine läuft.

### Schritte

1. **Repo klonen**

```bash
git clone <DEIN_PEAK_TRADE_REPO_URL> peak_trade
cd peak_trade
```

2. **Python-Umgebung aktivieren**
   (Details stehen in `docs/GETTING_STARTED.md` – hier nur ein Beispiel mit venv):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

3. **Tests laufen lassen**

```bash
pytest
```

Erwartung:

* ca. **1733 Tests**, 5 skipped, **0 Warnings**.
* Falls etwas rot ist: zuerst `docs/GETTING_STARTED.md` & `docs/PEAK_TRADE_STATUS_OVERVIEW.md` checken.

### Erfolgs-Check

* Du kannst `pytest` ohne Fehler laufen lassen.
* Du weißt, wo:
  * `config/config.toml`,
  * `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`,
  * `docs/GETTING_STARTED.md`
    liegen.

---

## 4. Tag 2 – Erste Backtests & Registry-Demo

**Ziel:**
Einen ersten Backtest-Lauf ausführen und sehen, wie Ergebnisse in der Registry/Reports landen.

### Schritte

1. **v1.0 Overview lesen (Überfliegen reicht)**

* `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`
  Fokus:
  * Architektur-Snapshot,
  * Rollen & Golden Paths,
  * Test- & Qualitätsstatus.

2. **Demo-Backtest laufen lassen**

```bash
python scripts/demo_registry_backtest.py
```

Beobachte:

* Konsolen-Output (welche Strategien, welche Zeiträume),
* wohin Ergebnisse geschrieben werden (z.B. `experiments/`, `reports/` o.ä.).

3. **Ergebnis-Dateien anschauen**

* Öffne den generierten Backtest-Report (Markdown oder HTML), z.B.:
  * `reports/backtests/...`
  * oder was `demo_registry_backtest.py` am Ende ausgibt.

### Erfolgs-Check

* Du hast mindestens **einen** Backtest-Lauf ausgeführt.
* Du findest die zugehörigen Resultate (Registry/Report).
* Du kannst grob sagen: *„So sieht ein Backtest-Resultat in Peak_Trade aus."*

---

## 5. Tag 3 – Strategien verstehen & minimal tweaken

**Ziel:**
Verstehen, wie Strategien im Code aussehen und eine kleine Parameteränderung durchführen.

### Schritte

1. **Strategie-Code anschauen**

Öffne z.B.:

* `src/strategies/ma_crossover.py`
* `src/strategies/trend_following.py`
* `src/strategies/mean_reversion.py`

Achte auf:

* Parameter (z.B. Lookback-Längen, Schwellenwerte),
* Struktur (Signal-Berechnung, Risk-Filter, etc.).

2. **Kleine Änderung machen**

Beispiel-Ideen:

* Fast/Slow-MA-Längen minimal anpassen.
* Schwelle für einen Entry/Exit leicht verändern.
* Nur eine Strategie auf einmal ändern.

3. **Demo-Backtest erneut laufen lassen**

```bash
python scripts/demo_registry_backtest.py
```

Vergleiche:

* PnL / Sharpe / Drawdown vor & nach der Änderung.
* Ob sich Trades / Equity curve sichtbar verändert.

### Erfolgs-Check

* Du hast **mindestens eine Strategie leicht verändert**.
* Du siehst, welchen Effekt diese Änderung auf ein Backtest-Resultat hat.
* Du verstehst grob: *„Wo würde ich eine neue Strategie einhängen?"*

---

## 6. Tag 4 – Research-Pipeline v2 (Sweeps, Monte-Carlo, Stress-Tests)

**Ziel:**
Die **Research-Pipeline v2** einmal komplett durchlaufen, um einen vollwertigen Research-Run zu sehen.

### Schritte

1. **Dokumentation lesen**

* `docs/PHASE_30_REPORTING_AND_VISUALIZATION.md`
* ggf. Doku zur **Research-Pipeline v2** (Verweis in `PEAK_TRADE_STATUS_OVERVIEW.md`).
* **NEU:** [`docs/PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md`](PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md) – vollständige End-to-End-Workflows für typische Research-Aufgaben.

2. **Pipeline-Beispiel ausführen**

Beispiel (ggf. Parameter/Names an dein Repo anpassen):

```bash
python scripts/research_cli.py pipeline \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --format both \
  --with-plots \
  --top-n 5 \
  --run-walkforward \
  --walkforward-train-window 90d \
  --walkforward-test-window 30d \
  --run-montecarlo \
  --mc-num-runs 1000 \
  --run-stress-tests \
  --stress-scenarios single_crash_bar vol_sp
```

3. **Reports ansehen**

* Erzeuge Backtest-/Experiment-Reports mit:
  * `scripts/generate_backtest_report.py`
  * `scripts/generate_experiment_report.py`

  (Details siehe Reporting-Doku.)

### Erfolgs-Check

* Du hast einen **Sweep + Walk-Forward + Monte-Carlo + Stress-Tests** durchlaufen.
* Du findest die entsprechenden Reports (Markdown/HTML) und kannst sie öffnen.
* Du weißt jetzt: *„Wie würde ich eine Hypothese erst richtig durchprügeln, bevor ich an Live denke?"*

---

## 7. Tag 5 – Shadow-/Testnet-Orchestrator

**Ziel:**
Einen Shadow- oder Testnet-Run über den Orchestrator starten, seinen Status prüfen und ihn wieder stoppen.

### Schritte

1. **Doku-Abschnitt zum Orchestrator lesen**

* `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
  * Abschnitt **10a. Testnet-Orchestrator v1**

2. **Shadow-Run starten (Beispiel)**

```bash
python scripts/testnet_orchestrator_cli.py start-shadow \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m \
  --config config/config.toml
```

Merke dir die ausgegebene **Run-ID**.

3. **Status prüfen**

```bash
python scripts/testnet_orchestrator_cli.py status
```

4. **Run stoppen**

```bash
python scripts/testnet_orchestrator_cli.py stop --run-id <DEINE_RUN_ID>
```

### Erfolgs-Check

* Du hast einen Shadow-/Testnet-Run gestartet, im Status gesehen und sauber gestoppt.
* Du weißt: *„Wie bringe ich Peak_Trade in Bewegung – aber noch ohne echte Live-Orders?"*

---

## 8. Tag 6 – Monitoring, Alerts & Web-Dashboard

**Ziel:**
Laufende Runs im CLI & Web-Dashboard beobachten und Alerts prüfen.

> Tipp: Starte parallel einen Shadow-/Testnet-Run (z.B. wie an Tag 5), damit es etwas zu sehen gibt.

### 8.1 Monitoring-CLI

1. **Übersicht aller Runs**

```bash
python scripts/live_monitor_cli.py overview
```

2. **Details zu einem Run**

```bash
python scripts/live_monitor_cli.py run --run-id <DEINE_RUN_ID>
```

3. **Follow-Modus**

```bash
python scripts/live_monitor_cli.py follow \
  --run-id <DEINE_RUN_ID> \
  --interval 5
```

### 8.2 Alerts

1. **Doku lesen**

* `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
  * Abschnitt **10c. Alerts & Incident Notifications v1**

2. **Alert-Regeln einmal ausführen**

```bash
python scripts/live_alerts_cli.py run-rules \
  --run-id <DEINE_RUN_ID> \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10 \
  --error-spike-max-errors 5 \
  --error-spike-window-minutes 10
```

(Später kann das z.B. per Cron alle 5 Minuten laufen.)

### 8.3 Web-Dashboard v0

1. **Web-Server starten**

```bash
python scripts/live_web_server.py
# oder:
# uvicorn src.live.web.app:app --host 127.0.0.1 --port 8000 --reload
```

2. **Im Browser öffnen**

* `http://localhost:8000/` → Übersicht aller Runs
* `http://localhost:8000/dashboard` → Dashboard
* Run-Detailseite (nach Link klicken)

### Erfolgs-Check

* Du kannst:
  * laufende Runs im CLI und Web sehen,
  * Alerts für einen Run ausführen,
  * das Web-Dashboard v0 bedienen.
* Du verstehst: *„Wie erkenne ich Probleme (PnL-Drop, No-Events, Errors) im Betrieb?"*

---

## 9. Tag 7 – Mini-Projekt & deine erste „Story"

**Ziel:**
Eine **kleine eigene Story** durchspielen – von Idee bis Auswertung – und sie kurz festhalten.

### Vorschlag für ein Mini-Projekt

1. **Wähle eine kleine Idee**, z.B.:
   * eine andere Symbol/Timeframe-Kombination,
   * eine leicht angepasste Strategiekonfiguration,
   * ein alternatives Risk-Filter-Setting.

2. **Backtest & Pipeline**

* Fahre:
  * einen klassischen Backtest (z.B. via Demo-/Registry-Script),
  * optional einen kleinen Pipeline-Run (Sweep mit reduzierten Parametern).

3. **Shadow-/Testnet-Run**

* Starte einen Shadow-Run mit deiner Konfiguration.
* Überwache ihn kurz via Monitoring-CLI oder Web-Dashboard.

4. **Notiere dein Ergebnis**

* Erstelle z.B. eine kleine Markdown-Datei:
  * `docs/user_notes/FIRST_7_DAYS_<DEIN_NAME>.md`

  Inhalt (kurz):
  * Was war deine Idee?
  * Welche Skripte/Kommandos hast du genutzt?
  * Was ist grob rausgekommen?
  * Was würdest du als nächstes testen?

### Erfolgs-Check

* Du hast Peak_Trade **einmal komplett** für deine eigene Fragestellung benutzt.
* Du hast irgendwo eine Notiz, die du später wiederfinden kannst.

---

## 10. Wenn du irgendwo hängst

Nutze die bestehende Doku:

* **Architektur & Gesamtbild**
  * `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`

* **Status & Phasen**
  * `docs/PEAK_TRADE_STATUS_OVERVIEW.md`

* **Setup & Basics**
  * `docs/GETTING_STARTED.md`

* **Live/Testnet-Operation**
  * `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
  * `docs/LIVE_READINESS_CHECKLISTS.md`

* **CLI-Übersicht**
  * `docs/CLI_CHEATSHEET.md`

* **AI-/Assistenten-Workflows (falls vorhanden)**
  * `docs/ai/…` (z.B. CLAUDE-/GPT-Guides)

---

## 11. Nach den ersten 7 Tagen – mögliche nächste Schritte

* Tiefer in die **Strategie-Entwicklung** einsteigen (neue Strategien, besseres Risk-Model).
* Mehr mit der **Research-Pipeline v2** spielen (größere Sweeps, mehr Szenarien).
* Testnet-Runs länger laufen lassen und **Realismus (Slippage, Fees, Gaps)** schärfen.
* Dich mit der **v1.x-Roadmap** vertraut machen und gezielt einzelne Phasen angehen.

> Wenn du diese 7 Tage durch hast, bist du nicht mehr „neuer User", sondern ein **vollwertiger Operator/Researcher in Peak_Trade v1.0**.
