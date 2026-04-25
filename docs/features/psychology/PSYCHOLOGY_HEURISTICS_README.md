# 🧠 Psychologie-Heuristik-System – Quick Start


## Authority and epoch note

This document preserves historical and component-level trading psychology context. Psychology readiness, production-ready, complete, success, operational, or readiness wording is not, by itself, current Master V2 approval, Doubleplay authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, or permission to route orders into any live capital path.

Psychology material can support operator discipline and review, but it is not a standalone promotion gate. Any live or first-live promotion remains governed by current gate/evidence/signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, and staged Execution Enablement. This docs-only note changes no runtime behavior and changes no checklist items, tables, dates, or historical claims.

**Status:** ✅ Production-Ready  
**Version:** 1.0  
**Tests:** 47/47 passing ✅

---

## 🎯 Was ist das?

Ein **quantitatives Scoring-System** für Trading-Psychologie-Analyse. Es berechnet Scores (0–3) für **5 Achsen**:

| Achse | Beschreibung | Beispiel |
|-------|--------------|----------|
| **FOMO** | Hinterherjagen von Moves | Spät in gelaufenen Move einsteigen |
| **Verlustangst** | Zu frühe Exits, Vermeidung | Exit bei kleinem Adverse-Move |
| **Impulsivität** | Spontan-Trades ohne Setup | Entry ohne Signal |
| **Zögern** | Zu spät oder gar nicht | Setup verpasst |
| **Regelbruch** | System-Regeln ignoriert | Entry gegen Signal-Richtung |

---

## 🚀 Quick Start

### 1. Minimal-Beispiel

```python
from src.reporting.psychology_heuristics import (
    TriggerTrainingPsychEventFeatures,
    compute_psychology_heatmap_from_events,
)

# Events erstellen
events = [
    TriggerTrainingPsychEventFeatures(
        cluster="Trend-Folge",
        event_type="ENTER",
        side="LONG",
        signal_strength=0.8,
        latency_s=5.0,  # Spät!
        latency_window_s=3.0,
        price_move_since_signal_pct=0.6,  # Großer Move!
        price_max_favorable_pct=0.7,
        price_max_adverse_pct=0.1,
        pnl_vs_ideal_bp=-25.0,
        had_valid_setup=True,
        entered_without_signal=False,
        opposite_to_signal=False,
        size_violation=False,
        risk_violation=False,
        recent_loss_streak=0,
        recent_skip_streak=0,
        manually_marked_fomo=True,  # Manuell markiert
        manually_marked_fear=False,
        manually_marked_impulsive=False,
    ),
]

# Heatmap-Daten generieren (End-to-End)
heatmap_data = compute_psychology_heatmap_from_events(events)

# In Template verwenden
# render_template("psychology.html", heatmap_rows=heatmap_data)
```

### 2. Demo-Script ausführen

```bash
cd /Users/frnkhrz/Peak_Trade
PYTHONPATH=. python3 scripts/example_psychology_heuristics.py
```

Zeigt:
- Event-Level Scoring
- Cluster-Aggregation
- End-to-End Workflow
- JSON-Export
- Flask-Integration

### 3. Tests ausführen

```bash
python3 -m pytest tests/reporting/test_psychology_heuristics.py -v
```

**Ergebnis:** 47 Tests, alle passing ✅

---

## 📁 Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/reporting/psychology_heuristics.py` | **Kern-Modul** (780 Zeilen) |
| `tests/reporting/test_psychology_heuristics.py` | **Tests** (1100+ Zeilen) |
| `scripts/example_psychology_heuristics.py` | **Demo-Script** |
| `docs/psychology_heuristics.md` | **Ausführliche Doku** |
| `PSYCHOLOGY_HEURISTICS_README.md` | **Dieser Quick Start** |

---

## 🔢 Scoring-Formeln (Kurzversion)

### FOMO
```
base = late_factor * 1.5 + move_component
if manually_marked: base += 1.0
return clamp_0_3(base)
```

### Verlustangst
```
if EXIT && adverse_small && pnl_bad: base += 2.0
if NO_ACTION && loss_streak_high: base += 1.7
if manually_marked: base += 1.0
return clamp_0_3(base)
```

### Impulsivität
```
if !valid_setup: base += 1.5
if very_fast: base += 1.0
if no_signal: base += 1.5
return clamp_0_3(base)
```

### Zögern
```
if late_action: base += 2.0
if NO_ACTION && setup && big_move_missed: base += 1.5
if skip_streak_high: base += 1.0
return clamp_0_3(base)
```

### Regelbruch
```
if opposite_signal: base += 1.5
if size_violation: base += 1.0
if risk_violation: base += 1.0
return clamp_0_3(base)
```

---

## ⚙️ Schwellenwerte (konfigurierbar)

Am Kopf von `psychology_heuristics.py`:

```python
LATENCY_OK_S = 3.0          # <= okay
LATENCY_HESITATION_S = 8.0  # > = hohes Zögern

MOVE_SMALL_PCT = 0.10       # 0.10%
MOVE_MEDIUM_PCT = 0.30      # 0.30%
MOVE_LARGE_PCT = 0.70       # 0.70%

PNL_MEDIUM_BP = 15.0        # 15 Basis-Punkte
PNL_LARGE_BP = 30.0         # 30 Basis-Punkte

LOSS_STREAK_MEDIUM = 2
LOSS_STREAK_HIGH = 4
SKIP_STREAK_MEDIUM = 2
SKIP_STREAK_HIGH = 4
```

