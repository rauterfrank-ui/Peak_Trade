# Trigger Training: Multi-Session Reports & Operator Analytics

**Status:** ✅ Production Ready  
**Version:** v1.0  
**Datum:** 2025-12-10

---

## 🎯 Überblick

Das Trigger-Training-System ermöglicht es Operatoren, ihre Reaktionsfähigkeit und Disziplin systematisch zu trainieren und über mehrere Sessions hinweg zu tracken.

### Key Features

- ✅ **Session Storage** – Persistentes Speichern von Drill-Sessions
- ✅ **Multi-Session Reports** – Aggregierte HTML-Reports über mehrere Drills
- ✅ **Operator Analytics** – Hit-Rate, Missed-Rate, Pain-Score, Reaktionszeit
- ✅ **CLI Tools** – Einfache Command-Line-Integration
- ✅ **Production Ready** – 8/8 Tests bestehen

---

## 📦 Module

### Core Module

| Modul | Pfad | Beschreibung |
|-------|------|--------------|
| **Hooks** | | Event-Extraktion aus DataFrames |
| **Operator Meta Report** | | HTML-Report-Generierung |
| **Session Store** | | Persistentes Speichern/Laden |

### Scripts

| Script | Beschreibung | Usage |
|--------|--------------|-------|
| `generate_operator_meta_report_demo.py` | Demo mit 3 künstlichen Sessions | `PYTHONPATH=. python3 scripts&#47;generate_operator_meta_report_demo.py` |
| `generate_operator_meta_report.py` | Production CLI für Meta-Reports | `PYTHONPATH=. python3 scripts&#47;generate_operator_meta_report.py` |

### Tests

| Test-Datei | Beschreibung | Status |
|------------|--------------|--------|
| `test_operator_meta_report.py` | Tests für HTML-Report-Generierung | ✅ 1/1 |
| `test_session_store.py` | Tests für Session-Storage | ✅ 6/6 |
| `test_trigger_training_hooks.py` | Tests für Event-Extraktion | ✅ 1/1 |

---

## 🚀 Quick Start

### 1. Demo ausführen

```bash
cd /Users/frnkhrz/Peak_Trade

# Demo-Sessions erstellen + Report generieren
PYTHONPATH=. python3 scripts/generate_operator_meta_report_demo.py

# Report im Browser öffnen
open reports/trigger_training/meta/operator_stats_overview_demo.html
```

### 2. Sessions verwalten

```bash
# Alle Session-IDs anzeigen
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list

# Meta-Report aus allen Sessions generieren
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py

# Nur letzte 5 Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 5

# Bestimmte Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py \
    --session-ids SESSION_A SESSION_B
```

### 3. In eigene Scripts integrieren

```python
from datetime import datetime
from pathlib import Path
from src.trigger_training import (
    build_trigger_training_events_from_dfs,
    save_session_to_store,
)

# Events aus Drill extrahieren
events = build_trigger_training_events_from_dfs(
    signals_df=signals_df,
    decisions_df=decisions_df,
    pnl_window=5,
)

# Session speichern
session_id = f"DRILL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
save_session_to_store(
    session_id=session_id,
    events=events,
    store_path="live_runs/trigger_training_sessions.jsonl",
)

print(f"[INFO] Session gespeichert: {session_id}")
```

---

## 📊 Report-Metriken

### Sessions Overview

Für jede Session:

| Metrik | Beschreibung | Zielwert |
|--------|--------------|----------|
| **n_events** | Anzahl der Trigger-Events | - |
| **hit_rate** | Erfolgsquote (HIT / n_events) | ≥ 0.70 |
| **missed_rate** | Verpasste Chancen (MISSED / n_events) | ≤ 0.20 |
| **avg_reaction_delay_s** | Durchschnittliche Reaktionszeit | ≤ 3.0s |
| **pain_score** | Summe verpasster PnL (MISSED + LATE + RULE_BREAK) | ≤ 50 |

### Globale Outcome-Verteilung

- **HIT** – Signal erkannt, rechtzeitig ausgeführt ✅
- **MISSED** – Signal verpasst ❌
- **LATE** – Zu langsam reagiert ⚠️
- **FOMO** – Emotionaler Trade ohne Signal 😱
- **RULE_BREAK** – Position zu groß, Regel verletzt ⚠️

### Top Pain Sessions

Top 5 Sessions nach Pain-Score sortiert, um Problemsessions zu identifizieren.

---

## 📁 Dateistruktur

