# Phase 78 – R&D Report-Gallery & Multi-Run Comparison v1

**Status:** ✅ Abgeschlossen  
**Datum:** 2025-12-09  
**Abhängigkeiten:** Phase 76 (R&D Dashboard v0), Phase 77 (Experiment Detail & Report Viewer)

---

## 1. Ziel der Phase

Phase 78 erweitert den R&D-Hub um zwei zentrale Features: eine **Report-Gallery** in der Detail-Ansicht und einen **Multi-Run Comparison View** für den direkten Vergleich mehrerer Experimente. Damit schließt sich die Lücke zwischen Einzelbetrachtung (Phase 77) und systematischer Analyse über mehrere Runs hinweg.

**Kernziele:**

* Report-Gallery im Detail-View für schnellen Zugriff auf alle zugehörigen Reports
* Multi-Run Comparison View zum Vergleich von 2–10 Experimenten
* Batch-API-Endpoint für effiziente Mehrfachabfragen
* Bessere Entscheidungsgrundlage für Researcher und Operatoren
* Betrifft ausschließlich den **Research-/R&D-Layer** – kein Einfluss auf den Live-Order-Flow

---

## 2. Nicht-Ziele (Abgrenzung)

* Automatische Empfehlungen oder Ranking-Algorithmen
* Export-Funktionen (CSV, PDF) für Vergleichsansichten
* Persistierung von Vergleichs-Sets oder Favoriten
* Live-Vergleiche mit laufenden Sessions
* Integration in den Live-Track-Bereich

---

## 3. User Stories

### 3.1 Operator

| # | User Story |
|---|------------|
| O1 | Als Operator möchte ich für einen Run alle Reports in einer übersichtlichen Gallery sehen, um nicht in der Ordnerstruktur suchen zu müssen. |
| O2 | Als Operator möchte ich mehrere Runs direkt in der Übersicht markieren und vergleichen können, um schnell die besten Kandidaten zu identifizieren. |
| O3 | Als Operator möchte ich auf einen Blick sehen, welcher Run die beste Sharpe Ratio hat, um fundierte Entscheidungen zu treffen. |

### 3.2 Researcher

| # | User Story |
|---|------------|
| R1 | Als Researcher möchte ich 2–4 Experimente hinsichtlich Sharpe, MaxDD, Trades und Status direkt im Browser vergleichen können. |
| R2 | Als Researcher möchte ich in der Vergleichsansicht die besten Werte pro Metrik hervorgehoben sehen, um Muster schneller zu erkennen. |

---

## 4. Scope & Deliverables

### 4.1 Report-Gallery

**Integration in bestehendes Template:**

* Erweiterung von `templates/peak_trade_dashboard/r_and_d_experiment_detail.html`
* Nutzung des Feldes `report_links` der R&D API v1.2 (Phase 77)

**Darstellung:**

* Gallery-Layout mit Cards oder kompakter Liste
* Pro Report-Eintrag:
  * Typ-Badge (HTML / MD / PNG / JSON)
  * Dateiname oder aussagekräftiger Label
  * „Öffnen"-Button (neuer Tab)
* Gruppierung nach Report-Typ (optional)
* Fallback-Hinweis, wenn `report_links` leer ist

### 4.2 Multi-Run Comparison

**Erweiterung der Übersicht `/r_and_d`:**

* Auswahlmechanismus (Checkbox pro Zeile)
* Counter: „X von max. 10 ausgewählt"
* Button: „Vergleiche ausgewählte Runs" (aktiviert ab 2 Auswahlen)

**Neuer View `/r_and_d/comparison?run_ids=...`:**

* Vergleichstabelle mit Kernmetriken:
  * Run-ID / Tag
  * Preset
  * Strategy
  * Symbol / Timeframe
  * Total Return
  * Sharpe Ratio
  * Max Drawdown
  * Total Trades
  * Win Rate
  * Profit Factor
  * Status
* Hervorhebung bester Werte pro Spalte (CSS-Klasse `best-metric`)
* Hervorhebung schlechtester Werte (optional, CSS-Klasse `worst-metric`)
* Link zur Einzelansicht pro Run

### 4.3 API-Erweiterung

**Neuer Endpoint:**

```
GET /api/r_and_d/experiments/batch?run_ids=id1,id2,id3
```

**Spezifikation:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `run_ids` | string | Komma-separierte Liste von Run-IDs |

**Constraints:**

* Maximal 10 IDs pro Request
* Mindestens 2 IDs erforderlich
* Ungültige IDs werden übersprungen (mit Warnung im Response)

**Response:**

```json
{
  "experiments": [
    {
      "run_id": "exp_rnd_w2_ehlers_v1_20241208_233107",
      "experiment": {...},
      "results": {...},
      "meta": {...},
      "report_links": [...],
      "status": "success",
      "duration_info": {...}
    }
  ],
  "requested_ids": ["id1", "id2", "id3"],
  "found_ids": ["id1", "id2"],
  "not_found_ids": ["id3"],
  "total_requested": 3,
  "total_found": 2
}
```

