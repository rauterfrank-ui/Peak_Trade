# Integration Example: Session Storage in Offline-Realtime Scripts

## Beispiel: `run_offline_realtime_ma_crossover.py` erweitern

### Schritt 1: Import hinzufügen

Am Anfang des Scripts (nach den anderen Imports):

```python
from src.trigger_training import save_session_to_store
```

### Schritt 2: Session-ID generieren

In der `main()`-Funktion, nach dem Parsen der CLI-Args:

```python
def main():
    args = parse_args()
    
    # Session-ID für Trigger-Training-Store
    session_id = (
        f"OFFLINE_REALTIME_MA_CROSSOVER"
        f"_{normalize_symbol(args.symbol)}"
        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    logger.info(f"[SESSION] ID: {session_id}")
    
    # ... rest der main() ...
```

### Schritt 3: Events im Store speichern

Am Ende der `main()`-Funktion, nachdem `trigger_training_events` erstellt wurde:

```python
def main():
    # ... Pipeline-Ausführung ...
    
    # Trigger-Training-Events erstellen (bereits vorhanden im Script)
    if hook_config.enabled and len(tracker.signals_log) > 0:
        trigger_training_events = build_trigger_training_events_from_dfs(
            signals_df=signals_df,
            decisions_df=decisions_df,
            pnl_window=hook_config.pnl_window,
        )
        
        # NEU: Im Store speichern
        if trigger_training_events:
            store_path = Path("live_runs/trigger_training_sessions.jsonl")
            save_session_to_store(
                session_id=session_id,
                events=trigger_training_events,
                store_path=store_path,
            )
            logger.info(f"[SESSION] Gespeichert in Store: {store_path} ({len(trigger_training_events)} Events)")
        
        # Report generieren (bereits vorhanden)
        report_path = build_trigger_training_report(
            events=trigger_training_events,
            output_path=Path(f"reports/trigger_training/ma_crossover_{run_id}_trigger_training.html"),
        )
        logger.info(f"[REPORT] Trigger-Training-Report: {report_path}")
```

### Schritt 4: Testen

```bash
# Script ausführen
PYTHONPATH=. python3 scripts/run_offline_realtime_ma_crossover.py \
    --symbol BTC/EUR \
    --n-steps 500 \
    --fast-window 10 \
    --slow-window 30

# Sessions anzeigen
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --list

# Meta-Report generieren
PYTHONPATH=. python3 scripts/generate_operator_meta_report.py --limit 5
```

---

## Vollständiger Diff

```diff
--- a/scripts/run_offline_realtime_ma_crossover.py
+++ b/scripts/run_offline_realtime_ma_crossover.py
@@ -51,6 +51,7 @@ import pandas as pd
 from src.core.environment import EnvironmentConfig, TradingEnvironment
 from src.strategies.ma_crossover import MACrossoverStrategy
 from src.orders.paper import PaperOrderExecutor, PaperMarketContext
 from src.execution.pipeline import ExecutionPipeline, ExecutionPipelineConfig
+from src.trigger_training import save_session_to_store
 
@@ -800,6 +801,14 @@ def main():
     args = parse_args()
     setup_logging(args.log_level)
     
+    # Session-ID für Trigger-Training-Store
+    session_id = (
+        f"OFFLINE_REALTIME_MA_CROSSOVER"
+        f"_{normalize_symbol(args.symbol)}"
+        f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
+    )
+    logger.info(f"[SESSION] ID: {session_id}")
+    
     logger.info("=" * 70)
     logger.info("Offline-Realtime MA-Crossover Pipeline")
     logger.info("=" * 70)
@@ -900,6 +909,17 @@ def main():
             pnl_window=hook_config.pnl_window,
         )
         
+        # NEU: Im Store speichern
+        if trigger_training_events:
+            store_path = Path("live_runs/trigger_training_sessions.jsonl")
+            save_session_to_store(
+                session_id=session_id,
+                events=trigger_training_events,
+                store_path=store_path,
+            )
+            logger.info(
+                f"[SESSION] Gespeichert in Store: {store_path} ({len(trigger_training_events)} Events)"
+            )
+        
         # Trigger-Training-Report generieren
         report_path = build_trigger_training_report(
             events=trigger_training_events,
```

---

## Alternative: Minimale Integration (nur 3 Zeilen)

Falls du es noch einfacher halten willst:

```python
# Nach Trigger-Training-Events erstellen:
from src.trigger_training import save_session_to_store

if trigger_training_events:
    session_id = f"OFFLINE_REALTIME_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_session_to_store(session_id, trigger_training_events)
    print(f"[SESSION] Saved: {session_id}")
```

---

## Weitere Anwendungsfälle

### Live-Beta-Drill Integration

```python
# scripts/run_live_beta_drill.py

from src.trigger_training import save_session_to_store

# Nach Drill-Ausführung:
session_id = f"LIVE_BETA_DRILL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
save_session_to_store(
    session_id=session_id,
    events=drill_events,
    store_path="live_runs/trigger_training_sessions_live.jsonl",
)
```

### Research-Experiment Integration

```python
# src/experiments/...

from src.trigger_training import save_session_to_store

# Am Ende eines Experiments:
session_id = f"RESEARCH_ARMSTRONG_{experiment_id}"
save_session_to_store(
    session_id=session_id,
    events=experiment_events,
    store_path="live_runs/trigger_training_sessions_research.jsonl",
)
```

---

## Best Practice: Automatische Backups

Optional: Tägliches Backup des Session-Stores:

```bash
#!/bin/bash
# scripts/backup_session_store.sh

DATE=$(date +%Y%m%d)
cp live_runs/trigger_training_sessions.jsonl \
   live_runs/backups/trigger_training_sessions_${DATE}.jsonl

echo "[BACKUP] Session-Store gesichert: trigger_training_sessions_${DATE}.jsonl"
```

Ausführen via Cron:
```cron
0 0 * * * /path/to/Peak_Trade/scripts/backup_session_store.sh
```

