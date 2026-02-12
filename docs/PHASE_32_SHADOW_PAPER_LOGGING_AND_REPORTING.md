# Phase 32: Shadow/Paper Run Logging & Live Reporting

## Übersicht

Phase 32 erweitert das Shadow/Paper Trading System (Phase 31) um strukturiertes Run-Logging und Report-Generierung. Jeder Run wird mit einer eindeutigen Run-ID gespeichert und kann später analysiert werden.

### Zielsetzung

- **Strukturiertes Logging** jedes Shadow-/Paper-Runs
- **Persistente Events** in Parquet/CSV Format
- **Report-Generierung** aus Run-Logs
- **CLI-Tools** für Logging-Kontrolle und Report-Erstellung

### Key Features

1. **Eindeutige Run-IDs** mit Timestamp, Mode, Strategie, Symbol, Timeframe
2. **Event-basiertes Logging** mit OHLC, Signals, Orders, Risk-Events
3. **Automatisches Flushing** für Persistenz
4. **Markdown/HTML Reports** aus Run-Logs

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ShadowPaperSession                               │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  step_once()│───►│LiveRunEvent │───►│    LiveRunLogger        │ │
│  │             │    │  (collect)  │    │  log_event() / flush()  │ │
│  └─────────────┘    └─────────────┘    └───────────┬─────────────┘ │
│                                                     │               │
└─────────────────────────────────────────────────────┼───────────────┘
                                                      │
                                                      ▼
                           ┌──────────────────────────────────────────┐
                           │         Filesystem                        │
                           │  live_runs/{run_id}/                     │
                           │     ├── meta.json                        │
                           │     ├── events.parquet (oder .csv)       │
                           │     └── report.md (optional)             │
                           └──────────────────────────────────────────┘
                                                      │
                                                      ▼
                           ┌──────────────────────────────────────────┐
                           │      Report Generation                    │
                           │  build_live_run_report()                 │
                           │      → Report (Markdown/HTML)            │
                           └──────────────────────────────────────────┘
```

### Komponenten

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| `ShadowPaperLoggingConfig` | `src/live/run_logging.py` | Logging-Konfiguration |
| `LiveRunMetadata` | `src/live/run_logging.py` | Run-Metadaten |
| `LiveRunEvent` | `src/live/run_logging.py` | Einzelnes Event |
| `LiveRunLogger` | `src/live/run_logging.py` | Logger-Klasse |
| `build_live_run_report` | `src/reporting/live_run_report.py` | Report-Builder |
| CLI | `scripts/run_shadow_paper_session.py` | Session CLI |
| CLI | `scripts/generate_live_run_report.py` | Report CLI |

---

## Konfiguration

### config.toml

```toml
[shadow_paper_logging]
# Run-Logging aktivieren
enabled = true

# Basis-Verzeichnis für Run-Logs
base_dir = "live_runs"

# Flush-Intervall (alle N Steps werden Events persistiert)
flush_interval_steps = 50

# Format für Events-Datei ("parquet" oder "csv")
format = "parquet"

# Automatisch Markdown-Report beim Beenden generieren
write_markdown_report_on_finish = false

# Detailliertes Event-Logging
log_ohlc_details = true
log_order_details = true
log_risk_details = true
```

### Konfigurationsparameter

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `enabled` | bool | true | Logging aktivieren |
| `base_dir` | str | "live_runs" | Basis-Verzeichnis |
| `flush_interval_steps` | int | 50 | Flush alle N Steps |
| `format` | str | "parquet" | "parquet" oder "csv" |
| `write_markdown_report_on_finish` | bool | false | Auto-Report |
| `log_ohlc_details` | bool | true | OHLC loggen |
| `log_order_details` | bool | true | Orders loggen |
| `log_risk_details` | bool | true | Risk loggen |

---

## Filesystem-Layout

```
live_runs/
└── 20251204_180000_paper_ma_crossover_BTC-EUR_1m/
    ├── meta.json           # Run-Metadaten
    ├── events.parquet      # Time-Series Events
    └── report.md           # Optional: Generierter Report
