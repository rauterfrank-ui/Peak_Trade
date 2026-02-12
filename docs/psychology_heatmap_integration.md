# Psychology Heatmap Integration

## Übersicht

Die **Psychologie-Heatmap** ist ein Tool zur Visualisierung psychologischer Muster im Trigger-Training. Sie hilft Tradern, ihre typischen emotionalen Trigger zu identifizieren und gezielt daran zu arbeiten.

### Features

- 🎯 **5 Kern-Metriken**: FOMO, Verlustangst, Impulsivität, Zögern, Regelbruch
- 📊 **Cluster-basiert**: Verschiedene Trading-Situationen (Trend-Folge, Breakouts, Exits, etc.)
- 🎨 **Visuell intuitiv**: 4-Stufen Heat-Level (0=kein Thema, 3=starkes Thema)
- 📈 **Statistiken**: Aggregierte Metriken und Problem-Cluster-Erkennung
- 🔄 **Flexibel**: Standalone-Reports oder Integration in bestehende Dashboards

---

## Architektur

### Backend-Modul

**Datei**: `src/reporting/psychology_heatmap.py`

#### Kernfunktionen

```python
# 1. Rows bauen
rows = build_psychology_heatmap_rows(raw_data)

# 2. Für Template serialisieren
serialized = serialize_psychology_heatmap_rows(rows)

# 3. Statistiken berechnen
stats = calculate_cluster_statistics(rows)
```

#### Datenstrukturen

```python
# Input: Roh-Daten
raw_data = [
    {
        "name": "Trend-Folge Einstiege",
        "fomo": 2.0,           # Score 0-3+
        "loss_fear": 1.0,
        "impulsivity": 1.0,
        "hesitation": 0.0,
        "rule_break": 1.0,
    },
    # ... weitere Cluster
]

# Output: Serialisierte Rows für Template
serialized = [
    {
        "name": "Trend-Folge Einstiege",
        "fomo": {
            "value": 2.0,
            "heat_level": 2,          # 0, 1, 2, oder 3
            "display_value": "2",
            "css_class": "heat-2",
        },
        # ... weitere Metriken
    },
]
```

### Frontend-Templates

**Dateien**:
- `templates/peak_trade_dashboard/psychology_heatmap_macro.html` - Wiederverwendbare Macros
- `templates/peak_trade_dashboard/trigger_training_psychology.html` - Vollständige Seite

#### Verwendung der Macros

```jinja
{% from 'psychology_heatmap_macro.html' import psychology_heatmap %}

{# Vollständige Heatmap mit Legende und Hinweisen #}
{{ psychology_heatmap(heatmap_rows, show_legend=True, show_notes=True) }}

{# Oder kompakte Version für Dashboard #}
{% from 'psychology_heatmap_macro.html' import psychology_heatmap_compact %}
{{ psychology_heatmap_compact(heatmap_rows) }}
```

---

## Integration

### 1. In bestehenden Trigger-Training-Report integrieren

```python
from src.reporting.psychology_heatmap import (
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
    calculate_cluster_statistics,
)

def build_trigger_training_report(stats):
    """Erweitere bestehenden Report mit Psychologie-Heatmap."""

    # Scores aus deinen Stats extrahieren
    psychology_raw_rows = [
        {
            "name": "Trend-Folge Einstiege",
            "fomo": stats.trend_fomo_score,
            "loss_fear": stats.trend_loss_fear_score,
            "impulsivity": stats.trend_impulsivity_score,
            "hesitation": stats.trend_hesitation_score,
            "rule_break": stats.trend_rule_break_score,
        },
        # ... weitere Cluster
    ]

    # Rows bauen und serialisieren
    rows = build_psychology_heatmap_rows(psychology_raw_rows)
    heatmap_ctx = serialize_psychology_heatmap_rows(rows)

    # Statistiken berechnen (optional)
    stats_ctx = calculate_cluster_statistics(rows)

    return {
        # ... dein bisheriger Context
        "psychology_heatmap_rows": heatmap_ctx,
        "psychology_statistics": stats_ctx,
    }
```