```
Peak_Trade/
├── src/trigger_training/
│   ├── __init__.py
│   ├── hooks.py                    # Event-Extraktion
│   ├── operator_meta_report.py     # HTML-Report-Generator
│   └── session_store.py            # Session-Storage (JSONL)
│
├── scripts/
│   ├── generate_operator_meta_report_demo.py    # Demo
│   └── generate_operator_meta_report.py         # Production CLI
│
├── tests/trigger_training/
│   ├── test_operator_meta_report.py
│   ├── test_session_store.py
│   └── test_trigger_training_hooks.py
│
├── docs/trigger_training/
│   ├── README.md                                # Diese Datei
│   ├── WORKFLOW_MULTI_SESSION_REPORTS.md        # Workflow-Guide
│   └── INTEGRATION_EXAMPLE_SNIPPET.md           # Integration-Snippets
│
├── live_runs/
│   ├── trigger_training_sessions.jsonl          # Production Store
│   └── trigger_training_sessions_demo.jsonl     # Demo Store
│
└── reports/trigger_training/meta/
    ├── operator_stats_overview.html             # Production Report
    └── operator_stats_overview_demo.html        # Demo Report
```

---

## 🧪 Tests ausführen

```bash
# Alle Trigger-Training-Tests
python3 -m pytest tests/trigger_training/ -v

# Nur Session-Store-Tests
python3 -m pytest tests/trigger_training/test_session_store.py -v

# Nur Meta-Report-Tests
python3 -m pytest tests/trigger_training/test_operator_meta_report.py -v
```

**Erwartetes Ergebnis:** ✅ 8 passed

---

## 🔧 Integration in existierende Scripts

Siehe detaillierte Beispiele in:
- `docs/trigger_training/INTEGRATION_EXAMPLE_SNIPPET.md`
- `docs/trigger_training/WORKFLOW_MULTI_SESSION_REPORTS.md`

**Minimal-Integration (3 Zeilen):**

```python
from src.trigger_training import save_session_to_store

if trigger_training_events:
    session_id = f"DRILL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_session_to_store(session_id, trigger_training_events)
```

---

## 🎯 Mindest-Standards vor Live-Trading

Vor dem Übergang zu Live-Trading sollten folgende Metriken erreicht werden:

| Metrik | Zielwert | Bemerkung |
|--------|----------|-----------|
| **Anzahl Drills** | ≥ 10 | Mindestens 10 erfolgreiche Sessions |
| **Hit-Rate** | ≥ 70% | Über letzte 10 Sessions |
| **Missed-Rate** | ≤ 20% | Über letzte 10 Sessions |
| **Avg. Reaction Delay** | ≤ 3s | Über letzte 10 Sessions |
| **Pain-Score/Session** | ≤ 50 | Durchschnitt über letzte 10 Sessions |

---

## 📈 Roadmap

### v1.0 (✅ Aktuell)
- ✅ Session Storage (JSONL)
- ✅ Multi-Session HTML-Reports
- ✅ CLI Tools
- ✅ Tests (8/8)

### v1.1 (Geplant)
- [ ] Grafische Charts (Matplotlib/Plotly)
- [ ] Trend-Analyse (Hit-Rate über Zeit)
- [ ] CSV/Excel-Export
- [ ] Automatische Backups

### v2.0 (Zukunft)
- [ ] Web-Dashboard (Live-Monitoring)
- [ ] Automatische Alerts bei schlechter Performance
- [ ] ML-basierte Vorhersagen

---

## 📚 Weitere Dokumentation

- **Workflow-Guide:** `docs/trigger_training/WORKFLOW_MULTI_SESSION_REPORTS.md`
- **Integration-Beispiele:** `docs/trigger_training/INTEGRATION_EXAMPLE_SNIPPET.md`
- **Offline-Realtime-Pipeline:** `docs/SCRIPT_OFFLINE_REALTIME_MA_CROSSOVER.md`
- **Trigger-Training-Runbook:** `docs/runbooks/OFFLINE_TRIGGER_TRAINING_DRILL_V1.md`

---

## 🐛 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'src'`

```bash
# Lösung: PYTHONPATH setzen
PYTHONPATH=/Users/frnkhrz/Peak_Trade:$PYTHONPATH python3 scripts/...
```

### Problem: Keine Sessions im Store

```bash
# Store-Inhalt prüfen
cat live_runs/trigger_training_sessions.jsonl

# Sessions manuell hinzufügen (siehe Integration-Beispiele)
```

### Problem: HTML-Report leer

```bash
# Filter prüfen
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 10
```

---

## 🏆 Erfolge

```
[2025-12-10] ✅ Operator-Meta-Report v1.0 erfolgreich implementiert
[2025-12-10] ✅ Session-Store mit JSONL-Persistierung
[2025-12-10] ✅ CLI-Tools für Production-Use
[2025-12-10] ✅ 8/8 Tests bestanden
[2025-12-10] ✅ Vollständige Dokumentation
```

---

**Happy Drilling!** 🚀

*Peak_Trade Team – Dez 2025*