```

### meta.json

```json
{
  "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
  "mode": "paper",
  "strategy_name": "ma_crossover",
  "symbol": "BTC/EUR",
  "timeframe": "1m",
  "started_at": "2025-12-04T18:00:00+00:00",
  "ended_at": "2025-12-04T19:30:00+00:00",
  "config_snapshot": {
    "shadow_paper": {
      "start_balance": 10000.0,
      "fee_rate": 0.0026
    }
  },
  "notes": ""
}
```

### events.parquet/csv

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| step | int | Schritt-Nummer |
| ts_bar | datetime | Bar-Zeitstempel |
| ts_event | datetime | Event-Zeitstempel |
| price | float | Close-Preis |
| open, high, low, close | float | OHLC-Daten |
| volume | float | Volumen |
| position_size | float | Aktuelle Position |
| signal | int | Strategie-Signal (-1, 0, +1) |
| signal_changed | bool | Signal-Änderung |
| orders_generated | int | Generierte Orders |
| orders_filled | int | Gefüllte Orders |
| orders_rejected | int | Abgelehnte Orders |
| orders_blocked | int | Durch Risk blockiert |
| risk_allowed | bool | Risk-Check bestanden |
| risk_reasons | str | Block-Gründe |

---

## CLI-Nutzung

### Session starten

```bash
# Standard mit Logging
python3 -m scripts.run_shadow_paper_session

# Mit spezifischer Run-ID
python3 -m scripts.run_shadow_paper_session --run-id my_test_001

# Logging deaktivieren
python3 -m scripts.run_shadow_paper_session --no-logging

# Alternatives Log-Verzeichnis
python3 -m scripts.run_shadow_paper_session --log-dir /tmp/runs
```

### Report generieren

```bash
# Report für spezifischen Run
python3 -m scripts.generate_live_run_report live_runs/RUN_ID

# Als HTML
python3 -m scripts.generate_live_run_report live_runs/RUN_ID --format html

# In Datei speichern
python3 -m scripts.generate_live_run_report live_runs/RUN_ID -o report.md

# Alle Runs auflisten
python3 -m scripts.generate_live_run_report --list

# Letzten Run
python3 -m scripts.generate_live_run_report --latest
```

---

## Programmatische Nutzung

### Run-Logger direkt verwenden

```python
from src.live.run_logging import (
    LiveRunLogger,
    LiveRunMetadata,
    LiveRunEvent,
    ShadowPaperLoggingConfig,
    generate_run_id,
)

# Konfiguration
cfg = ShadowPaperLoggingConfig(
    enabled=True,
    base_dir="live_runs",
    format="parquet",
)

# Metadaten
run_id = generate_run_id("paper", "ma_crossover", "BTC/EUR", "1m")
metadata = LiveRunMetadata(
    run_id=run_id,
    mode="paper",
    strategy_name="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1m",
)

# Logger verwenden (Context Manager)
with LiveRunLogger(cfg, metadata) as logger:
    for candle in data_source:
        # ... process ...
        event = LiveRunEvent(
            step=step,
            ts_bar=candle.timestamp,
            price=candle.close,
            signal=current_signal,
            # ...
        )
        logger.log_event(event)

# Nach Exit: Events gespeichert, Metadaten finalisiert
```

### Mit ShadowPaperSession

```python
from src.live.shadow_session import create_shadow_paper_session
from src.core.peak_config import load_config

cfg = load_config("config/config.toml")
strategy = create_strategy("ma_crossover", cfg)

# Session mit Logging (automatisch aktiviert)
session = create_shadow_paper_session(
    cfg=cfg,
    strategy=strategy,
    run_id="custom_run_id",      # Optional
    enable_logging=True,          # Default
    log_dir_override=None,        # Optional
)

session.warmup()
session.run_n_steps(100, sleep_between=False)

# Logger-Info
if session.run_logger:
    print(f"Run-Dir: {session.run_logger.run_dir}")
    print(f"Events: {session.run_logger.total_events_logged}")