---

## 🔌 Integration

### Flask-Route

```python
from src.reporting.psychology_heuristics import (
    compute_psychology_heatmap_from_events,
)

@app.route("/psychology/<session_id>")
def psychology(session_id):
    events = load_and_convert_events(session_id)
    heatmap_data = compute_psychology_heatmap_from_events(events)
    return render_template("psychology.html", heatmap_rows=heatmap_data)
```

### Template

```jinja
{% from 'psychology_heatmap_macro.html' import psychology_heatmap %}
{{ psychology_heatmap(heatmap_rows, show_legend=True) }}
```

---

## 📊 Output-Format

```python
[
    {
        "name": "Trend-Folge Einstiege",
        "fomo": {
            "value": 2.0,
            "heat_level": 2,         # 0, 1, 2, oder 3
            "display_value": "2",
            "css_class": "heat-2",   # heat-0, heat-1, heat-2, heat-3
        },
        "loss_fear": { ... },
        "impulsivity": { ... },
        "hesitation": { ... },
        "rule_break": { ... },
    },
    # ... weitere Cluster
]
```

Direkt kompatibel mit `psychology_heatmap_macro.html`!

---

## ✅ Checkliste für Integration

- [ ] Event-Daten sammeln (Signals, Actions, Timestamps, Prices)
- [ ] `TriggerTrainingPsychEventFeatures` aus Rohdaten erstellen
- [ ] `compute_psychology_heatmap_from_events()` aufrufen
- [ ] Output in Template übergeben
- [ ] Optional: Cluster-Statistiken mit `calculate_cluster_statistics()` berechnen

---

## 📚 Weitere Ressourcen

| Ressource | Link |
|-----------|------|
| **Ausführliche Doku** | `docs/psychology_heuristics.md` |
| **Heatmap-Integration** | `docs/psychology_heatmap_integration.md` |
| **Code** | `src/reporting/psychology_heuristics.py` |
| **Tests** | `tests/reporting/test_psychology_heuristics.py` |
| **Demo** | `scripts/example_psychology_heuristics.py` |

---

## 🎓 Konzepte

### Score-Bedeutung

| Score | Farbe | Bedeutung | Aktion |
|-------|-------|-----------|--------|
| **0** | 🟢 Grau | Kein Thema | ✅ Alles gut |
| **1** | 🔵 Blau | Leicht | 💡 Bewusstsein |
| **2** | 🟡 Amber | Mittel | ⚠️ Aufmerksam |
| **3** | 🔴 Rot | Stark | 🚨 Dringend |

### Aggregations-Strategie

Pro Cluster:
```
avg_all = Durchschnitt aller Event-Scores
avg_top3 = Durchschnitt der Top-3 Event-Scores
combined = 0.5 * avg_all + 0.5 * avg_top3
cluster_score = clamp_0_3(combined)
```

**Intuition:** Starke Events bekommen mehr Gewicht, aber nicht zu viel (50/50 Mix).

---

## 🐛 Troubleshooting

### Problem: Import-Error

```bash
ModuleNotFoundError: No module named 'src'
```

**Lösung:**
```bash
PYTHONPATH=/Users/frnkhrz/Peak_Trade:$PYTHONPATH python3 your_script.py
```

### Problem: Alle Scores sind 0

**Ursachen:**
- Keine Events vorhanden
- Feature-Werte alle im "grünen Bereich"
- Flags nicht korrekt gesetzt

**Lösung:** Prüfe Event-Features mit Beispiel-Events:
```python
from src.reporting.psychology_heuristics import create_example_fomo_event
ev = create_example_fomo_event()
print(score_fomo(ev))  # Sollte >= 2 sein
```

### Problem: Tests schlagen fehl

**Lösung:**
```bash
cd /Users/frnkhrz/Peak_Trade
python3 -m pytest tests/reporting/test_psychology_heuristics.py -v
```

Sollte 47/47 passing sein. Wenn nicht → Code-Review.

---

## 🎯 Next Steps

1. ✅ **Tests laufen lassen:** `python3 -m pytest tests&#47;reporting&#47;test_psychology_heuristics.py -v`
2. ✅ **Demo anschauen:** `PYTHONPATH=. python3 scripts&#47;example_psychology_heuristics.py`
3. 📖 **Doku lesen:** `docs/psychology_heuristics.md`
4. 🔧 **Integrieren:** Event-Konvertierung implementieren
5. 🎨 **Visualisieren:** In Dashboard einbauen

---

## ✨ Features

- [x] 5 Psychologie-Achsen mit quantitativen Formeln
- [x] Event-Level & Cluster-Level Scoring
- [x] Heatmap-kompatibles Output-Format
- [x] 47 Unit-Tests (100% passing)
- [x] Beispiel-Script mit Demo-Daten
- [x] Ausführliche Dokumentation
- [x] Konfigurierbare Schwellenwerte
- [x] Manuelle Markierungen (FOMO, Fear, Impulsive)
- [x] Aggregations-Strategien (50/50 Mix avg/top3)

---

**Status:** ✅ Ready to Use!

**Viel Erfolg beim Integrieren! 🚀**
