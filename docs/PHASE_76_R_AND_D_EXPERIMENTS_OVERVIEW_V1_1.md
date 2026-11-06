# Phase 76 – R&D Experiments Overview v1.1 – R&D Hub im Web-Dashboard

**Status:** ✅ Abgeschlossen  
**Commit:** `5f3e3b1 feat(phase76): R&D Experiments Overview v1.1 - R&D Hub im Web-Dashboard`

---

## 1. Ziel der Phase

Phase 76 hebt die bisherige R&D-Experimente-Übersicht zu einem zentralen **R&D Hub** im Peak_Trade Web-Dashboard an.
Der Hub soll:

* laufende, erfolgreiche und fehlerhafte Experimente auf einen Blick sichtbar machen
* Daily-Summary-Kacheln für „heute" und „aktuell laufend" bereitstellen
* nach **Run-Type**, **Tier** und **Experiment-Category** filterbar sein
* direkt an Registry und R&D-API angebunden sein, ohne zusätzliche Skripte oder manuelle Queries

Damit wird R&D von einer „Logfile-/CLI-Perspektive" zu einer **Dashboard-zentrierten Steuerzentrale** für Research.

---

## 2. Kern-Deliverables

### R&D Hub UI v1.1

* Neue Template-Datei `templates/peak_trade_dashboard/r_and_d_experiments.html`
* Kompaktes Tabellenlayout mit Status-Badges (z.B. success, running, failed)
* Run-Type-Badges (z.B. `backtest`, `portfolio_backtest`, `forward_signal`, `scheduler_job` etc.)
* Quick-Actions (z.B. Link zu Detail-Reports / Registry-Ansichten)

### Daily Summary & Run-Type-Filter

* Kacheln wie „Heute fertig", „Aktuell laufend", „Heute fehlgeschlagen"
* Filterleiste mit:
  * `run_type`
  * `tier` (z.B. `core`, `beta`, `r_and_d`)
  * `experiment_category` (z.B. „Strategy-Sweeps", „Regime-Analysen")
* Integration in `src/webui/app.py` zur Bereitstellung der Filter- und Daily-Stats-Daten

### R&D-API v1.1

* Erweiterte API in `src/webui/r_and_d_api.py`
* Neue/erweiterte Endpoints zur Abfrage von:
  * gefilterten Experiment-Listen
  * Daily-Statistiken (z.B. Anzahl Experimente pro Status und Run-Type)
* Unterstützung neuer Felder wie:
  * `run_type`
  * `tier`
  * `experiment_category`
  * `date_str` (normierte Tagesaggregation für Daily-Views)

### Dokumentation

* Neues Phase-Dokument: `docs/PHASE_76_R_AND_D_EXPERIMENTS_OVERVIEW_V1_1.md`
* Update der Mini-Roadmap: `docs/PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md` (Phase-76-Eintrag angepasst)

### Tests

* **65 spezialisierte Tests** in `tests/test_r_and_d_api.py` (übertrifft Ziel von 51)
* Abdeckung u.a.:
  * Filterkombinationen (`run_type`, `tier`, `experiment_category`, `preset`, `strategy`)
  * Paging / Limit (Boundary Tests, Min/Max Validation)
  * Daily-Stats-Berechnungen (`/today`, `/running`, `/categories`)
  * Error-Cases (ungültige Parameter, 404, Validation Errors)
  * Edge-Cases (fehlende Timestamps, leere Results, kurze Timestamps)
  * v1.1 Features (Status-Badges, Run-Type-Badges, experiment_category)

---

## 3. Operator- & Research-Workflow (High Level)

### 1. Experimente starten

* R&D-/Research-Jobs laufen wie gewohnt über die bestehenden CLI-Skripte / Scheduler-Jobs.

### 2. R&D Hub öffnen (Web-Dashboard)

* Aufruf des Web-Dashboards und Wechsel in den R&D-Bereich („Experiments / R&D Hub").

### 3. Daily Overview nutzen

* Daily-Kacheln checken:
  * Wie viele Experimente heute gelaufen sind
  * Wie viele davon erfolgreich / fehlgeschlagen / laufend sind
* Erste Plausibilitätskontrolle: „Sieht das Volumen und die Fehlerrate plausibel aus?"

### 4. Run-Type-Filter anwenden

* Filter auf relevante Run-Types (z.B. nur `portfolio_backtest` oder nur `forward_signal`)
* Optional Kombination mit:
  * Tier (`core` vs. `r_and_d`)
  * Experiment-Category (z.B. „Armstrong-Strategien", „Ehlers-Filtern", „Lopez-de-Prado-Signalsets")

### 5. Drill-Down & Fehleranalyse

* Identifikation von fehlerhaften Experimenten über Status-Badges
* Übergang von der UI zur Registry / Detail-Reports (z.B. Logfiles, Plots, HTML-Reports)
* Grundlage für:
  * R&D-Dailies
  * Cleanup-/Housekeeping-Routinen
  * Priorisierung weiterer Research-Wellen

---

## 4. Technische Umsetzung (Kurzüberblick)

### Backend / API

* Datei: `src/webui/r_and_d_api.py`
* Stellt gefilterte Listen und Daily-Stats bereit
* Saubere Trennung von:
  * Query-/Filterlogik
  * Serialisierung für das Web-Dashboard

### App-Integration

* Datei: `src/webui/app.py`
* Registrierung der R&D-Endpoints im Web-Stack
* Wiring der Run-Type-Filter und Daily-Stats-Funktionalität zur Template-Engine

### Frontend / Template

* Datei: `templates/peak_trade_dashboard/r_and_d_experiments.html`
* Nutzung von:
  * Tabellen-Layout mit Badges
  * Filter-Controls (Drop-Downs / Buttons)
  * Daily-Stat-Kacheln
* Ziel: schnelle visuelle Erfassung + minimaler Klickaufwand für Operatoren

---

## 5. Verknüpfte Dateien & Artefakte

### Dokumentation

* `docs/PEAK_TRADE_MINI_ROADMAP_V1_RESEARCH_LIVE_BETA.md` (Eintrag zu Phase 76)
* `docs/PHASE_76_R_AND_D_EXPERIMENTS_OVERVIEW_V1_1.md`

### Web / API

* `src/webui/r_and_d_api.py`
* `src/webui/app.py`
* `templates/peak_trade_dashboard/r_and_d_experiments.html`

### Tests

* `tests/test_r_and_d_api.py`

---

## 6. Nutzen für das Gesamtsystem

* **R&D wird „first-class citizen" im Web-Dashboard** – keine reine CLI-/Logfile-Perspektive mehr
* **Schnelle Daily-Checks** für Research-Lead / Operator ohne Code-Kontext
* **Klare Trennung** zwischen produktiven und experimentellen Runs via `tier` & `run_type`
* **Basis für weitere R&D-Wellen** (z.B. Armstrong-, El-Karoui-, Ehlers-, Lopez-de-Prado-Stacks), die direkt im Hub sichtbar werden

---

**Built for Research – R&D Experiments Hub v1.1**