**Fehlerverhalten:**

| Szenario | HTTP-Status | Beschreibung |
|----------|-------------|--------------|
| Keine `run_ids` angegeben | 400 | Bad Request |
| Weniger als 2 IDs | 400 | Bad Request |
| Mehr als 10 IDs | 400 | Bad Request |
| Keine gültigen Runs gefunden | 404 | Not Found |
| Teilweise gültig | 200 | Response mit `not_found_ids` |

### 4.4 Tests

**Neue Tests für API:**

* `TestBatchEndpoint`: Batch-Endpoint Grundfunktionalität
* `TestBatchEndpointValidation`: Validierung (min/max IDs, Format)
* `TestBatchEndpointPartialMatch`: Verhalten bei teilweise ungültigen IDs
* `TestBatchEndpointNotFound`: 404 bei komplett ungültigen IDs

**Neue Tests für Web-Views:**

* `TestComparisonRoute`: HTML Comparison-View Route
* `TestComparisonRouteValidation`: Validierung der URL-Parameter
* `TestReportGalleryRendering`: Report-Gallery im Detail-View

---

## 5. Technische Skizze

### 5.1 Betroffene Module

| Modul | Änderung |
|-------|----------|
| `src/webui/r_and_d_api.py` | Neuer Batch-Endpoint |
| `src/webui/app.py` | Neue Route `/r_and_d/comparison` |
| `templates/.../r_and_d_experiments.html` | Checkbox-Auswahl, Vergleichs-Button |
| `templates/.../r_and_d_experiment_detail.html` | Report-Gallery-Section |
| `templates/.../r_and_d_experiment_comparison.html` | **NEU**: Comparison-View |

### 5.2 Batch-Endpoint Implementierung

```python
# src/webui/r_and_d_api.py

@router.get("/api/r_and_d/experiments/batch")
async def get_experiments_batch(run_ids: str = Query(...)):
    """
    Batch-Abfrage für mehrere Experimente.
    
    Args:
        run_ids: Komma-separierte Liste von Run-IDs (2-10 IDs)
    
    Returns:
        BatchExperimentsResponse mit allen gefundenen Experimenten
    """
    ids = [id.strip() for id in run_ids.split(",") if id.strip()]
    
    if len(ids) < 2:
        raise HTTPException(400, "Mindestens 2 Run-IDs erforderlich")
    if len(ids) > 10:
        raise HTTPException(400, "Maximal 10 Run-IDs erlaubt")
    
    # Reuse Detail-Serialisierung aus Phase 77
    experiments = []
    not_found = []
    
    for run_id in ids:
        exp = find_experiment_by_id(run_id)
        if exp:
            experiments.append(serialize_experiment_detail(exp))
        else:
            not_found.append(run_id)
    
    if not experiments:
        raise HTTPException(404, "Keine gültigen Experimente gefunden")
    
    return {
        "experiments": experiments,
        "requested_ids": ids,
        "found_ids": [e["run_id"] for e in experiments],
        "not_found_ids": not_found,
        "total_requested": len(ids),
        "total_found": len(experiments)
    }
```

### 5.3 Frontend-Logik (Auswahl)

```javascript
// In r_and_d_experiments.html

let selectedRuns = new Set();
const MAX_SELECTION = 10;

function toggleRunSelection(runId, checkbox) {
    if (checkbox.checked) {
        if (selectedRuns.size >= MAX_SELECTION) {
            checkbox.checked = false;
            alert(`Maximal ${MAX_SELECTION} Runs auswählbar`);
            return;
        }
        selectedRuns.add(runId);
    } else {
        selectedRuns.delete(runId);
    }
    updateCompareButton();
}

function updateCompareButton() {
    const btn = document.getElementById('compare-btn');
    const count = selectedRuns.size;
    btn.disabled = count < 2;
    btn.textContent = `Vergleiche (${count}/${MAX_SELECTION})`;
}

function openComparison() {
    const ids = Array.from(selectedRuns).join(',');
    window.location.href = `/r_and_d/comparison?run_ids=${ids}`;
}
```

### 5.4 Comparison-Template Struktur

```html
<!-- r_and_d_experiment_comparison.html -->

{% extends "peak_trade_dashboard/base.html" %}

{% block content %}
<div class="comparison-header">
    <h1>R&D Experiment Vergleich</h1>
    <p>{{ experiments | length }} Experimente im Vergleich</p>
</div>

<table class="comparison-table">
    <thead>
        <tr>
            <th>Metrik</th>
            {% for exp in experiments %}
            <th>
                <a href="/r_and_d/experiment/{{ exp.run_id }}">
                    {{ exp.run_id | truncate(25) }}
                </a>
            </th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Preset</td>
            {% for exp in experiments %}
            <td>{{ exp.meta.preset_id }}</td>
            {% endfor %}
        </tr>
        <!-- Weitere Metriken -->
        <tr>
            <td>Sharpe Ratio</td>
            {% for exp in experiments %}
            <td class="{{ 'best-metric' if exp.results.sharpe == best_sharpe }}">
                {{ exp.results.sharpe | round(2) }}
            </td>
            {% endfor %}
        </tr>
        <!-- ... -->
    </tbody>
</table>
{% endblock %}
```