### 2. Flask/Dashboard Route hinzufügen

```python
from flask import render_template
from src.reporting.psychology_heatmap import (
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
    calculate_cluster_statistics,
)

@app.route("/trigger_training/psychology")
def trigger_training_psychology():
    """Zeigt die vollständige Psychologie-Analyse."""

    # 1. Daten aus DB / Stats laden
    raw_data = load_psychology_data_from_db()

    # 2. Processing
    rows = build_psychology_heatmap_rows(raw_data)
    serialized_rows = serialize_psychology_heatmap_rows(rows)
    stats = calculate_cluster_statistics(rows)

    # 3. Meta-Informationen
    meta = {
        "from_date": "2025-01-01",
        "to_date": "2025-12-10",
        "total_sessions": 42,
        "total_events": 1337,
    }

    # 4. Render Template
    return render_template(
        "trigger_training_psychology.html",
        heatmap_rows=serialized_rows,
        statistics=stats,
        meta=meta,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
```

### 3. In Session-Detail-View einbetten

```jinja
{# In templates/peak_trade_dashboard/session_detail.html #}

{% from 'psychology_heatmap_macro.html' import psychology_heatmap_compact %}

<!-- ... bestehender Content ... -->

<!-- Psychologie-Kompakt-Ansicht hinzufügen -->
{% if session.psychology_data %}
<section class="mb-6">
  {{ psychology_heatmap_compact(session.psychology_data) }}
</section>
{% endif %}
```

---

## Heat-Level Mapping

Die Scores werden auf diskrete Heat-Levels gemappt:

| Score-Bereich | Heat-Level | Farbe | Bedeutung |
|---------------|------------|-------|-----------|
| 0.0 - 0.4     | 0          | Grau (Slate) | Kein Thema |
| 0.5 - 1.4     | 1          | Blau | Leicht |
| 1.5 - 2.4     | 2          | Amber | Mittel |
| 2.5+          | 3          | Rot | Stark |

### CSS-Klassen

- `heat-0`: Grauer Hintergrund (kein Thema)
- `heat-1`: Blauer Gradient (leicht)
- `heat-2`: Amber/Orange Gradient (mittel)
- `heat-3`: Roter Gradient (stark)

---

## Cluster-Definitionen

Die Standard-Cluster sind:

1. **Trend-Folge Einstiege** - Trading mit dem Trend
2. **Counter-Trend Einstiege** - Trading gegen den Trend
3. **Breakout / Breakdowns** - Trading bei Ausbrüchen
4. **Take-Profit / Exits** - Profit-Mitnahmen und Exits
5. **Re-Entries / Scaling** - Wiedereinstiege und Position-Scaling

Du kannst die Cluster nach Bedarf anpassen:

```python
custom_clusters = [
    {
        "name": "Opening Range Breakouts",
        "fomo": 2.5,
        "loss_fear": 1.0,
        # ...
    },
    {
        "name": "News-Trading",
        "fomo": 3.0,
        "impulsivity": 2.5,
        # ...
    },
]
```

---

## Statistiken

Die `calculate_cluster_statistics()` Funktion berechnet:

### Total Clusters
Anzahl der analysierten Cluster.

### Average Scores
Durchschnittswerte für jede Metrik über alle Cluster hinweg.

```python
stats["avg_scores"] = {
    "fomo": 2.0,
    "loss_fear": 1.5,
    "impulsivity": 1.8,
    "hesitation": 1.2,
    "rule_break": 1.6,
}
```

### Max Scores
Maximalwerte für jede Metrik.

### Problem Clusters
Liste von Clustern mit mindestens einem Score >= 2.5:

```python
stats["problem_clusters"] = [
    {"name": "Breakout / Breakdowns", "max_score": 3.0},
    {"name": "Re-Entries / Scaling", "max_score": 3.0},
]
```

