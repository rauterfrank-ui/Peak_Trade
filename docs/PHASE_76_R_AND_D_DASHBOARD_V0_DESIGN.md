# Phase 76 – R&D Dashboard v0 (Design & Spezifikation)

**Status:** 📋 Design-Phase
**Abhängigkeiten:** Phase 75 (R&D-Wave v2 Experiments, Operator-View)
**Zieldatum:** TBD

---

## 1. Kontext & Zielsetzung

Phase 76 liefert ein erstes **R&D Dashboard v0**, das auf den bestehenden
R&D-Bausteinen aufsetzt:

- Strategy-Profiling via `scripts/research_cli.py strategy-profile`
- R&D Experiments Viewer CLI `scripts/view_r_and_d_experiments.py`
- Analyse-Template `notebooks/r_and_d_experiment_analysis_template.py`
- Operator-Workflow aus Phase 75 (R&D-Wave v1/v2)

**Ziel von Phase 76:**

- Ein **lesendes Web-Dashboard** (read-only) für R&D-Experimente bereitstellen
- R&D-Operatoren und Researchern eine schnelle visuelle Übersicht über
  R&D-Waves, Presets, Strategien und Kennzahlen geben
- Die bestehende CLI-/Notebook-Logik so kapseln, dass sie "Dashboard-ready" ist

**Scope v0:** Keine Job-Trigger, keine Live-Änderungen – Fokus auf **Read-Only-Views**
(mit klaren Filtern, Tabellen und Basis-Visualisierungen).

---

## 2. Scope v0 – Was das Dashboard können soll

### 2.1 In Scope

- Übersicht aller R&D-Experimente einer oder mehrerer Wellen
- Filterbare Tabellenansicht mit Kernspalten:
  - Timestamp, Tag, Preset, Strategy, Symbol, TF, Trades, Return, Sharpe,
    MaxDD, WinRate, Status
- Detailansicht für einzelne Experimente (inkl. Roh-JSON-View oder
  vorverarbeiteter Detail-Tabelle)
- Aggregations-Views:
  - Kennzahlen pro Preset
  - Kennzahlen pro Strategy
- Einfache Visualisierungen:
  - Sharpe-Verteilung
  - Return-Verteilung nach Preset
  - Scatter-Plot Sharpe vs. Return

### 2.2 Out of Scope (für spätere Phasen)

- Auslösen neuer Experimente aus dem Dashboard
- Editieren von R&D-Configs
- Vollwertiges Parameter-Heatmap- oder Hyperparameter-Tuning-UI
- User-/Role-Management
- Live-Kopplung an Execution-Stack
- Real-Time Updates / WebSocket-Streaming

---

## 3. User Stories & Operator-Flows

### 3.1 R&D-Operator

- **Ziel:** Schnell sehen, welche R&D-Runs einer Welle sinnvoll sind.
- **Flow:**
  1. Wählt R&D-Welle / Preset aus (z.B. Wave v2, Ehlers/Armstrong/Lopez)
  2. Filtert nach Tag-Substring, Strategy, Datum, Trades > 0
  3. Sortiert nach Sharpe, Return oder WinRate
  4. Öffnet 1–3 interessante Runs in der Detailansicht
  5. Nutzt diese Auswahl für weitere Deep-Dives im Notebook

### 3.2 Researcher

- **Ziel:** Verteilung und Struktur der R&D-Ergebnisse verstehen.
- **Flow:**
  1. Lädt eine Preset- oder Strategy-aggregierte View
  2. Analysiert Kennzahlen pro Parameter-Cluster (z.B. Preset-Level)
  3. Nutzt Plots (Sharpe-Verteilung, Return vs. Sharpe) für Hypothesen
  4. Springt bei Bedarf ins Notebook (`r_and_d_experiment_analysis_template.py`)

### 3.3 Product/Stakeholder

- **Ziel:** High-Level Eindruck der R&D-Aktivität und -Qualität bekommen.
- **Flow:**
  1. Öffnet R&D Dashboard Overview
  2. Sieht Anzahl Experimente pro Welle / Preset / Strategy
  3. Grobe Kennzahlen (Median Sharpe, Median Return) auf aggregierter Ebene

---

## 4. Datenquellen & Backend-Schnittstellen