---

## 5.5 Helper-Refactoring (Phase 78 v1.1)

Die R&D-API wurde um ein zentralisiertes Helper-Set erweitert, das konsistentes Verhalten zwischen JSON-API und HTML-Views garantiert:

* **`find_experiment_by_run_id()`** – Zentraler Lookup mit striktem exaktem Matching (Run-ID, Filename oder Timestamp). Substring-Matches wurden bewusst entfernt, um unerwartete Treffer zu vermeiden.

* **`build_experiment_detail()`** – Einheitlicher Payload-Builder, der raw JSON mit berechneten Feldern (Status, Run-Type, Report-Links) kombiniert. Wird von `/api/r_and_d/experiments/{run_id}`, `/api/r_and_d/experiments/batch` und der HTML-Detail-Route verwendet.

* **`compute_best_metrics()`** – Berechnet die besten Werte pro Metrik für Comparison-Highlighting (Return, Sharpe, Drawdown, Win-Rate, Profit-Factor, Trades). Sonderlogik für Drawdown: der Wert nächste zu 0 „gewinnt".

* **`parse_and_validate_run_ids()`** – Parst, dedupliziert und validiert Komma-separierte Run-IDs. Standard-Limits sind konfigurierbar (z.B. 2–10 IDs pro Batch-Request). Validierungsfehler werden als `ValueError` geworfen und in den Endpoints in `HTTPException(400, ...)` übersetzt.

**Neue Modelle:**

* **`RnDBatchResponse`** – Batch-Antwort mit transparenter Trennung in `found` und `not_found`.
* **`BestMetricsDict`** (TypedDict) – explizite Typisierung für das Ergebnis von `compute_best_metrics()`, optional nach Metrik befüllt.

---

## 6. Testing & Akzeptanzkriterien

### 6.1 Akzeptanzkriterien

| # | Kriterium | Status |
|---|-----------|--------|
| A1 | API-Tests für Batch-Endpoint grün | ✅ |
| A2 | Multi-Run Comparison View rendert für 2–4 valide Runs mit allen Kernmetriken | ✅ |
| A3 | Report-Gallery wird angezeigt, wenn `report_links` nicht leer ist | ✅ (Phase 77) |
| A4 | Best-Metric-Hervorhebung funktioniert korrekt für alle numerischen Spalten | ✅ |
| A5 | Fehlerbehandlung bei ungültigen/fehlenden Run-IDs funktioniert | ✅ |
| A6 | Checkbox-Auswahl in Übersicht limitiert auf 4 Runs | ✅ |
| A7 | Gesamtsuite weiterhin grün (bestehende Tests nicht gebrochen) | ✅ |

### 6.2 Test-Abdeckung

| Test-Datei | Neue Tests | Beschreibung |
|------------|------------|--------------|
| `tests/test_r_and_d_api.py` | ~15 | Batch-Endpoint Tests |
| `tests/test_webui.py` | ~5 | Comparison-Route Tests |

---

## 7. Verwandte Dokumente

* [`docs/PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md`](PHASE_76_R_AND_D_DASHBOARD_V0_DESIGN.md) – R&D Dashboard Design & API-Grundlagen
* [`docs/PHASE_77_R_AND_D_EXPERIMENT_DETAIL_VIEWER.md`](PHASE_77_R_AND_D_EXPERIMENT_DETAIL_VIEWER.md) – Detail-View & Report-Links (Basis für Phase 78)
* [`docs/R_AND_D_OPERATOR_FLOW.md`](R_AND_D_OPERATOR_FLOW.md) – Operator-Workflow-Dokumentation
* [`docs/PEAK_TRADE_STATUS_OVERVIEW.md`](PEAK_TRADE_STATUS_OVERVIEW.md) – Status-Übersicht (Abschnitt Phase 76/77/78)
* [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md) – Gesamtübersicht Peak Trade v1

---

## 8. Änderungshistorie

| Datum | Version | Kommentar |
|-------|---------|-----------|
| 2025-12-09 | v0.1 | Initiales Phase-78-Designdokument erstellt |
| 2025-12-09 | v1.0 | Implementierung abgeschlossen: Batch-API, Comparison-View, Checkbox-Auswahl, Tests |
| 2025-12-09 | v1.1 | Helper-Refactoring: Framework-agnostische Validierung (ValueError), BestMetricsDict TypedDict, Architekturnote |

---

**Built for Research – R&D Report-Gallery & Multi-Run Comparison v1**