---

## Score-Berechnung

### Aus Trigger-Training-Events

Die Funktion `extract_psychology_scores_from_events()` bietet eine Basis-Implementation
zur Berechnung von Scores aus Events:

```python
from src.reporting.psychology_heatmap import extract_psychology_scores_from_events
from src.reporting.trigger_training_report import TriggerTrainingEvent

# Events laden
events: List[TriggerTrainingEvent] = load_events_from_db()

# Scores extrahieren
scores = extract_psychology_scores_from_events(events)

# scores = {
#     "trend_follow": {"fomo": 2.0, "loss_fear": 1.0, ...},
#     "breakout": {"fomo": 3.0, "loss_fear": 2.0, ...},
#     ...
# }
```

### Custom Score-Berechnung

Du kannst auch eigene Logik implementieren:

```python
def calculate_custom_scores(events):
    """Custom Score-Berechnung basierend auf deinen Kriterien."""
    scores = defaultdict(lambda: {
        "fomo": 0.0,
        "loss_fear": 0.0,
        "impulsivity": 0.0,
        "hesitation": 0.0,
        "rule_break": 0.0,
    })

    for event in events:
        cluster = determine_cluster(event)

        # FOMO: Trade nach starker Bewegung ohne Setup
        if event.outcome == "FOMO":
            scores[cluster]["fomo"] += 0.5

        # Impulsivität: Sehr schnelle Reaktion
        if event.reaction_delay_s < 1.0:
            scores[cluster]["impulsivity"] += 0.2

        # Zögern: Signal verpasst
        if event.outcome == "MISSED":
            scores[cluster]["hesitation"] += 0.5

        # ... weitere Logik

    return scores
```

---

## Testing

### Unit-Tests

```bash
python3 -m pytest tests/test_psychology_heatmap.py -v
```

Die Tests decken ab:
- Score-zu-Heat-Level-Konvertierung
- Cell-Erstellung
- Row-Building
- Serialisierung
- Statistik-Berechnung
- Vollständige Integration

### Beispiel-Script

```bash
python3 scripts/example_psychology_heatmap_integration.py
```

Das Script zeigt:
1. Standalone-Report-Generierung
2. Integration in bestehenden Report
3. Flask-Route-Implementierung
4. Vollständigen Workflow

---

## Best Practices

### 1. Score-Berechnung

- **Konsistenz**: Verwende einheitliche Kriterien über alle Sessions hinweg
- **Normalisierung**: Stelle sicher, dass Scores im Bereich 0-3 liegen
- **Transparenz**: Dokumentiere, wie Scores berechnet werden

### 2. Cluster-Definition

- **Relevanz**: Definiere Cluster, die für deine Trading-Strategie relevant sind
- **Granularität**: Nicht zu viele Cluster (5-8 optimal), nicht zu wenige
- **Konsistenz**: Cluster sollten sich nicht überlappen

### 3. Interpretation

- **Kontext**: Berücksichtige Marktbedingungen und Trading-Phasen
- **Trends**: Beobachte Entwicklung über Zeit (monatliche Reviews)
- **Fokus**: Arbeite an max. 2-3 Problem-Clustern gleichzeitig

### 4. Drill-Integration

- **Gezielt**: Nutze Problem-Cluster für fokussiertes Training
- **Messbar**: Tracke Verbesserung über Zeit
- **Realistisch**: Ziel ist Bewusstsein, nicht Perfektion (alle Scores auf 0)

---

## Troubleshooting

### Problem: Alle Scores sind 0

**Ursachen**:
- Keine Events vorhanden
- Score-Berechnung liefert keine Werte
- Events haben keine Tags/Outcomes

**Lösung**:
```python
# Debug-Output
print(f"Events: {len(events)}")
print(f"Scores: {scores}")

# Oder: Verwende Beispiel-Daten zum Testen
from src.reporting.psychology_heatmap import build_example_psychology_heatmap_data
raw_data = build_example_psychology_heatmap_data()
```