### 4.1 Primäre Datenquelle

- **Verzeichnis:** `reports/r_and_d_experiments/`
- **Format:** JSON-Dateien pro Experiment
- **Struktur:** Konsistent mit dem, was `view_r_and_d_experiments.py` und
  `r_and_d_experiment_analysis_template.py` bereits nutzen.

**Slice 1 (read-only Read-Model):** Defensive JSON-Ladung und Sortier-Helfer für
Listen-Daten liegen in `src/r_and_d/experiments_read_model.py` (keine Schreibpfade,
keine Netzwerk-Calls). Die WebUI-API `GET /api/r_and_d/experiments` in
`src/webui/r_and_d_api.py` nutzt diese Schicht und unterstützt Filter sowie
`sort_by` / `sort_order` wie in §5.2 beschrieben.

### 4.2 Aggregations-Layer

Für das Dashboard v0 gibt es zwei mögliche Ansätze:

**Option A: On-the-fly Aggregation (empfohlen für v0)**

- Backend-Endpoints lesen die JSON-Dateien direkt
- Nutzen intern Funktionen, die analog zu:
  - `load_experiments_from_dir(...)`
  - `to_dataframe(...)`
  - Filter-Logik aus dem Analysis-Template
- **Vorteil:** Keine zusätzliche Persistenz, einfache Implementierung
- **Nachteil:** Potenziell langsamer bei vielen Dateien (>1000)

**Option B: Pre-aggregierter Cache (für spätere Skalierung)**

- Hintergrund-Job aggregiert Daten periodisch
- Speichert Summary in SQLite oder JSON-Cache
- **Vorteil:** Schnellere Responses
- **Nachteil:** Zusätzliche Komplexität, Sync-Aufwand

**Empfehlung v0:** Option A – On-the-fly, da die erwartete Datenmenge
(< 500 Experimente) performant genug sein sollte.

### 4.3 Wiederverwendbare Komponenten

Folgende bestehende Funktionen können als Backend-Basis dienen:

```python
# Aus notebooks/r_and_d_experiment_analysis_template.py
from notebooks.r_and_d_experiment_analysis_template import (
    load_experiments_from_dir,
    to_dataframe,
    apply_filters,
    summary_stats,
    group_by_preset,
    group_by_strategy,
    top_n_by_sharpe,
)
```

---

## 5. API-Design (REST-Endpoints)

### 5.1 Übersicht der geplanten Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/r_and_d/experiments` | GET | Liste aller R&D-Experimente (mit Filtern) |
| `/api/r_and_d/experiments/{experiment_id}` | GET | Detail eines einzelnen Experiments |
| `/api/r_and_d/summary` | GET | Aggregierte Summary-Statistiken |
| `/api/r_and_d/presets` | GET | Aggregation nach Preset |
| `/api/r_and_d/strategies` | GET | Aggregation nach Strategy |
| `/api/r_and_d/stats` | GET | Globale Statistiken (Anzahl, Avg Sharpe, etc.) |

### 5.2 Filter-Parameter

Für `/api/r_and_d/experiments`:

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `preset` | string | Filter nach Preset-ID (exakt) |
| `strategy` | string | Filter nach Strategy-ID (exakt) |
| `tag_substr` | string | Filter nach Substring im Tag |
| `date_from` | string | Filter ab Datum (YYYY-MM-DD) |
| `date_to` | string | Filter bis Datum (YYYY-MM-DD) |
| `with_trades` | bool | Nur Experimente mit Trades > 0 |
| `limit` | int | Maximale Anzahl (default: 100) |
| `sort_by` | string | Sortierfeld (sharpe, return, timestamp) |
| `sort_order` | string | asc / desc |

### 5.3 Response-Formate

**Experiment-Liste:**

```json
{
  "experiments": [
    {
      "filename": "exp_rnd_w2_ehlers_v1_20251208_233254.json",
      "timestamp": "20251208_233254",
      "tag": "exp_rnd_w2_ehlers_v1",
      "preset_id": "ehlers_super_smoother_v1",
      "strategy": "ehlers_cycle_filter",
      "symbol": "BTC/USDT",
      "timeframe": "1h",
      "total_return": 0.15,
      "sharpe": 1.2,
      "max_drawdown": -0.08,
      "total_trades": 42,
      "win_rate": 0.55,
      "status": "ok"
    }
  ],
  "total_count": 42,
  "filtered_count": 42
}
```

