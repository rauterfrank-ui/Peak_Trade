# Phase 77 – R&D Experiment Detail & Report Viewer v1

**Status:** ✅ Abgeschlossen  
**Commit:** `feat(phase77): R&D Experiment Detail & Report Viewer v1`

---

## 1. Ziel der Phase

Phase 77 vertieft den in Phase 76 eingeführten R&D-Hub und ermöglicht eine detaillierte Einzelansicht pro Experiment. Forschende und Operatoren können nun Meta-Daten, Status, Laufzeit und Kern-Metriken eines Runs auf einen Blick einsehen – direkt im Web-Dashboard.

**Kernziele:**

* Detail-Ansicht pro Experiment mit allen relevanten Informationen
* Report-Link-Integration für schnellen Zugriff auf HTML/Markdown-Reports und Charts
* Bessere Nachvollziehbarkeit von Experimenten im Research-Track
* Betrifft ausschließlich den **Research-/R&D-Layer** – kein Einfluss auf den Live-Order-Flow

---

## 2. Kern-Deliverables

### R&D Experiment Detail View

* Neue Template-Datei `templates/peak_trade_dashboard/r_and_d_experiment_detail.html`
* Vollständige Meta-Daten-Anzeige (Preset, Strategy, Symbol, Timeframe)
* Timing-Informationen (Timestamp, Zeitraum, Laufzeit)
* Kern-Metriken mit visueller Hervorhebung (Return, Sharpe, MaxDD, Trades, WinRate, Profit Factor)
* Status-/Run-Type-/Tier-Badges
* Collapsible Raw JSON-Ansicht

### Report-Link-Integration

* Automatische Erkennung zugehöriger Report-Dateien:
  * HTML-Reports (`*_report.html`)
  * Markdown-Reports (`*_report.md`, `*.md`)
  * Stats-JSON (`*_stats.json`)
  * Equity-Charts (`*_equity.png`)
  * Drawdown-Charts (`*_drawdown.png`)
* Direkte Links aus dem Dashboard zu den Report-Dateien
* Suche in mehreren Report-Verzeichnissen (`reports/`, `reports/r_and_d_experiments/`, `reports/portfolio/`, `reports/ideas/`)

### API-Erweiterung (v1.2)

* Erweiterter Detail-Endpoint `GET /api/r_and_d/experiments/{run_id}`:
  * `report_links`: Liste erkannter Report-Dateien
  * `status`: Experiment-Status (success, running, failed, no_trades)
  * `run_type`: Typ des Runs (backtest, sweep, monte_carlo, walkforward)
  * `tier`: Strategie-Tier (r_and_d, core, aux, legacy)
  * `experiment_category`: Kategorie (cycles, volatility, ml, microstructure, general)
  * `duration_info`: Laufzeit-Informationen (start_time, end_time, duration_seconds, duration_human)

### Klickbare Übersichts-Tabelle

* Zeilen in der R&D-Übersicht sind nun klickbar
* Detail-Link-Spalte mit Pfeil-Icon (→)
* Direkte Navigation zur Detail-Ansicht

### Tests

* **90 Tests** in `tests/test_r_and_d_api.py` (von 65 auf 90 erweitert)
* Neue Test-Klassen für Phase 77:
  * `TestDetailEndpointV12`: Detail-Endpoint mit erweiterten Feldern
  * `TestFindReportLinks`: Report-Link-Erkennung
  * `TestComputeDurationInfo`: Laufzeit-Berechnung
  * `TestFormatDuration`: Duration-Formatierung
  * `TestHTMLDetailRoute`: HTML Detail-View Route
  * `TestReportLinkTypes`: Report-Link-Typen

---

## 3. Operator- & Research-Workflow

### 1. R&D Hub öffnen

* Aufruf des Web-Dashboards → R&D Hub (`/r_and_d`)

### 2. Experiment auswählen

* Klick auf eine Zeile in der Übersichtstabelle
* Oder Klick auf den Detail-Link (→) in der letzten Spalte

### 3. Detail-Ansicht nutzen

* **Meta-Informationen**: Preset, Strategy, Symbol, Timeframe
* **Timing**: Timestamp, Von/Bis-Datum, Laufzeit
* **Konfiguration**: Tier, Run-Type, Kategorie, Dummy-Daten-Flag
* **Ergebnisse**: Return, Sharpe, MaxDD, Trades, WinRate, Profit Factor

### 4. Reports abrufen

