# Psychologie-Heuristik-System

**Version:** 1.0  
**Status:** Production-Ready  
**Datum:** Dezember 2025

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Kern-Konzepte](#kern-konzepte)
3. [Architektur](#architektur)
4. [Heuristik-Formeln](#heuristik-formeln)
5. [Verwendung](#verwendung)
6. [Integration](#integration)
7. [Konfiguration](#konfiguration)
8. [Testing](#testing)
9. [Beispiele](#beispiele)
10. [FAQ](#faq)

---

## Übersicht

Das **Psychologie-Heuristik-System** implementiert konkrete Formeln zur Berechnung von Psychologie-Scores (0–3) aus Trigger-Training-Events. Es analysiert **5 Kern-Achsen** des Trading-Verhaltens und erzeugt eine Heatmap zur Visualisierung psychologischer Muster.

### Features

- 🎯 **5 Psychologie-Achsen**: FOMO, Verlustangst, Impulsivität, Zögern, Regelbruch
- 📊 **Cluster-basiert**: Verschiedene Trading-Situationen (Trend-Folge, Breakouts, Exits, etc.)
- 🔢 **Quantitative Formeln**: Klare, nachvollziehbare Score-Berechnung
- 🎨 **Heatmap-Integration**: Direkt kompatibel mit bestehendem Heatmap-System
- ⚙️ **Konfigurierbar**: Alle Schwellenwerte zentral anpassbar
- ✅ **Getestet**: 47 Unit-Tests mit 100% Pass-Rate

---

## Kern-Konzepte

### Die 5 Psychologie-Achsen

#### 1. FOMO (Fear of Missing Out)
**Definition:** Hinterherjagen von bereits gelaufenen Moves

**Indikatoren:**
- Hohe Latenz zwischen Signal und Entry
- Signifikante Preisbewegung vor Entry
- Entry nach starkem Momentum

**Intuition:** "Der Zug fährt ab, ich muss jetzt rein!"

---

#### 2. Verlustangst (Loss Fear)
**Definition:** Zu frühes Exit oder Vermeidung nach Verlusten

**Indikatoren:**
- Früher Exit bei kleinem Adverse-Move
- Großer Unterschied zu idealem Exit-Punkt
- Keine Action nach Verlust-Streak
- Verpasste Setups während Loss-Phase

**Intuition:** "Ich darf keinen weiteren Verlust riskieren!"

---

#### 3. Impulsivität (Impulsivity)
**Definition:** Spontan-Trades ohne Setup oder Regelkonformität

**Indikatoren:**
- Action ohne gültiges Setup
- Extrem schnelle Reaktion (< 0.2 * LATENCY_OK_S)
- Entry ohne vorheriges Signal
- Hyperaktives Trading

**Intuition:** "Ich muss JETZT handeln, sofort!"

---

#### 4. Zögern (Hesitation)
**Definition:** Zu späte oder ausbleibende Action trotz Setup

**Indikatoren:**
- Hohe Latenz trotz gültigem Setup
- NO_ACTION bei klarem Signal
- Verpasste favorable Moves
- Hoher Skip-Streak

**Intuition:** "Ich bin mir nicht sicher, lieber abwarten..."

---

#### 5. Regelbruch (Rule Break)
**Definition:** Bewusstes Ignorieren von System-Regeln

**Indikatoren:**
- Entry gegen Signal-Richtung
- Size-Violations (zu groß)
- Risk-Violations (Stop/Risk verletzt)
- Entry ohne Setup trotz klarer Regeln
- Schlechter PnL durch Regelbruch

**Intuition:** "Die Regeln gelten jetzt nicht, ich weiß es besser!"

---

### Score-System

Alle Scores liegen im Bereich **[0, 3]**:

| Score | Bedeutung | Farbe | Handlungsbedarf |
|-------|-----------|-------|-----------------|
| 0 | Kein Thema | Grau | ✅ Alles gut |
| 1 | Leicht | Blau | 💡 Bewusstsein schaffen |
| 2 | Mittel | Amber | ⚠️ Aufmerksamkeit erforderlich |
| 3 | Stark | Rot | 🚨 Dringender Handlungsbedarf |

---

## Architektur

### Module

```
src/reporting/
├── psychology_heuristics.py       # Kern-Modul (NEU)
│   ├── TriggerTrainingPsychEventFeatures (Dataclass)
│   ├── TriggerTrainingPsychClusterScores (Dataclass)
│   ├── score_fomo()
│   ├── score_loss_fear()
│   ├── score_impulsivity()
│   ├── score_hesitation()
│   ├── score_rule_break()
│   ├── aggregate_cluster_scores()
│   └── compute_psychology_heatmap_from_events()
│
└── psychology_heatmap.py           # Bestehende Heatmap-Infrastruktur
    ├── build_psychology_heatmap_rows()
    ├── serialize_psychology_heatmap_rows()
    └── calculate_cluster_statistics()
```

### Datenfluss

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Rohdaten (DB, CSV, ...)                                      │
│    - Signals, Actions, Timestamps, Prices, ...                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Event-Features erstellen                                     │
│    TriggerTrainingPsychEventFeatures                            │
│    - cluster, event_type, latency_s, price_move_pct, ...       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Event-Level Scoring                                          │
│    score_fomo(ev), score_loss_fear(ev), ...                     │
│    → Scores 0-3 pro Event & Achse                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Cluster-Aggregation                                          │
│    aggregate_cluster_scores(events)                             │
│    → TriggerTrainingPsychClusterScores pro Cluster              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Heatmap-Format                                               │
│    compute_psychology_heatmap_from_events(events)               │
│    → Serialisierte Heatmap-Rows (ready für Template)            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Visualisierung                                               │
│    Jinja2-Template mit psychology_heatmap() Macro               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Heuristik-Formeln

### Konfigurierbare Schwellenwerte

Alle Schwellenwerte sind am Kopf von `psychology_heuristics.py` definiert:

```python
# Zeit-Schwellwerte (Sekunden)
LATENCY_OK_S = 3.0          # <= diese Zeit = "okay"
LATENCY_HESITATION_S = 8.0  # > = starke Zögerlichkeit

# Preisbewegungs-Schwellen (%)
MOVE_SMALL_PCT = 0.10       # 0.10% ~ "kleiner Move"
MOVE_MEDIUM_PCT = 0.30
MOVE_LARGE_PCT = 0.70

# PnL-Schwellwerte (Basis-Punkte)
PNL_SMALL_BP = 5.0
PNL_MEDIUM_BP = 15.0
PNL_LARGE_BP = 30.0

# Streak-Schwellen
LOSS_STREAK_MEDIUM = 2
LOSS_STREAK_HIGH = 4
SKIP_STREAK_MEDIUM = 2
SKIP_STREAK_HIGH = 4
```

### FOMO-Formel

**Primär für:** ENTER-Events

```python
def score_fomo(ev: TriggerTrainingPsychEventFeatures) -> int:
    if ev.event_type != "ENTER":
        base = 0.0
    else:
        # Latenz-Komponente
        late_factor = (ev.latency_s - LATENCY_OK_S) / (LATENCY_HESITATION_S - LATENCY_OK_S)
        late_factor = clamp(late_factor, 0.0, 1.5)

        # Move-Komponente (Stufenfunktion)
        move = abs(ev.price_move_since_signal_pct)
        if move < MOVE_SMALL_PCT:
            move_component = 0.0
        elif move < MOVE_MEDIUM_PCT:
            move_component = 0.8
        elif move < MOVE_LARGE_PCT:
            move_component = 1.5
        else:
            move_component = 2.2

        base = late_factor * 1.5 + move_component

    # Manuelle Markierung
    if ev.manually_marked_fomo:
        base += 1.0

    return clamp_0_3(base)
```

**Beispiele:**

| Latenz | Move | Manual | → Score |
|--------|------|--------|---------|
| 2s | 0.05% | Nein | 0 |
| 5s | 0.4% | Nein | 2 |
| 6s | 0.8% | Ja | 3 |

---

### Loss-Fear-Formel

**Primär für:** EXIT-Events, NO_ACTION nach Verlusten

```python
def score_loss_fear(ev: TriggerTrainingPsychEventFeatures) -> int:
    base = 0.0

    # 1) Zu frühe Exits
    if ev.event_type == "EXIT":
        if ev.price_max_adverse_pct < MOVE_SMALL_PCT and \
           ev.price_max_favorable_pct > MOVE_SMALL_PCT:
            base += 1.0

        if ev.pnl_vs_ideal_bp < -PNL_MEDIUM_BP:
            base += 1.0
        if ev.pnl_vs_ideal_bp < -PNL_LARGE_BP:
            base += 0.5

    # 2) Vermeidung nach Verlusten
    if ev.event_type in ("NO_ACTION", "SKIP") and ev.had_valid_setup:
        if ev.recent_loss_streak >= LOSS_STREAK_MEDIUM:
            base += 1.0
        if ev.recent_loss_streak >= LOSS_STREAK_HIGH:
            base += 0.7

    # 3) Manuelle Markierung
    if ev.manually_marked_fear:
        base += 1.0

    return clamp_0_3(base)
```

**Beispiele:**

| Event | Adverse | Favorable | PnL vs Ideal | Loss Streak | Manual | → Score |
|-------|---------|-----------|--------------|-------------|--------|---------|
| EXIT | 0.08% | 0.4% | -25bp | 0 | Nein | 2 |
| NO_ACTION | - | 0.5% | -40bp | 5 | Ja | 3 |
| EXIT | 0.15% | 0.3% | -5bp | 0 | Nein | 0 |

---

### Impulsivity-Formel

**Primär für:** ENTER/EXIT ohne Setup

```python
def score_impulsivity(ev: TriggerTrainingPsychEventFeatures) -> int:
    base = 0.0

    # 1) Action ohne Setup
    if ev.event_type in ("ENTER", "EXIT") and not ev.had_valid_setup:
        base += 1.5

    # 2) Extrem schnell
    if ev.event_type in ("ENTER", "EXIT"):
        if ev.latency_s < 0.2 * LATENCY_OK_S:
            base += 1.0

    # 3) Entry ohne Signal
    if ev.entered_without_signal:
        base += 1.5

    # 4) Manuelle Markierung
    if ev.manually_marked_impulsive:
        base += 1.0

    return clamp_0_3(base)
```

**Beispiele:**

| Setup | Latenz | Ohne Signal | Manual | → Score |
|-------|--------|-------------|--------|---------|
| Ja | 2.5s | Nein | Nein | 0 |
| Nein | 0.4s | Ja | Nein | 3 |
| Nein | 2.0s | Nein | Ja | 3 |

---

### Hesitation-Formel

**Primär für:** Späte Actions, NO_ACTION

```python
def score_hesitation(ev: TriggerTrainingPsychEventFeatures) -> int:
    base = 0.0

    # 1) Späte Action
    if ev.event_type in ("ENTER", "EXIT") and ev.had_valid_setup:
        if ev.latency_s > LATENCY_OK_S:
            base += 1.0
        if ev.latency_s > LATENCY_HESITATION_S:
            base += 1.0

    # 2) NO_ACTION bei Setup
    if ev.event_type in ("NO_ACTION", "SKIP") and ev.had_valid_setup:
        base += 1.0
        if ev.price_max_favorable_pct > MOVE_MEDIUM_PCT:
            base += 0.5

    # 3) Skip-Streak
    if ev.recent_skip_streak >= SKIP_STREAK_MEDIUM:
        base += 0.5
    if ev.recent_skip_streak >= SKIP_STREAK_HIGH:
        base += 0.5

    return clamp_0_3(base)
```

**Beispiele:**

| Event | Setup | Latenz | Favorable Move | Skip Streak | → Score |
|-------|-------|--------|----------------|-------------|---------|
| ENTER | Ja | 2.0s | - | 0 | 0 |
| ENTER | Ja | 10.0s | - | 0 | 2 |
| NO_ACTION | Ja | 8.0s | 0.6% | 6 | 3 |

---

### Rule-Break-Formel

**Primär für:** Violations jeglicher Art

```python
def score_rule_break(ev: TriggerTrainingPsychEventFeatures) -> int:
    base = 0.0

    # Richtung gegen Signal
    if ev.opposite_to_signal:
        base += 1.5

    # Size/Risk Violations
    if ev.size_violation:
        base += 1.0
    if ev.risk_violation:
        base += 1.0

    # Entry ohne Setup
    if ev.entered_without_signal and not ev.had_valid_setup:
        base += 1.0

    # Teurer Regelbruch
    if ev.pnl_vs_ideal_bp < -PNL_LARGE_BP:
        base += 0.5

    return clamp_0_3(base)
```

**Beispiele:**

| Opposite | Size Violation | Risk Violation | Ohne Setup | → Score |
|----------|----------------|----------------|------------|---------|
| Nein | Nein | Nein | Nein | 0 |
| Ja | Nein | Nein | Nein | 2 |
| Ja | Ja | Ja | Ja | 3 |

---

### Aggregations-Strategie

Pro Cluster werden Event-Scores wie folgt aggregiert:

```python
def aggregate_scores(scores: List[int]) -> int:
    # Durchschnitt aller Scores
    avg_all = sum(scores) / len(scores)

    # Durchschnitt der Top-3 Scores
    if len(scores) >= 3:
        top_3 = sorted(scores, reverse=True)[:3]
        avg_top = sum(top_3) / len(top_3)
        # 50/50 Mix
        combined = 0.5 * avg_all + 0.5 * avg_top
    else:
        combined = avg_all

    return clamp_0_3(combined)
```

**Intuition:** Starke Events (hohe Scores) bekommen mehr Gewicht, aber nicht zu viel (50/50 Mix). Das verhindert, dass einzelne Ausreißer den Cluster-Score dominieren, aber problematische Muster dennoch sichtbar bleiben.

---

## Verwendung

### Minimal-Beispiel

```python
from src.reporting.psychology_heuristics import (
    TriggerTrainingPsychEventFeatures,
    compute_psychology_heatmap_from_events,
)

# 1. Events erstellen
events = [
    TriggerTrainingPsychEventFeatures(
        cluster="Trend-Folge Einstiege",
        event_type="ENTER",
        side="LONG",
        signal_strength=0.8,
        latency_s=5.0,
        latency_window_s=3.0,
        price_move_since_signal_pct=0.4,
        price_max_favorable_pct=0.5,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-20.0,
        had_valid_setup=True,
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=True,
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    ),
    # ... weitere Events
]

# 2. Heatmap-Daten generieren (End-to-End)
heatmap_data = compute_psychology_heatmap_from_events(events)

# 3. In Template verwenden
# render_template("psychology.html", heatmap_rows=heatmap_data)
```

### Detailliertes Beispiel

```python
from src.reporting.psychology_heuristics import (
    TriggerTrainingPsychEventFeatures,
    score_fomo,
    score_loss_fear,
    score_impulsivity,
    score_hesitation,
    score_rule_break,
    aggregate_cluster_scores,
)

# 1. Event erstellen
ev = TriggerTrainingPsychEventFeatures(...)

# 2. Einzelne Scores berechnen (für Debugging)
print(f"FOMO: {score_fomo(ev)}")
print(f"Loss Fear: {score_loss_fear(ev)}")
print(f"Impulsivity: {score_impulsivity(ev)}")
print(f"Hesitation: {score_hesitation(ev)}")
print(f"Rule Break: {score_rule_break(ev)}")

# 3. Cluster-Scores aggregieren
cluster_scores = aggregate_cluster_scores([ev1, ev2, ev3])

# 4. Ergebnis inspizieren
for cs in cluster_scores:
    print(f"Cluster: {cs.cluster}")
    print(f"  FOMO: {cs.fomo}, Loss Fear: {cs.loss_fear}, ...")
```

---

## Integration

### In Trigger-Training-Report

```python
from src.reporting.psychology_heuristics import (
    TriggerTrainingPsychEventFeatures,
    compute_psychology_heatmap_from_events,
)
from src.reporting.trigger_training_report import (
    load_trigger_training_session,
)

def build_trigger_training_report_with_psychology(session_id: str):
    """Erweitert bestehenden Report um Psychologie-Analyse."""

    # 1. Bestehende Session-Daten laden
    session = load_trigger_training_session(session_id)

    # 2. Events in Feature-Format konvertieren
    events = [
        TriggerTrainingPsychEventFeatures(
            cluster=determine_cluster(e),
            event_type=map_event_type(e),
            side=e.side,
            signal_strength=e.signal_strength,
            latency_s=calculate_latency(e),
            latency_window_s=3.0,
            price_move_since_signal_pct=calculate_price_move(e),
            price_max_favorable_pct=e.max_favorable,
            price_max_adverse_pct=e.max_adverse,
            pnl_vs_ideal_bp=e.pnl_vs_ideal,
            had_valid_setup=e.setup_valid,
            entered_without_signal=not e.had_signal,
            opposite_to_signal=check_opposite(e),
            size_violation=e.size > MAX_SIZE,
            risk_violation=e.stop_distance > MAX_RISK,
            recent_loss_streak=calculate_loss_streak(e),
            recent_skip_streak=calculate_skip_streak(e),
            manually_marked_fomo="fomo" in e.tags,
            manually_marked_fear="fear" in e.tags,
            manually_marked_impulsive="impulsive" in e.tags,
        )
        for e in session.events
    ]

    # 3. Psychologie-Heatmap generieren
    psychology_heatmap = compute_psychology_heatmap_from_events(events)

    # 4. In Report-Context einfügen
    return {
        # ... bestehender Context
        "psychology_heatmap_rows": psychology_heatmap,
    }
```

### Flask-Route

```python
from flask import render_template
from src.reporting.psychology_heuristics import (
    compute_psychology_heatmap_from_events,
)

@app.route("/trigger_training/psychology/<session_id>")
def trigger_training_psychology(session_id: str):
    """Standalone Psychologie-Analyse für eine Session."""

    # 1. Events laden und konvertieren
    events = load_and_convert_events(session_id)

    # 2. Heatmap generieren
    heatmap_data = compute_psychology_heatmap_from_events(events)

    # 3. Template rendern
    return render_template(
        "trigger_training_psychology.html",
        heatmap_rows=heatmap_data,
        session_id=session_id,
    )
```

### Template (Jinja2)

```jinja
{% from 'psychology_heatmap_macro.html' import psychology_heatmap %}

<section class="psychology-analysis">
  <h1>Psychologie-Analyse: Session {{ session_id }}</h1>

  {{ psychology_heatmap(heatmap_rows, show_legend=True, show_notes=True) }}

  <div class="actions mt-4">
    <a href="/trigger_training/drills?session={{ session_id }}"
       class="btn btn-primary">
      🎯 Gezieltes Training starten
    </a>
  </div>
</section>
```

---

## Konfiguration

### Schwellenwerte anpassen

**Option 1:** Direkt im Modul (`psychology_heuristics.py`)

```python
# Am Kopf des Moduls
LATENCY_OK_S = 4.0  # statt 3.0 (mehr Zeit als "okay")
MOVE_LARGE_PCT = 0.50  # statt 0.70 (niedrigere Schwelle für "große Moves")
```

**Option 2:** Via Config-File (zukünftig)

```toml
# config/psychology_heuristics.toml
[thresholds]
latency_ok_s = 4.0
latency_hesitation_s = 10.0
move_small_pct = 0.15
move_medium_pct = 0.40
move_large_pct = 0.80

[streaks]
loss_streak_medium = 3
loss_streak_high = 6
```

### Cluster-Mapping anpassen

Implementiere eine eigene `determine_cluster()`-Funktion:

```python
def determine_cluster(event: YourEventType) -> str:
    """Ordnet Event einem Cluster zu basierend auf deinen Kriterien."""

    if event.setup_type == "TREND_FOLLOW":
        return "Trend-Folge Einstiege"
    elif event.setup_type == "BREAKOUT":
        return "Breakout / Breakdowns"
    elif event.is_exit:
        return "Take-Profit / Exits"
    elif event.is_reentry:
        return "Re-Entries / Scaling"
    else:
        return "Sonstige"
```

---

## Testing

### Tests ausführen

```bash
# Alle Tests
pytest tests/reporting/test_psychology_heuristics.py -v

# Nur spezifische Test-Klasse
pytest tests/reporting/test_psychology_heuristics.py::TestScoreFOMO -v

# Mit Coverage
pytest tests/reporting/test_psychology_heuristics.py --cov=src.reporting.psychology_heuristics
```

### Test-Struktur

```
tests/reporting/test_psychology_heuristics.py
├── TestClamp                    # Helper-Funktion Tests
├── TestScoreFOMO                # FOMO-Formel Tests
├── TestScoreLossFear            # Loss-Fear-Formel Tests
├── TestScoreImpulsivity         # Impulsivity-Formel Tests
├── TestScoreHesitation          # Hesitation-Formel Tests
├── TestScoreRuleBreak           # Rule-Break-Formel Tests
├── TestAggregateClusterScores   # Aggregations-Tests
├── TestBuildHeatmapInput        # Format-Konvertierung
├── TestEndToEnd                 # End-to-End Workflow
├── TestExampleEvents            # Beispiel-Events
└── TestEdgeCases                # Edge-Cases & Robustheit
```

### Eigene Tests hinzufügen

```python
def test_custom_scenario():
    """Test für ein spezifisches Szenario."""
    ev = TriggerTrainingPsychEventFeatures(
        # ... dein Szenario
    )

    score = score_fomo(ev)
    assert score == 2, "Expected FOMO score of 2"
```

---

## Beispiele

### Beispiel 1: FOMO-Event

```python
from src.reporting.psychology_heuristics import (
    create_example_fomo_event,
    score_fomo,
)

# Erstelle Beispiel-Event
ev = create_example_fomo_event()

# Berechne Score
score = score_fomo(ev)
print(f"FOMO Score: {score} / 3")

# Charakteristiken:
# - ENTER-Event
# - Latenz: 6s (spät, sollte <= 3s sein)
# - Price Move: 0.8% (groß)
# - Manuell als FOMO markiert
# → Erwartet: Score 3
```

### Beispiel 2: Regelbruch-Event

```python
from src.reporting.psychology_heuristics import (
    create_example_rule_break_event,
    score_rule_break,
)

ev = create_example_rule_break_event()
score = score_rule_break(ev)
print(f"Rule Break Score: {score} / 3")

# Charakteristiken:
# - Entry gegen Signal-Richtung (opposite_to_signal=True)
# - Size-Violation (zu groß)
# - Risk-Violation (Stop/Risk verletzt)
# - Ohne gültiges Setup
# → Erwartet: Score 3
```

### Beispiel 3: Komplette Session

```python
from src.reporting.psychology_heuristics import (
    create_example_mixed_events,
    compute_psychology_heatmap_from_events,
)
from src.reporting.psychology_heatmap import (
    build_psychology_heatmap_rows,
    calculate_cluster_statistics,
)

# 1. Events generieren
events = create_example_mixed_events()
print(f"Anzahl Events: {len(events)}")

# 2. Heatmap-Daten
heatmap_data = compute_psychology_heatmap_from_events(events)
print(f"Anzahl Cluster: {len(heatmap_data)}")

# 3. Statistiken
rows = build_psychology_heatmap_rows([
    {
        "name": row["name"],
        "fomo": row["fomo"]["value"],
        "loss_fear": row["loss_fear"]["value"],
        "impulsivity": row["impulsivity"]["value"],
        "hesitation": row["hesitation"]["value"],
        "rule_break": row["rule_break"]["value"],
    }
    for row in heatmap_data
])
stats = calculate_cluster_statistics(rows)

print("\nStatistiken:")
print(f"  Durchschnittlicher FOMO: {stats['avg_scores']['fomo']:.2f}")
print(f"  Problem-Cluster: {len(stats['problem_clusters'])}")
```

### Beispiel 4: Demo-Script ausführen

```bash
cd /Users/frnkhrz/Peak_Trade
PYTHONPATH=. python3 scripts/example_psychology_heuristics.py
```

Das Script zeigt:
- Event-Level Scoring
- Cluster-Aggregation
- End-to-End Workflow
- JSON-Export
- Flask-Integration

---

## FAQ

### Wie bestimme ich den richtigen Cluster für ein Event?

**Antwort:** Du musst eine `determine_cluster()`-Funktion implementieren, die basierend auf Event-Properties (z.B. `setup_type`, `tags`, `signal_type`) den passenden Cluster-Namen zurückgibt. Siehe [Cluster-Mapping](#cluster-mapping-anpassen).

---

### Kann ich die Formeln anpassen?

**Antwort:** Ja! Die Schwellenwerte sind zentral am Kopf des Moduls definiert. Für tiefere Anpassungen kannst du die Scoring-Funktionen direkt editieren. Achte darauf, die Tests entsprechend anzupassen.

---

### Wie integriere ich manuelle Markierungen?

**Antwort:** Setze die Flags `manually_marked_fomo`, `manually_marked_fear`, `manually_marked_impulsive` beim Erstellen der `TriggerTrainingPsychEventFeatures`. Diese erhöhen die jeweiligen Scores um +1.

---

### Was mache ich, wenn Events keine gültigen Feature-Daten haben?

**Antwort:** Setze fehlende Werte auf sinnvolle Defaults:
- `latency_s`: Berechne aus Timestamps oder setze auf `latency_window_s`
- `price_move_since_signal_pct`: 0.0 wenn unbekannt
- `pnl_vs_ideal_bp`: 0.0 wenn unbekannt
- Flags: `False` als Default

---

### Können Scores > 3 werden?

**Antwort:** Nein. Alle Scoring-Funktionen verwenden `clamp_0_3()`, was Werte auf [0, 3] begrenzt.

---

### Wie teste ich neue Formeln?

**Antwort:**
1. Erstelle Test-Cases in `tests/reporting/test_psychology_heuristics.py`
2. Definiere spezifische Events mit bekannten Inputs
3. Assert erwartete Scores
4. Führe Tests aus: `pytest tests/reporting/test_psychology_heuristics.py::TestYourTest -v`

---

### Kann ich Scores für einzelne Events exportieren (nicht nur Cluster)?

**Antwort:** Ja! Nutze die Scoring-Funktionen direkt:

```python
event_scores = [
    {
        "event_id": ev.event_id,
        "cluster": ev.cluster,
        "fomo": score_fomo(ev),
        "loss_fear": score_loss_fear(ev),
        "impulsivity": score_impulsivity(ev),
        "hesitation": score_hesitation(ev),
        "rule_break": score_rule_break(ev),
    }
    for ev in events
]
```

---

### Wie oft sollte ich die Schwellenwerte neu kalibrieren?

**Antwort:**
- **Initial:** Nach ersten 20-30 Sessions anschauen und ggf. anpassen
- **Danach:** Monatlich oder nach signifikanten Strategie-Änderungen
- **Trigger:** Wenn Scores durchweg zu niedrig/hoch sind (z.B. avg < 0.5 oder avg > 2.5)

---

## Best Practices

### 1. Sinnvolle Event-Features

✅ **Gut:**
- Präzise Latenz-Messungen (ms-genau)
- Akkurate Preisbewegungen (bereinigt um Spread)
- Valide Setup-Erkennung (konsistent mit Regelwerk)

❌ **Schlecht:**
- Geschätzte/gerundete Werte
- Fehlende/inkonsistente Feature-Daten
- Inkorrekte Flag-Setzung

---

### 2. Cluster-Definition

✅ **Gut:**
- 5-8 Cluster (nicht zu viele, nicht zu wenige)
- Klar abgegrenzte Situationen
- Trading-relevant (z.B. "Trend-Folge", "Breakout", "Exit")

❌ **Schlecht:**
- 20+ Cluster (zu granular)
- Überlappende Definitionen
- Irrelevante Cluster

---

### 3. Interpretation

✅ **Gut:**
- Kontext berücksichtigen (Marktphase, Trading-Phase)
- Trends über Zeit beobachten
- Fokus auf max. 2-3 Problem-Cluster gleichzeitig

❌ **Schlecht:**
- Einzelne Scores isoliert betrachten
- Perfektion erwarten (alle Scores auf 0)
- Zu viele Baustellen gleichzeitig

---

### 4. Kontinuierliche Verbesserung

1. **Wöchentlich:** Heatmap checken
2. **Monatlich:** Tiefe Review-Session
3. **Quartalsweise:** Schwellenwerte neu kalibrieren
4. **Bei Änderungen:** Tests aktualisieren

---

## Roadmap

### Version 1.1 (geplant)

- [ ] Config-File-Support (TOML)
- [ ] Gewichtete Aggregation (konfigurierbar)
- [ ] Zeitliche Trends (Score-Entwicklung über Zeit)
- [ ] Auto-Drill-Empfehlungen basierend auf Problem-Clustern

### Version 1.2 (geplant)

- [ ] Interaktive Heatmap (Click → Details)
- [ ] Vergleichsmodus (Session A vs. Session B)
- [ ] Export-Funktionen (CSV, JSON, PDF)
- [ ] Multi-Session-Aggregation

---

## Support & Feedback

Bei Fragen, Bugs oder Feature-Requests:

1. **Code:** `src/reporting/psychology_heuristics.py`
2. **Tests:** `tests/reporting/test_psychology_heuristics.py`
3. **Beispiele:** `scripts/example_psychology_heuristics.py`
4. **Doku:** Dieses Dokument

---

## Lizenz & Autor

Teil des **Peak_Trade** Systems.

**Version:** 1.0  
**Datum:** Dezember 2025  
**Status:** Production-Ready  
**Autor:** Quant-Psychologie-Heuristik-Designer

---

**Ende der Dokumentation**
