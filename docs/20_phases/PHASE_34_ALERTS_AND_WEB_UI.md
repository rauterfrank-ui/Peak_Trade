# Phase 34: Alerts & Web-UI

## Übersicht

Phase 34 erweitert den Live-/Shadow-Run-Stack (Phasen 31-33) um:

- **Phase 34A – Alerts**: Regelbasiertes Alert-System für Anomalien und Risk-Events
- **Phase 34B – Web-API**: REST-Endpoints für Run-Daten (FastAPI)
- **Phase 34C – Web-UI**: HTML-Dashboard für Browser-basiertes Monitoring

**Wichtig**: Die Web-UI ist read-only und trifft keine Trading-Entscheidungen.

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Peak_Trade Live Stack                        │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 31-32: Shadow/Paper Session → events.parquet, meta.json      │
│                                                                      │
│  Phase 33: Monitoring CLI                                            │
│            └── load_run_snapshot(), load_run_tail()                 │
│                                                                      │
│  Phase 34A: Alerts                                                   │
│             └── AlertEngine.evaluate_snapshot() → alerts.jsonl      │
│                                                                      │
│  Phase 34B: Web-API (FastAPI)                                        │
│             └── /runs, /runs/{id}/snapshot, /runs/{id}/tail         │
│                                                                      │
│  Phase 34C: Web-UI (HTML Dashboard)                                  │
│             └── Auto-Refresh Dashboard unter /                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Web-Dependencies installieren

```bash
# Optional dependencies für Web-UI
pip install -e ".[web]"

# Oder manuell:
pip install fastapi uvicorn
```

---

## Komponenten

### 1. Alerts (Phase 34A)

**Modul**: `src/live/alerts.py`

#### Datenklassen

```python
from src.live.alerts import (
    AlertsConfig,
    AlertRule,
    AlertEvent,
    AlertEngine,
    Severity,
)

# AlertsConfig - Konfiguration
config = AlertsConfig(
    enabled=True,
    min_severity="warning",
    debounce_seconds=60,
    rules={
        "risk_blocked": AlertRule(enabled=True, severity="critical"),
        "large_loss_abs": AlertRule(enabled=True, severity="warning", threshold=-500.0),
        "large_loss_pct": AlertRule(enabled=True, severity="warning", threshold=-5.0),
        "drawdown": AlertRule(enabled=True, severity="critical", threshold=-10.0),
        "no_events": AlertRule(enabled=True, severity="info"),
    },
)

# AlertEvent - Einzelner Alert
alert = AlertEvent(
    rule_id="risk_blocked",
    severity="critical",
    message="Risk-Limit blocked order",
    run_id="20251204_180000_paper_ma_crossover_BTC-EUR_1m",
    timestamp=datetime.now(timezone.utc),
)
```

#### Built-in Alert-Regeln

| Rule ID | Beschreibung | Default Severity |
|---------|--------------|------------------|
| `risk_blocked` | Order wurde von Risk-Limits blockiert | critical |
| `large_loss_abs` | Absoluter Verlust überschreitet Schwelle | warning |
| `large_loss_pct` | Prozentualer Verlust überschreitet Schwelle | warning |
| `drawdown` | Drawdown überschreitet Schwelle | critical |
| `no_events` | Keine Events in den letzten N Minuten | info |

#### Severity-Ranking

```python
Severity.CRITICAL > Severity.WARNING > Severity.INFO
Severity.rank("critical")  # → 3
Severity.rank("warning")   # → 2
Severity.rank("info")      # → 1
```

#### AlertEngine Verwendung

```python
from src.live.alerts import AlertEngine, create_alert_engine_from_config
from src.live.monitoring import load_run_snapshot

# Engine erstellen
engine = create_alert_engine_from_config(config)

# Snapshot evaluieren
snapshot = load_run_snapshot(run_dir)
alerts = engine.evaluate_snapshot(snapshot)

# Alerts in Datei schreiben
from src.live.alerts import append_alerts_to_file
append_alerts_to_file(run_dir / "alerts.jsonl", alerts)

# Alerts laden
from src.live.alerts import load_alerts_from_file
all_alerts = load_alerts_from_file(run_dir / "alerts.jsonl")
```

#### Debouncing

Der AlertEngine verhindert Alert-Spam durch Debouncing:
- Gleiche `rule_id` wird nur einmal pro `debounce_seconds` ausgelöst
- Standard: 60 Sekunden