* Klick auf verfügbare Report-Links (HTML-Reports, Charts, Stats)
* Reports öffnen sich in neuem Tab

### 5. Raw JSON inspizieren

* Collapsible-Section für vollständiges Experiment-JSON
* Nützlich für Debugging und detaillierte Analyse

---

## 4. Technische Umsetzung

### Backend / API

* Datei: `src/webui/r_and_d_api.py` (v1.2)
* Neue Funktionen:
  * `find_report_links(run_id, experiment)`: Sucht zugehörige Report-Dateien
  * `compute_duration_info(experiment)`: Berechnet Laufzeit-Informationen
  * `format_duration(seconds)`: Formatiert Sekunden zu menschenlesbarer Form

### App-Integration

* Datei: `src/webui/app.py` (v1.3)
* Neue Route: `GET /r_and_d/experiment/{run_id}`
* 404-Handling mit `error.html` Template

### Frontend / Templates

* `templates/peak_trade_dashboard/r_and_d_experiment_detail.html`: Detail-Ansicht
* `templates/peak_trade_dashboard/r_and_d_experiments.html`: Erweitert mit klickbaren Zeilen
* `templates/peak_trade_dashboard/error.html`: Generische Fehlerseite

---

## 5. Verknüpfte Dateien & Artefakte

### Dokumentation

* `docs/PHASE_77_R_AND_D_EXPERIMENT_DETAIL_VIEWER.md`
* `docs/PHASE_76_R_AND_D_EXPERIMENTS_OVERVIEW_V1_1.md` (Vorgänger)

### Web / API

* `src/webui/r_and_d_api.py` (v1.2)
* `src/webui/app.py` (v1.3)
* `templates/peak_trade_dashboard/r_and_d_experiment_detail.html`
* `templates/peak_trade_dashboard/r_and_d_experiments.html` (v1.2)
* `templates/peak_trade_dashboard/error.html`

### Tests

* `tests/test_r_and_d_api.py` (90 Tests)

---

## 6. API-Referenz

### GET /r_and_d/experiment/{run_id}

HTML Detail-Page für ein einzelnes R&D-Experiment.

**Parameter:**
- `run_id` (path): Run-ID (Dateiname ohne .json oder Timestamp-Substring)

**Response:** HTML-Seite mit Detail-Ansicht

**404:** Wenn Experiment nicht gefunden

### GET /api/r_and_d/experiments/{run_id} (v1.2)

JSON Detail-Endpoint für ein einzelnes Experiment.

**Response (neu in v1.2):**
```json
{
  "filename": "exp_rnd_w2_ehlers_v1_20241208_233107.json",
  "run_id": "exp_rnd_w2_ehlers_v1_20241208_233107",
  "experiment": {...},
  "results": {...},
  "meta": {...},
  "parameters": {...},
  "raw": {...},
  "report_links": [
    {
      "type": "html",
      "label": "📄 HTML Report",
      "path": "reports/...",
      "url": "/static/reports/...",
      "exists": true
    }
  ],
  "status": "success",
  "run_type": "backtest",
  "tier": "r_and_d",
  "experiment_category": "cycles",
  "duration_info": {
    "start_time": "20241208_233107",
    "end_time": "20241208_233507",
    "duration_seconds": 240,
    "duration_human": "4.0m"
  }
}
```

---

## 7. Nutzen für das Gesamtsystem

* **Verbesserte Nachvollziehbarkeit**: Alle Experiment-Details auf einen Blick
* **Schneller Report-Zugriff**: Keine manuelle Suche nach Report-Dateien mehr
* **Integrierter Workflow**: Direkt von Übersicht zu Detail zu Reports
* **Basis für weitere R&D-Features**: z.B. Vergleiche, Batch-Operationen, Export
* **Konsistente UX**: Einheitliches Design wie Live-Track Session Explorer

---

## 8. Highlights

- **Detail-View** mit allen relevanten Run-Informationen (Preset, Strategie, Metriken, Tags)
- **Dedizierte API** für Einzelabfragen (`/experiments/{run_id}`) mit erweiterten Feldern
- **Report-Link-Integration** für schnellen Zugriff auf generierte Analysen
- **Klickbare Tabellen** in der Übersicht für nahtlose Navigation
- **90 Tests** für hohe Code-Qualität
- Betrifft ausschließlich den **Research-/R&D-Layer** – kein Einfluss auf den Live-Order-Flow

---

**Built for Research – R&D Experiment Detail View v1**
