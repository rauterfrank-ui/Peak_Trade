# Phase 33: Live-/Shadow-Run-Monitoring & CLI-Dashboards

## Übersicht

Phase 33 erweitert das Peak_Trade Framework um **Echtzeit-Monitoring** für laufende oder abgeschlossene Shadow-/Paper-Runs. Das Monitoring basiert auf den in Phase 31/32 eingeführten Run-Logs und bietet CLI-Dashboards zur Beobachtung von:

- **Equity / PnL-Verlauf**
- **Position & Exposure**
- **Risk-Events / geblockte Orders**

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     Shadow/Paper Session                        │
│                   (Phase 31 + 32)                               │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │ LiveCandles │ -> │   Strategy   │ -> │ ExecutionPipeline │  │
│  └─────────────┘    └──────────────┘    └────────┬────────┘   │
│                                                   │             │
│                                    ┌──────────────▼──────────┐ │
│                                    │    LiveRunLogger        │ │
│                                    │    (writes events)      │ │
│                                    └──────────────┬──────────┘ │
└───────────────────────────────────────────────────┼─────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Filesystem                                  │
│                                                                 │
│   live_runs/                                                    │
│   └── 20251204_180000_paper_ma_crossover_BTC-EUR_1m/           │
│       ├── meta.json        (Run-Metadaten)                     │
│       └── events.parquet   (Time-Series Events)                │
│                                                                 │
└───────────────────────────────────────────────────┬─────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Monitoring Module (Phase 33)                   │
│                   src/live/monitoring.py                        │
│                                                                 │
│   ┌────────────────────┐    ┌────────────────────┐             │
│   │ load_run_snapshot()│    │  load_run_tail()   │             │
│   │                    │    │                    │             │
│   │  -> LiveRunSnapshot│    │  -> [TailRow, ...] │             │
│   └─────────┬──────────┘    └─────────┬──────────┘             │
│             │                         │                         │
│             └──────────┬──────────────┘                         │
│                        ▼                                        │
│              ┌─────────────────────┐                           │
│              │   render_summary()  │                           │
│              │   render_tail()     │                           │
│              └─────────────────────┘                           │
│                                                                 │
└───────────────────────────────────────────────────┬─────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLI Monitor                                    │
│               scripts/monitor_live_run.py                       │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Peak_Trade Live Monitor (Phase 33)                     │  │
│   │  ═══════════════════════════════════════════════════════│  │
│   │                                                         │  │
│   │  === RUN SUMMARY ===                                    │  │
│   │  run_id        : 20251204_180000_paper_...              │  │
│   │  mode          : PAPER                                  │  │
│   │  strategy      : ma_crossover                           │  │
│   │  equity        : 10,050.00                              │  │
│   │  realized_pnl  : +100.00  (grün)                        │  │
│   │  blocked       : 1 (Risk-Blocked) (gelb)                │  │
│   │                                                         │  │
│   │  === LAST 15 EVENTS ===                                 │  │
│   │  ts_bar              equity    r_pnl   pos   risk       │  │
│   │  2025-12-04 18:23:00 10050.00  100.00  0.10  OK         │  │
│   │  2025-12-04 18:22:00  9900.00   50.00  0.10  BLOCK      │  │
│   │  ...                                                    │  │
│   │                                                         │  │
│   │  [monitor] run_dir=... | refresh in 2.0s | Ctrl+C      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Komponenten

### 1. Monitoring-Modul (`src/live/monitoring.py`)

Zentrale API für das Monitoring, die auf Run-Logs arbeitet:

#### Dataclasses

```python
@dataclass
class LiveRunSnapshot:
    """Aggregierter Snapshot des Run-Status."""
    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    started_at: Optional[datetime]
    last_bar_time: Optional[datetime]
    last_price: Optional[float]
    position_size: Optional[float]
    equity: Optional[float]
    realized_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    total_steps: int
    total_orders: int
    total_blocked_orders: int

@dataclass
class LiveRunTailRow:
    """Einzelne Zeile für die Tail-Ansicht."""
    ts_bar: Optional[datetime]
    equity: Optional[float]
    realized_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    position_size: Optional[float]
    orders_count: int
    risk_allowed: bool
    risk_reasons: str
```

#### Funktionen

| Funktion | Beschreibung |
|----------|--------------|
| `load_run_snapshot(run_dir)` | Lädt aggregierten Snapshot aus Run-Directory |
| `load_run_tail(run_dir, n)` | Lädt letzte N Events als TailRows |
| `get_latest_run_dir(base_dir)` | Findet neuestes Run-Directory |
| `render_summary(snapshot)` | Rendert Summary als Terminal-String |
| `render_tail(tail_rows)` | Rendert Tail-Tabelle als Terminal-String |

### 2. CLI Monitor (`scripts/monitor_live_run.py`)

Interaktives Terminal-Dashboard mit Auto-Refresh:

```bash
# Neuesten Run monitoren:
python3 -m scripts.monitor_live_run --latest

# Spezifischen Run:
python3 -m scripts.monitor_live_run --run-id 20251204_180000_paper_ma_crossover_BTC-EUR_1m

# Mit Optionen:
python3 -m scripts.monitor_live_run --latest --interval 5 --rows 20 --view both
```