**Summary-Stats:**

```json
{
  "total_experiments": 150,
  "unique_presets": 9,
  "unique_strategies": 6,
  "experiments_with_trades": 80,
  "avg_sharpe": 0.85,
  "avg_return": 0.12,
  "median_sharpe": 0.75,
  "median_return": 0.10
}
```

---

## 6. UI-Views & Komponenten

### 6.1 View-Übersicht

| View | Beschreibung | URL-Pfad |
|------|--------------|----------|
| R&D Overview | Globale Stats + Quick-Links | `/r_and_d` |
| Experiments List | Filterbare Tabelle aller Experimente | `/r_and_d/experiments` |
| Experiment Detail | Einzelansicht mit JSON-Dump | `/r_and_d/experiments/{id}` |
| Preset Summary | Aggregation nach Preset | `/r_and_d/presets` |
| Strategy Summary | Aggregation nach Strategy | `/r_and_d/strategies` |
| Charts | Visualisierungen (Sharpe-Dist, Scatter) | `/r_and_d/charts` |

### 6.2 Experiments List View

**Komponenten:**

- **Filter-Bar** (oben):
  - Preset-Dropdown (alle / einzelne Presets)
  - Strategy-Dropdown (alle / einzelne Strategies)
  - Tag-Substring-Textfeld
  - Date-Picker (von/bis)
  - Checkbox "Nur mit Trades"
  - Apply-Button

- **Tabelle** (scrollbar):
  - Spalten: Timestamp, Tag, Preset, Strategy, TF, Trades, Return, Sharpe, Status
  - Sortierbar per Klick auf Spaltenheader
  - Klickbare Zeilen → Detailansicht

- **Pagination** (unten):
  - 25 / 50 / 100 Einträge pro Seite
  - Seitenzahlen

### 6.3 Experiment Detail View

**Komponenten:**

- **Header-Karte:**
  - Tag, Preset, Strategy, Symbol, Timeframe
  - Zeitraum (from_date → to_date)
  - Status-Badge

- **Metriken-Grid:**
  - Return, Sharpe, MaxDD, WinRate, ProfitFactor
  - Trades, Sortino, Calmar

- **JSON-Viewer:**
  - Collapsible Raw-JSON-Ansicht
  - Copy-to-Clipboard Button

- **Navigation:**
  - Zurück zur Liste
  - Link zum Notebook-Template (Hinweis)

### 6.4 Charts View

**Visualisierungen:**

1. **Sharpe-Histogramm**
   - X-Achse: Sharpe-Bins
   - Y-Achse: Anzahl Experimente
   - Optional: Median-Linie

2. **Return by Preset (Boxplot)**
   - X-Achse: Presets
   - Y-Achse: Return-Verteilung

3. **Sharpe vs. Return (Scatter)**
   - X-Achse: Return
   - Y-Achse: Sharpe
   - Farbe: nach Preset
   - Hover: Tag, Strategy

**Chart-Bibliothek:** Chart.js oder Plotly.js (leichtgewichtig, interaktiv)

---

## 7. Architektur & Integration

### 7.1 Einbettung in bestehenden Web-Stack

Das R&D Dashboard wird als neuer Tab/Bereich im bestehenden
Peak_Trade Web-Dashboard (`src/webui/app.py`) integriert:

```
Peak_Trade Web-Dashboard
├── / (Startseite / Live-Track Panel)
├── /session/{id} (Session-Detail)
├── /r_and_d (NEU: R&D Overview)
├── /r_and_d/experiments (NEU: Experiments List)
├── /r_and_d/experiments/{id} (NEU: Experiment Detail)
├── /r_and_d/presets (NEU: Preset Summary)
├── /r_and_d/strategies (NEU: Strategy Summary)
└── /r_and_d/charts (NEU: Charts)
```

### 7.2 Code-Struktur (geplant)