```

### Report generieren

```python
from src.reporting.live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)

# Von Dateipfaden
report = build_live_run_report(
    meta_path="live_runs/RUN_ID/meta.json",
    events_path="live_runs/RUN_ID/events.parquet",
)

# Von Verzeichnis
report = load_and_build_report("live_runs/RUN_ID")

# Ausgabe
print(report.to_markdown())
print(report.to_html())

# Speichern
save_report(report, "output.md", format="markdown")
save_report(report, "output.html", format="html")
```

### Runs auflisten und laden

```python
from src.live.run_logging import list_runs, load_run_metadata, load_run_events

# Alle Runs
runs = list_runs("live_runs")
print(f"Gefunden: {len(runs)} Runs")

# Metadaten laden
meta = load_run_metadata("live_runs/RUN_ID")
print(f"Strategy: {meta.strategy_name}")

# Events laden
events_df = load_run_events("live_runs/RUN_ID")
print(f"Steps: {len(events_df)}")
```

---

## Report-Inhalt

Ein generierter Report enthält:

### 1. Summary

- Total Steps
- Signal Changes
- Orders (Generated, Filled, Rejected, Blocked)
- Fill Rate
- Final Position
- Run Duration

### 2. Session Info

- Run ID, Mode, Strategy
- Symbol, Timeframe
- Start/End Time

### 3. Signal Statistics

- Signal Distribution (-1, 0, +1)
- Total Signal Changes

### 4. Order Statistics

- Events with Orders
- Fill/Reject/Block Counts

### 5. Risk Events

- Risk Violations Count
- Violation Reasons

### 6. Trade List

- Tabelle aller Trades (Step, Time, Signal, Price, Filled, Position)

### 7. Configuration

- Config-Snapshot aus Metadaten

---

## Tests

```bash
# Alle Phase-32-Tests
python3 -m pytest tests/test_run_logging_and_reporting.py -v

# Spezifische Test-Klassen
python3 -m pytest tests/test_run_logging_and_reporting.py::TestLiveRunLogger -v
python3 -m pytest tests/test_run_logging_and_reporting.py::TestReportGeneration -v
```

### Test-Kategorien

| Kategorie | Beschreibung |
|-----------|--------------|
| `TestShadowPaperLoggingConfig` | Config-Tests |
| `TestLiveRunMetadata` | Metadaten-Tests |
| `TestLiveRunEvent` | Event-Tests |
| `TestGenerateRunId` | Run-ID-Generierung |
| `TestLiveRunLogger` | Logger-Tests |
| `TestHelperFunctions` | Helper-Funktionen |
| `TestReportGeneration` | Report-Tests |
| `TestSessionIntegration` | Session-Integration |

---

## Integration mit Phase 31

Phase 32 integriert nahtlos mit der bestehenden ShadowPaperSession aus Phase 31:

1. **Optionaler run_logger Parameter** in `ShadowPaperSession.__init__()`
2. **Automatische Event-Generierung** in `step_once()`
3. **Finalisierung** in `run_forever()`, `run_n_steps()`, `run_for_duration()`
4. **Factory-Funktion** `create_shadow_paper_session()` mit Logging-Support

---

## Best Practices

1. **Parquet für Produktion** - Effizienter als CSV für große Runs
2. **Regelmäßiges Flushing** - `flush_interval_steps=50` für Balance
3. **Run-IDs** - Automatisch generieren lassen für Konsistenz
4. **Logging deaktivieren** - Für schnelle Tests `--no-logging` verwenden
5. **Cleanup** - Alte Runs regelmäßig archivieren/löschen

---

## Referenzen

- [Phase 31: Shadow/Paper Flow](./PHASE_31_SHADOW_PAPER_FLOW.md)
- [Phase 30: Reporting](./REPORTING_V2.md)
- `src/live/run_logging.py` - Run-Logging-Modul
- `src/reporting/live_run_report.py` - Report-Generierung
- `scripts/run_shadow_paper_session.py` - Session CLI
- `scripts/generate_live_run_report.py` - Report CLI