### 2. Web-API (Phase 34B)

**Modul**: `src/live/web/app.py`

#### Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/health` | GET | Health-Check |
| `/runs` | GET | Liste aller Runs |
| `/runs/{run_id}/snapshot` | GET | Aktueller Snapshot eines Runs |
| `/runs/{run_id}/tail` | GET | Letzte N Events (default: 50) |
| `/runs/{run_id}/alerts` | GET | Alerts eines Runs (default: 100) |
| `/` | GET | HTML Dashboard |
| `/dashboard` | GET | HTML Dashboard (Alias) |

#### Response-Modelle

```python
# GET /health
{"status": "ok"}

# GET /runs
[
    {
        "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
        "mode": "paper",
        "strategy_name": "ma_crossover",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
        "started_at": "2025-12-04T18:00:00+00:00",
        "ended_at": null
    }
]

# GET /runs/{run_id}/snapshot
{
    "run_id": "...",
    "mode": "paper",
    "strategy_name": "ma_crossover",
    "symbol": "BTC/EUR",
    "timeframe": "1m",
    "total_steps": 100,
    "total_orders": 5,
    "total_blocked_orders": 1,
    "equity": 10250.50,
    "realized_pnl": 150.50,
    "unrealized_pnl": 100.00,
    "position_size": 0.1,
    "drawdown_pct": -2.5,
    "last_bar_ts": "2025-12-04T19:40:00+00:00"
}

# GET /runs/{run_id}/tail?limit=10
[
    {
        "ts_bar": "2025-12-04T19:40:00+00:00",
        "equity": 10250.50,
        "realized_pnl": 150.50,
        "unrealized_pnl": 100.00,
        "position_size": 0.1,
        "orders_count": 0,
        "risk_allowed": true,
        "risk_reasons": ""
    }
]

# GET /runs/{run_id}/alerts?limit=50
[
    {
        "rule_id": "risk_blocked",
        "severity": "critical",
        "message": "Risk-Limit blocked order",
        "run_id": "...",
        "timestamp": "2025-12-04T19:15:00+00:00"
    }
]
```

### 3. Web-UI (Phase 34C)

**Modul**: `src/live/web/app.py` (inline HTML)

#### Features

- Automatische Liste aller verfügbaren Runs
- Snapshot-Anzeige mit Key-Metriken
- Tail-Ansicht der letzten Events
- Alerts-Liste mit Severity-Highlighting
- Auto-Refresh (konfigurierbar, default: 5 Sekunden)
- Responsive Design für Desktop und Mobile

#### Dashboard starten

```bash
# Mit Defaults (127.0.0.1:8000)
python -m scripts.serve_live_dashboard

# Mit Custom-Port
python -m scripts.serve_live_dashboard --port 8080

# Mit anderem Runs-Verzeichnis
python -m scripts.serve_live_dashboard --base-runs-dir /path/to/runs

# Mit Auto-Reload (Development)
python -m scripts.serve_live_dashboard --reload
```

---

## Konfiguration

### config/config.toml

```toml
# =============================================================================
# Phase 34: Alerts
# =============================================================================
[alerts]
enabled = true
min_severity = "warning"  # "info", "warning", "critical"
debounce_seconds = 60

[alerts.rules]
enable_risk_blocked = true
enable_large_loss_abs = true
large_loss_abs_threshold = -500.0  # EUR
enable_large_loss_pct = true
large_loss_pct_threshold = -5.0    # Prozent
enable_drawdown = true
drawdown_threshold = -10.0         # Prozent
enable_no_events = false           # Optional

# =============================================================================
# Phase 34: Web-UI
# =============================================================================
[web_ui]
enabled = true
host = "127.0.0.1"
port = 8000
auto_refresh_seconds = 5
```

### WebUIConfig

```python
from src.live.web.app import WebUIConfig, load_web_ui_config
from src.core.peak_config import load_config

# Defaults
cfg = WebUIConfig()
assert cfg.host == "127.0.0.1"
assert cfg.port == 8000
assert cfg.auto_refresh_seconds == 5
assert cfg.base_runs_dir == "live_runs"

# Aus config.toml laden
config = load_config("config/config.toml")
web_cfg = load_web_ui_config(config)
```

---

## Integration mit CLI-Monitor

Der CLI-Monitor (`scripts/monitor_live_run.py`) wurde erweitert:

