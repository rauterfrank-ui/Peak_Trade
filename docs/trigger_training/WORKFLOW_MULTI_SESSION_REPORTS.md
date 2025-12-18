# Workflow: Multi-Session Trigger Training Reports

**Status:** ✅ Production Ready  
**Version:** v1.0  
**Datum:** 2025-12-10

---

## Übersicht

Das Multi-Session-Report-System ermöglicht es, Trigger-Training-Daten über mehrere Drill-Sessions hinweg zu aggregieren und als HTML-Report auszugeben. Dies hilft dabei, die Entwicklung von:

- **Reaktionsqualität** (Hit-Rate, Missed-Rate)
- **Disziplin** (FOMO, Rule-Breaks)
- **Pain Points** (Summe verpasster PnL)

über die Zeit zu tracken.

---

## Komponenten

### 1. Session Store (`src/trigger_training/session_store.py`)

Persistentes Speichern und Laden von Trigger-Training-Sessions.

**Funktionen:**
- `save_session_to_store(session_id, events, store_path)` – Speichert Session
- `load_sessions_from_store(store_path, limit, session_ids)` – Lädt Sessions
- `list_session_ids(store_path)` – Listet alle Session-IDs auf

**Storage-Format:**
- JSON-Lines (`.jsonl`) – eine Session pro Zeile
- Standard-Pfad: `live_runs/trigger_training_sessions.jsonl`

### 2. Meta Report Generator (`src/trigger_training/operator_meta_report.py`)

Generiert HTML-Report aus mehreren Sessions.

**Funktionen:**
- `build_operator_meta_report(sessions, output_path)` – Erstellt HTML-Report

**Report-Inhalt:**
- Sessions Overview (n_events, hit_rate, missed_rate, avg_reaction_delay_s, pain_score)
- Globale Outcome-Verteilung
- Top Pain Sessions (Top 5)

### 3. CLI Tools

**Demo-Script:**
```bash
PYTHONPATH=. python3 scripts/generate_operator_meta_report_demo.py
```

**Production CLI:**
```bash
# Alle Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py

# Nur letzte 5 Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 5

# Nur bestimmte Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --session-ids SESSION_A SESSION_B

# Session-IDs auflisten
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list
```

---

## Workflow

### Phase 1: Drill Durchführen + Events Speichern

**Option A: Manuell in Python-Script**

```python
from datetime import datetime
from pathlib import Path
from src.trigger_training import (
    build_trigger_training_events_from_dfs,
    save_session_to_store,
)

# 1. Drill durchführen (z.B. Offline-Realtime-MA-Crossover)
# ... dein Drill-Code ...

# 2. Events aus DataFrames extrahieren
events = build_trigger_training_events_from_dfs(
    signals_df=signals_df,
    decisions_df=decisions_df,
    pnl_window=5,
)

# 3. Session-ID generieren
session_id = f"DRILL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 4. Im Store speichern
save_session_to_store(
    session_id=session_id,
    events=events,
    store_path="live_runs/trigger_training_sessions.jsonl",
)

print(f"[INFO] Session gespeichert: {session_id}")
```

**Option B: Integration in bestehende Scripts**

Beispiel: `scripts/run_offline_realtime_ma_crossover.py` erweitern:

```python
# Am Ende des Scripts, nach dem Trigger-Training-Report
if trigger_training_events:
    from src.trigger_training import save_session_to_store
    
    session_id = f"OFFLINE_REALTIME_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_session_to_store(
        session_id=session_id,
        events=trigger_training_events,
        store_path="live_runs/trigger_training_sessions.jsonl",
    )
    print(f"[INFO] Session im Store: {session_id}")
```

### Phase 2: Sessions Anzeigen

```bash
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list
```

**Output:**
```
[INFO] 3 Sessions im Store:
  - DRILL_20250110_100530
  - DRILL_20250111_143022
  - DRILL_20250112_091455
```

### Phase 3: Meta-Report Generieren

```bash
# Alle Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py

# Nur letzte 5 Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 5

# Bestimmte Sessions
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py \
    --session-ids DRILL_20250110_100530 DRILL_20250111_143022
```

**Output:**
```
[INFO] Lade Sessions aus live_runs/trigger_training_sessions.jsonl...
[INFO] 3 Sessions geladen:
  - DRILL_20250110_100530: 8 Events
  - DRILL_20250111_143022: 12 Events
  - DRILL_20250112_091455: 6 Events
[INFO] Generiere Meta-Report...
[SUCCESS] Meta-Report generiert: reports/trigger_training/meta/operator_stats_overview.html
[INFO] Öffne im Browser: file:///Users/.../operator_stats_overview.html
```