### Problem: Template rendert nicht korrekt

**Ursachen**:
- Context-Struktur stimmt nicht
- Template-Pfad falsch
- Jinja2-Syntax-Fehler

**Lösung**:
```python
# Context validieren
print(context.keys())
print(type(context["heatmap_rows"]))
print(context["heatmap_rows"][0] if context["heatmap_rows"] else "empty")

# Template-Pfad prüfen
print(app.template_folder)
```

### Problem: Statistiken zeigen falsche Werte

**Ursachen**:
- Scores nicht im erwarteten Bereich
- Aggregations-Logik fehlerhaft

**Lösung**:
```python
# Scores vor Aggregation prüfen
for row in raw_data:
    for metric in ["fomo", "loss_fear", "impulsivity", "hesitation", "rule_break"]:
        assert 0.0 <= row[metric] <= 3.0, f"Score out of range: {metric}={row[metric]}"
```

---

## Roadmap / Erweiterungen

### Geplante Features

- [ ] **Zeitliche Trends**: Verlauf der Scores über Zeit visualisieren
- [ ] **Vergleichsmodus**: Mehrere Perioden nebeneinander vergleichen
- [ ] **Auto-Drill-Empfehlungen**: KI-basierte Drill-Vorschläge
- [ ] **Export**: PDF/PNG-Export für Offline-Reviews
- [ ] **Mobile-Optimierung**: Responsive Design verbessern
- [ ] **Interaktive Heatmap**: Hover-Details, Click-to-Drill

### Mögliche Erweiterungen

```python
# Zeitliche Trends
def calculate_trend_over_time(events, window_days=7):
    """Berechne Scores in gleitenden Zeitfenstern."""
    pass

# Vergleichsmodus
def compare_periods(period_a_data, period_b_data):
    """Vergleiche zwei Zeiträume."""
    pass

# Auto-Drill-Empfehlungen
def recommend_drills(problem_clusters, past_effectiveness):
    """Empfehle Drills basierend auf Problem-Clustern und bisheriger Effektivität."""
    pass
```

---

## Support

Bei Fragen oder Problemen:

1. **Dokumentation**: Lies diese Dokumentation vollständig
2. **Beispiele**: Schau dir `scripts/example_psychology_heatmap_integration.py` an
3. **Tests**: Führe die Unit-Tests aus
4. **Code**: Lies den gut kommentierten Source-Code in `src/reporting/psychology_heatmap.py`

---

## Lizenz & Autor

Teil des **Peak_Trade** Systems.

**Version**: 1.0  
**Datum**: Dezember 2025  
**Status**: Production-Ready

---

## Quick Reference

### Minimal-Beispiel

```python
# Import
from src.reporting.psychology_heatmap import (
    build_psychology_heatmap_rows,
    serialize_psychology_heatmap_rows,
)

# Daten
raw_data = [
    {
        "name": "Mein Cluster",
        "fomo": 2.0,
        "loss_fear": 1.0,
        "impulsivity": 1.5,
        "hesitation": 0.5,
        "rule_break": 1.0,
    }
]

# Processing
rows = build_psychology_heatmap_rows(raw_data)
serialized = serialize_psychology_heatmap_rows(rows)

# Template
# {{ psychology_heatmap(serialized) }}
```

### Template-Integration

```jinja
{% from 'psychology_heatmap_macro.html' import psychology_heatmap %}

<section>
  <h1>Psychologie-Analyse</h1>
  {{ psychology_heatmap(heatmap_rows) }}
</section>
```

### Flask-Route

```python
@app.route("/psychology")
def psychology():
    data = load_data()
    rows = build_psychology_heatmap_rows(data)
    serialized = serialize_psychology_heatmap_rows(rows)
    return render_template("psychology.html", heatmap_rows=serialized)
```

---

**Ende der Dokumentation**