```bash
# Mit Alerts (Default)
python -m scripts.monitor_live_run

# Ohne Alerts
python -m scripts.monitor_live_run --no-alerts

# Nur kritische Alerts
# (In config.toml: min_severity = "critical")
```

Alerts werden:
1. In `alerts.jsonl` im Run-Verzeichnis gespeichert
2. Im Terminal-Dashboard angezeigt
3. Mit farbiger Severity-Markierung dargestellt

---

## API-Beispiele

### Python-Client

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Health check
r = requests.get(f"{BASE_URL}/health")
assert r.json()["status"] == "ok"

# Runs auflisten
runs = requests.get(f"{BASE_URL}/runs").json()
print(f"Found {len(runs)} runs")

# Snapshot abrufen
if runs:
    run_id = runs[0]["run_id"]
    snapshot = requests.get(f"{BASE_URL}/runs/{run_id}/snapshot").json()
    print(f"Equity: {snapshot['equity']:.2f}")

    # Letzte 10 Events
    tail = requests.get(f"{BASE_URL}/runs/{run_id}/tail?limit=10").json()

    # Alerts
    alerts = requests.get(f"{BASE_URL}/runs/{run_id}/alerts").json()
    for alert in alerts:
        print(f"[{alert['severity']}] {alert['message']}")
```

### curl

```bash
# Health
curl http://127.0.0.1:8000/health

# Runs
curl http://127.0.0.1:8000/runs

# Snapshot
curl http://127.0.0.1:8000/runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m/snapshot

# Tail (letzte 10)
curl "http://127.0.0.1:8000/runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m/tail?limit=10"

# Alerts
curl http://127.0.0.1:8000/runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m/alerts
```

---

## Tests

```bash
# Alle Phase-34-Tests
pytest tests/test_live_alerts.py tests/test_live_web.py -v

# Nur Alert-Tests
pytest tests/test_live_alerts.py -v

# Nur Web-Tests
pytest tests/test_live_web.py -v
```

### Test-Coverage

- `test_live_alerts.py`:
  - Severity-Klasse und Ranking
  - AlertsConfig-Defaults und Custom-Werte
  - AlertRule-Dataclass
  - AlertEngine: Evaluation, Debouncing, Severity-Filter
  - File-I/O: append_alerts_to_file, load_alerts_from_file
  - render_alerts-Funktion

- `test_live_web.py`:
  - Health-Endpoint
  - Runs-Endpoint (Liste, leeres Verzeichnis)
  - Snapshot-Endpoint (Felder, Werte, 404)
  - Tail-Endpoint (Default, Limit, 404)
  - Alerts-Endpoint (Liste, Limit, leere Alerts)
  - Dashboard-Endpoint (HTML, JavaScript)
  - WebUIConfig (Defaults, Custom)
  - create_app Factory

---

## Dateien

### Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/live/alerts.py` | Alert-System (AlertEngine, AlertEvent, etc.) |
| `src/live/web/__init__.py` | Web-Package-Initialization |
| `src/live/web/app.py` | FastAPI-Anwendung mit Dashboard |
| `scripts/serve_live_dashboard.py` | CLI-Script zum Starten des Servers |
| `tests/test_live_alerts.py` | Alert-Tests |
| `tests/test_live_web.py` | Web-API-Tests |
| `docs/PHASE_34_ALERTS_AND_WEB_UI.md` | Diese Dokumentation |

### Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `config/config.toml` | `[alerts]` und `[web_ui]` Sektionen hinzugefügt |
| `scripts/monitor_live_run.py` | Alert-Integration |
| `src/live/__init__.py` | Alert-Exports hinzugefügt |
| `pyproject.toml` | `[web]` Optional-Dependency hinzugefügt |

---

## Sicherheitshinweise

1. **Lokaler Zugriff**: Default-Host ist `127.0.0.1` (nur lokaler Zugriff)
2. **Read-Only**: Die Web-UI kann keine Trading-Aktionen auslösen
3. **Keine Secrets**: Die API gibt keine sensiblen Daten (API-Keys, etc.) preis
4. **Production**: Für externen Zugriff einen Reverse-Proxy (nginx) mit Auth verwenden

---

## Nächste Schritte (Optional)

- WebSocket-Support für Live-Updates ohne Polling
- Grafana-Integration für erweiterte Visualisierung
- E-Mail/Telegram-Benachrichtigungen für kritische Alerts
- Historische Alert-Analyse und Statistiken
