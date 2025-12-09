# Phase 76 – R&D Experiments Overview v1.1

**Status:** ✅ Implementiert  
**Version:** v1.1  
**Abhängigkeiten:** Phase 75 (R&D-Wave v2), Phase 76 v0 (Basis-Dashboard)  
**Datum:** 2025-12-09

---

## 1. Übersicht

Die R&D-Experimente-Übersicht im Web-Dashboard wurde auf **v1.1** gehoben und als zentrale Einstiegsansicht für den Research-Track geschärft.

**Fokus:**
- Klarer Überblick: „Was läuft gerade? Was ist heute fertig geworden?"
- Bessere Lesbarkeit bei vielen Runs (lange Listen, verschiedene Run-Typen)
- Vorbereitung für weitere R&D-Wellen (Ehlers, Armstrong, Lopez de Prado, El Karoui)

---

## 2. Änderungen / Highlights v1.1

### 2.1 Layout & Struktur

- **R&D Hub Header:** Neuer, prominenter Header mit Emoji, Titel und Kurzbeschreibung
- **Daily Summary Kacheln:** Zwei neue Info-Kacheln:
  - "Heute fertig" – Anzahl und Status der heute abgeschlossenen Experimente
  - "Aktuell laufend" – Experimente die noch laufen
- **Kompakteres Tabellenlayout:** 
  - Schmalere Spalten
  - Status und Run-Type als erste Spalten (besserer Scan bei vielen Zeilen)
  - Bessere Truncation bei langen Tags/Presets

### 2.2 Usability & Orientierung

- **Klarere Kopfzeile:** Titel "R&D Experiments Hub" mit Beschreibung
- **Quick-Actions:** Buttons für "Alle", "Mit Trades", "Dashboard"
- **Konsistente Labels:** Gemäß R&D-Taxonomie:
  - Tier: `r_and_d`, `core`, `aux`, `legacy`
  - Run-Types: `backtest`, `sweep`, `monte_carlo`, `walkforward`
  - Kategorien: `cycles`, `volatility`, `ml`, `microstructure`
- **Vereinheitlichte Status-Badges:**
  - 🟢 `success` – Erfolgreich abgeschlossen mit Trades
  - 🔵 `running` – Noch laufend (mit Pulse-Animation)
  - 🔴 `failed` – Fehlgeschlagen
  - ⚪ `no_trades` – Abgeschlossen aber 0 Trades

### 2.3 Neue API-Endpunkte (v1.1)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/r_and_d/today` | GET | Heute fertige Experimente |
| `/api/r_and_d/running` | GET | Aktuell laufende Experimente |
| `/api/r_and_d/categories` | GET | Verfügbare Kategorien mit Counts |

### 2.4 Neue Felder im Experiment-Schema

```json
{
  "run_id": "exp_rnd_w2_ehlers_v1_20251209_...",
  "status": "success",
  "tier": "r_and_d",
  "run_type": "backtest",
  "experiment_category": "cycles",
  "date_str": "2025-12-09"
}
```

### 2.5 Neuer Filter: Run-Type

Im Filter-Formular kann jetzt nach Run-Type gefiltert werden:
- Backtest
- Parameter Sweep
- Monte Carlo
- Walk-Forward

---

## 3. Architektur

### 3.1 Backend-Änderungen

**`src/webui/r_and_d_api.py`:**
- Erweiterte `extract_flat_fields()` mit neuen Feldern
- Erweiterte `determine_status()` für running/failed
- Neue Endpoints: `/today`, `/running`, `/categories`

**`src/webui/app.py`:**
- Erweiterte `/r_and_d` Route mit:
  - Run-Type Filter
  - Daily Summary Stats (today_count, running_count)

### 3.2 Frontend-Änderungen

**`templates/peak_trade_dashboard/r_and_d_experiments.html`:**
- Neuer R&D Hub Header
- Daily Summary Section
- Erweiterte Macros für Status/Run-Type/Category Badges
- Kompakteres Tabellenlayout
- Run-Type Filter im Form

---

## 4. API-Referenz v1.1

### 4.1 GET /api/r_and_d/today

Experimente, die heute abgeschlossen wurden.

**Response:**
```json
{
  "items": [...],
  "count": 5,
  "date": "2025-12-09",
  "success_count": 4,
  "failed_count": 1
}
```

### 4.2 GET /api/r_and_d/running

Aktuell laufende Experimente.

**Response:**
```json
{
  "items": [...],
  "count": 2
}
```

### 4.3 GET /api/r_and_d/categories

Verfügbare Kategorien und Run-Types.

**Response:**
```json
{
  "categories": {
    "cycles": 15,
    "volatility": 8,
    "ml": 5,
    "general": 20
  },
  "run_types": {
    "backtest": 30,
    "sweep": 10,
    "monte_carlo": 5,
    "walkforward": 3
  },
  "category_labels": {...},
  "run_type_labels": {...}
}
```

---

## 5. Status-Badges

| Status | Farbe | Beschreibung |
|--------|-------|--------------|
| `success` | 🟢 Grün | Erfolgreich, Trades > 0 |
| `running` | 🔵 Blau (pulsierend) | Noch laufend |
| `failed` | 🔴 Rot | Fehlgeschlagen |
| `no_trades` | ⚪ Grau | Abgeschlossen, 0 Trades |
| `ok` | 🟢 Grün | Legacy-Status (= success) |

---

## 6. Run-Type Badges

| Run-Type | Badge | Beschreibung |
|----------|-------|--------------|
| `backtest` | `BT` (grau) | Standard-Backtest |
| `sweep` | `Sweep` (lila) | Parameter-Sweep |
| `monte_carlo` | `MC` (amber) | Monte-Carlo-Simulation |
| `walkforward` | `WF` (teal) | Walk-Forward-Analyse |

---

## 7. Kategorie-Mapping

Die Kategorie wird automatisch aus Preset/Strategy abgeleitet:

| Pattern | Kategorie |
|---------|-----------|
| `ehlers_*` | cycles |
| `armstrong_*` | cycles |
| `meta_labeling`, `lopez_*` | ml |
| `el_karoui_*`, `*_vol_*` | volatility |
| Sonstige | general |

---

## 8. Future-Proofing

Das Layout ist so angelegt, dass weitere R&D-Wellen ohne Redesign integriert werden können:

- **Neue Strategien:** Automatische Kategorie-Erkennung
- **Neue Run-Types:** Einfach erweiterbar in den Badge-Macros
- **Detailansicht:** Vorbereitet für späteren Ausbau
- **Charts:** Platzhalter für Sharpe-Verteilung, Scatter-Plots

---

## 9. Nutzung

### Web-Dashboard

```
http://localhost:8000/r_and_d
```

### API-Calls

```bash
# Alle Experimente
curl http://localhost:8000/api/r_and_d/experiments

# Heute fertig
curl http://localhost:8000/api/r_and_d/today

# Laufend
curl http://localhost:8000/api/r_and_d/running

# Mit Filtern
curl "http://localhost:8000/api/r_and_d/experiments?preset=ehlers_super_smoother_v1&with_trades=true"
```

---

## 10. Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2025-12-09 | v0 | Initiale Design-Version |
| 2025-12-09 | v1.1 | Layout-Upgrade, Daily Summary, Status-Badges, Run-Type Filter |

---

**Built for Research – R&D Experiments Hub v1.1**