### Phase 4: Report Analysieren

Öffne den HTML-Report im Browser und analysiere:

1. **Sessions Overview:**
   - Welche Session hatte die höchste Hit-Rate?
   - Welche Session hatte den höchsten Pain-Score?
   - Wie entwickelt sich die Reaktionszeit über die Sessions?

2. **Globale Outcome-Verteilung:**
   - Wie viele HITs vs. MISSED gesamt?
   - Wie viele emotionale Trades (FOMO, RULE_BREAK)?

3. **Top Pain Sessions:**
   - Welche Sessions waren besonders schmerzhaft?
   - Was war der Grund? (Notizen in Events prüfen)

---

## Best Practices

### 1. Session-ID-Konvention

Verwende aussagekräftige Session-IDs:

```python
# ✅ Gut: Datum + Zeit + Kontext
session_id = f"OFFLINE_REALTIME_BTCEUR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ✅ Gut: Drill-Typ + Kontext
session_id = f"DRILL_MA_CROSSOVER_MORNING_{datetime.now().strftime('%Y%m%d')}"

# ❌ Schlecht: Zu generisch
session_id = "SESSION_1"
```

### 2. Regelmäßige Reviews

- **Wöchentlich:** Meta-Report über letzte 7 Drills generieren
- **Monatlich:** Alle Sessions des Monats analysieren
- **Vor Live-Trading:** Mindestens 10 erfolgreiche Drills mit Hit-Rate > 70%

### 3. Ziel-Metriken

**Mindest-Standards vor Live-Trading:**
- Hit-Rate: ≥ 70%
- Missed-Rate: ≤ 20%
- Avg. Reaction Delay: ≤ 3 Sekunden
- Pain-Score pro Session: ≤ 50 (je nach Strategie)

### 4. Event-Notizen

Füge aussagekräftige Notizen zu Events hinzu:

```python
TriggerTrainingEvent(
    # ...
    note="Verpasst – abgelenkt durch Telefon",
    tags=["missed_opportunity", "distraction"],
)
```

Dies hilft später bei der Analyse der Top-Pain-Sessions.

---

## Beispiel: Vollständiger Workflow

```bash
# 1. Drill durchführen (erstellt automatisch Session im Store)
PYTHONPATH=. python3 scripts/run_offline_realtime_ma_crossover.py

# 2. Sessions anzeigen
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list

# 3. Meta-Report generieren (letzte 10 Sessions)
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 10

# 4. Report im Browser öffnen
open reports/trigger_training/meta/operator_stats_overview.html
```

---

## Nächste Schritte

### Kurzfristig (v1.1)
- [ ] Integration in alle Offline-Realtime-Scripts
- [ ] Automatische Backup-Funktion für Session-Store
- [ ] Grafische Darstellung (Charts) im HTML-Report

### Mittelfristig (v1.2)
- [ ] Trend-Analyse (Hit-Rate-Entwicklung über Zeit)
- [ ] Session-Vergleich (A/B-Vergleich zweier Sessions)
- [ ] Export als CSV/Excel für weitere Analysen

### Langfristig (v2.0)
- [ ] Web-Dashboard für Echtzeit-Monitoring
- [ ] Automatische Alerts bei schlechter Performance
- [ ] Machine Learning: Vorhersage von Pain-Sessions

---

## Fehlerbehebung

### Problem: `ModuleNotFoundError: No module named 'src'`

**Lösung:** PYTHONPATH setzen:
```bash
PYTHONPATH=/Users/frnkhrz/Peak_Trade:$PYTHONPATH python3 scripts/...
```

Oder am Anfang des Scripts hinzufügen:
```python
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
```

### Problem: Keine Sessions im Store

**Lösung:** Prüfe, ob Sessions gespeichert werden:
```bash
cat live_runs/trigger_training_sessions.jsonl
```

Falls leer, integriere `save_session_to_store()` in deine Drill-Scripts.

### Problem: HTML-Report zeigt "Keine Events vorhanden"

**Lösung:** Prüfe Filter-Kriterien (--limit, --session-ids) oder Store-Pfad (--store-path).

---

## Kontakt & Support

Bei Fragen oder Problemen: Peak_Trade Team  
Dokumentation: `docs/trigger_training/`

**Happy Drilling!** 🚀