#### CLI-Argumente

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--config` | `config/config.toml` | Pfad zur Config |
| `--run-dir` | - | Direkter Pfad zum Run-Directory |
| `--run-id` | - | Run-ID (wird aufgelöst) |
| `--latest` | - | Automatisch neuesten Run wählen |
| `--list` | - | Verfügbare Runs auflisten |
| `--interval` | 2.0 | Refresh-Intervall in Sekunden |
| `--rows` | 15 | Anzahl Tail-Zeilen |
| `--view` | `both` | `summary`, `tail`, oder `both` |
| `--no-colors` | - | ANSI-Farben deaktivieren |

### 3. Konfiguration (`[live_monitoring]`)

In `config/config.toml`:

```toml
[live_monitoring]
# Standard-Refresh-Intervall in Sekunden
default_interval_seconds = 2.0

# Anzahl der Tail-Zeilen (letzte Events)
default_tail_rows = 15

# ANSI-Farben im Terminal verwenden
use_colors = true
```

## Verwendung

### 1. Shadow-/Paper-Session starten

```bash
python3 -m scripts.run_shadow_paper_session --strategy ma_crossover
```

Die Session gibt einen Hinweis zum Monitoring aus:
```
Tip: You can monitor this run in real-time with:
  python3 -m scripts.monitor_live_run --run-dir live_runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m
Or monitor the latest run:
  python3 -m scripts.monitor_live_run --latest
```

### 2. Monitor in neuem Terminal starten

```bash
# In einem neuen Terminal-Fenster:
python3 -m scripts.monitor_live_run --latest
```

### 3. Verfügbare Runs anzeigen

```bash
python3 -m scripts.monitor_live_run --list
```

Output:
```
Available Runs in: live_runs
============================================================
   1. 20251204_180000_paper_ma_crossover_BTC-EUR_1m
   2. 20251204_150000_paper_rsi_strategy_ETH-EUR_5m
   3. 20251203_100000_paper_momentum_1h_BTC-EUR_1h

Total: 3 runs
```

## Dashboard-Ansichten

### Summary-View

```
============================================================
  RUN SUMMARY
============================================================

  run_id        : 20251204_180000_paper_ma_crossover_BTC-EUR_1m
  mode          : PAPER
  strategy      : ma_crossover
  symbol        : BTC/EUR
  timeframe     : 1m
  started_at    : 2025-12-04 18:00:00
  last_bar_time : 2025-12-04 18:23:00

  last_price    : 40,500.00
  position_size : 0.100000
  cash          : 9,800.00
  equity        : 10,050.00
  realized_pnl  : +100.00   <- grün bei positiv
  unrealized_pnl: +150.00   <- grün bei positiv

  steps         : 123
  orders        : 15
  blocked       : 1 (Risk-Blocked)  <- gelb wenn > 0
```

### Tail-View

```
====================================================================================================
  LAST 15 EVENTS
====================================================================================================
  ts_bar               equity       r_pnl      u_pnl        pos  ord   risk   reasons
  ------------------------------------------------------------------------------------------------
  2025-12-04 18:23:00   10,050.00    100.00    150.00     0.1000    0     OK   -
  2025-12-04 18:22:00    9,950.00     50.00    100.00     0.1000    1     OK   -
  2025-12-04 18:21:00    9,900.00     50.00     50.00     0.1000    0  BLOCK   max_total_exposure
  ...
```

## Safety & Governance

1. **Read-Only Monitoring**
   - Das Monitoring-Modul greift **nur lesend** auf Dateien zu
   - Es werden keine Trading-Entscheidungen getroffen
   - Keine Veränderung der Session oder Risk-Logik

2. **Fehlertoleranz**
   - Fehler beim Laden crashen nicht den Monitor
   - Fehlermeldung + Retry im nächsten Loop
   - Graceful Shutdown bei Ctrl+C

3. **Keine sensiblen Daten**
   - Run-Logs enthalten keine API-Keys oder Secrets
   - Nur Trading-Parameter und Metriken

## Tests

```bash
# Monitoring-Tests ausführen:
python3 -m pytest tests/test_live_monitoring.py -v
```

Test-Coverage:
- `test_load_run_snapshot_*`: Snapshot-Funktionen
- `test_load_run_tail_*`: Tail-Funktionen
- `test_render_*`: Render-Funktionen
- `test_*_integration`: Integration-Tests

## Einschränkungen (Phase 33)

- **Kein GUI/Web-Dashboard** - nur CLI
- **Keine externe Monitoring-Infra** - kein Prometheus, keine DB
- **Lokaler Betrieb** - kein Multi-User/Websocket
- **File-basiert** - keine Streaming-Events

## Weiterführende Dokumentation

- [Phase 31: Shadow-/Paper-Session](PHASE_31_SHADOW_PAPER_FLOW.md)
- [Phase 32: Run-Logging & Reporting](PHASE_32_SHADOW_PAPER_LOGGING_AND_REPORTING.md)
- [Live Risk Limits](LIVE_RISK_LIMITS.md)