```
src/
└── webui/
    ├── app.py              # FastAPI-Haupt-App (erweitern)
    ├── live_track.py       # Bestehendes Live-Track Panel
    └── r_and_d_dashboard.py  # NEU: R&D Dashboard Backend

templates/
└── peak_trade_dashboard/
    ├── index.html          # Bestehend (Navigation erweitern)
    ├── r_and_d_overview.html     # NEU
    ├── r_and_d_experiments.html  # NEU
    ├── r_and_d_experiment_detail.html  # NEU
    ├── r_and_d_presets.html      # NEU
    └── r_and_d_charts.html       # NEU
```

### 7.3 Abhängigkeiten

**Backend:**

- FastAPI (bereits vorhanden)
- Pydantic (bereits vorhanden)
- pandas (bereits vorhanden)

**Frontend:**

- Jinja2 Templates (bereits vorhanden)
- Chart.js oder Plotly.js (NEU, minimal)
- TailwindCSS oder Bootstrap (bereits teilweise vorhanden)

---

## 8. Implementation Plan

### 8.1 Milestones

| Milestone | Beschreibung | Geschätzt |
|-----------|--------------|-----------|
| M1 | Backend-Service `r_and_d_dashboard.py` mit Basis-Funktionen | 2h |
| M2 | API-Endpoints für Experiments + Summary | 2h |
| M3 | UI: Experiments List View + Filter | 3h |
| M4 | UI: Experiment Detail View | 1h |
| M5 | UI: Preset/Strategy Aggregation Views | 2h |
| M6 | UI: Charts View (Sharpe-Dist, Scatter) | 2h |
| M7 | Tests + Dokumentation | 2h |
| **Total** | | **~14h** |

### 8.2 Definition of Done

- [ ] API-Endpoints liefern korrekte Daten
- [ ] Filter funktionieren wie im CLI (`view_r_and_d_experiments.py`)
- [ ] Tabelle ist sortierbar und paginiert
- [ ] Detailansicht zeigt alle Metriken + JSON
- [ ] Mindestens 2 Charts (Sharpe-Dist, Scatter)
- [ ] Tests für API-Endpoints (mind. 10 Tests)
- [ ] Dokumentation aktualisiert

---

## 9. Abgrenzung zu Live-Track Dashboard

| Aspekt | Live-Track Dashboard (Phase 82/85) | R&D Dashboard (Phase 76) |
|--------|-----------------------------------|--------------------------|
| **Fokus** | Live-/Shadow-/Testnet-Sessions | Offline R&D-Experimente |
| **Datenquelle** | `reports/experiments/live_sessions/` | `reports/r_and_d_experiments/` |
| **Zeitbezug** | Laufende/abgeschlossene Sessions | Historische Backtests |
| **Safety-Relevanz** | Hoch (Live-Monitoring) | Niedrig (Read-Only Research) |
| **Zielgruppe** | Operatoren | Researcher, Quants |

**Integration:**

- Navigation: Separater Tab "R&D" neben "Live-Track"
- Keine Vermischung der Datenquellen
- Konsistentes UI-Design (gleiche Templates/Styles)

---

## 10. Offene Fragen / Entscheidungen

| # | Frage | Optionen | Entscheidung |
|---|-------|----------|--------------|
| 1 | Chart-Bibliothek | Chart.js vs. Plotly.js | TBD |
| 2 | Pagination Backend vs. Frontend | Backend-Paging vs. Alles laden | TBD |
| 3 | Caching-Strategie | Keins (v0) vs. In-Memory | Keins (v0) |
| 4 | Deep-Link zu Notebooks | Direkte Links vs. Hinweis-Text | Hinweis-Text |

---

## 11. Referenzen

- [PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md](PHASE_75_R_AND_D_WAVE_V2_EXPERIMENTS.md) – R&D Experiment-Katalog & Operator-View
- [PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md](PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md) – R&D Preset-Dokumentation
- [PHASE_82_LIVE_TRACK_DASHBOARD.md](PHASE_82_LIVE_TRACK_DASHBOARD.md) – Live-Track Dashboard (Referenz-Architektur)
- [PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md](PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md) – Session Explorer UI-Patterns
- `scripts/view_r_and_d_experiments.py` – CLI-Referenz für Filter-Logik
- `notebooks/r_and_d_experiment_analysis_template.py` – DataFrame-/Aggregations-Logik

---

## 12. Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-12-09 | Initiale Design-Version erstellt |

---

**Built for Research – Read-Only Dashboard v0**
