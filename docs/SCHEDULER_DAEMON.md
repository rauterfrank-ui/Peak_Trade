# Peak_Trade: Scheduler & Job Runner

Der Scheduler ist ein leichtgewichtiger CLI-basierter Job-Runner für automatisierte Aufgaben.

---

## Konzept

### Warum ein eigener Scheduler?

Statt komplexe System-Daemons (cron, systemd) zu konfigurieren, bietet Peak_Trade einen **eingebauten Scheduler**:

1. **Portabel**: Funktioniert auf jedem System mit Python
2. **Deklarativ**: Jobs werden in TOML-Dateien definiert
3. **Integriert**: Arbeitet mit Registry & Notifications zusammen
4. **Testbar**: Dry-Run-Modus für Entwicklung und Debugging

### Architektur

```
config/scheduler/jobs.toml  →  run_scheduler.py  →  Registry + Alerts
         ↓                            ↓
    Job-Definitionen            Job-Ausführung
    (TOML-Format)              (subprocess)
```

---

## Installation & Quick Start

### 1. Scheduler im Dry-Run-Modus testen

```bash
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --dry-run --once
```

### 2. Alle fälligen Jobs einmal ausführen

```bash
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --once
```

### 3. Scheduler als Daemon starten

```bash
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --poll-interval 60
```

Der Scheduler läuft dann kontinuierlich und prüft alle 60 Sekunden auf fällige Jobs.

---

## CLI-Referenz: run_scheduler.py

### Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--config` | Pfad zur Job-Config (TOML) | `config/scheduler/jobs.toml` |
| `--poll-interval` | Prüfintervall in Sekunden | `30` |
| `--once` | Einmal ausführen, dann beenden | False |
| `--include-tags` | Nur Jobs mit diesen Tags (komma-sep.) | - |
| `--exclude-tags` | Jobs mit diesen Tags ausschließen | - |
| `--dry-run` | Keine echte Ausführung | False |
| `--verbose` | Debug-Output | False |
| `--no-registry` | Nicht in Registry loggen | False |
| `--no-alerts` | Keine Alerts senden | False |

### Beispiele

```bash
# Nur Forward-Signal-Jobs ausführen
python scripts/run_scheduler.py --include-tags forward --once

# Alle Jobs außer "heavy" ausführen
python scripts/run_scheduler.py --exclude-tags heavy --once

# Verbose Dry-Run
python scripts/run_scheduler.py --dry-run --verbose --once
```

---

## Job-Konfiguration (TOML)

Jobs werden in `config/scheduler/jobs.toml` definiert.

### Struktur

```toml
[[job]]
name = "daily_forward_btc"
description = "Generiert Forward-Signal für BTC/EUR"
command = "python"
args = { script = "scripts/run_forward_signals.py", strategy = "ma_crossover", symbol = "BTC/EUR" }
schedule_type = "daily"
daily_time = "07:30"
enabled = true
tags = ["forward", "daily", "prod"]
timeout_seconds = 120
```

### Felder

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `name` | string | Eindeutiger Job-Name |
| `description` | string | Optionale Beschreibung |
| `command` | string | Auszuführendes Kommando (default: `python`) |
| `args` | dict | Argumente (script + flags) |
| `schedule_type` | string | `once`, `interval`, `daily` |
| `interval_seconds` | int | Intervall für `schedule_type = "interval"` |
| `daily_time` | string | Uhrzeit für `schedule_type = "daily"` (HH:MM) |
| `enabled` | bool | Ob der Job aktiv ist |
| `tags` | list | Tags für Filterung |
| `timeout_seconds` | int | Timeout (default: 300) |
| `env` | dict | Zusätzliche Umgebungsvariablen |

### Schedule-Typen

#### `once`
Job wird einmal ausgeführt und dann nie wieder:

```toml
[[job]]
name = "initial_setup"
args = { script = "scripts/setup.py" }
schedule_type = "once"
```

#### `interval`
Job wird alle N Sekunden ausgeführt:

```toml
[[job]]
name = "hourly_risk_check"
args = { script = "scripts/check_live_risk_limits.py" }
schedule_type = "interval"
interval_seconds = 3600  # 1 Stunde
```

#### `daily`
Job wird täglich zu einer bestimmten Uhrzeit ausgeführt:

```toml
[[job]]
name = "morning_signals"
args = { script = "scripts/run_forward_signals.py" }
schedule_type = "daily"
daily_time = "07:30"
```

---

## Beispiel-Jobs

### Forward-Signals generieren

```toml
[[job]]
name = "daily_forward_signals_btc"
description = "BTC Forward-Signal täglich um 07:30"
command = "python"
args = { script = "scripts/run_forward_signals.py", strategy = "ma_crossover", symbol = "BTC/EUR", timeframe = "1h", bars = 200, tag = "daily-forward" }
schedule_type = "daily"
daily_time = "07:30"
enabled = true
tags = ["forward", "daily", "prod"]
timeout_seconds = 120
```

### Market-Scan

```toml
[[job]]
name = "weekly_market_scan"
description = "Wöchentlicher Market-Scan"
args = { script = "scripts/scan_markets.py", strategy = "ma_crossover", top_n = 10, tag = "weekly-scan" }
schedule_type = "interval"
interval_seconds = 604800  # 7 Tage
tags = ["scan", "weekly"]
```

### Risk-Check

```toml
[[job]]
name = "risk_check_hourly"
description = "Stündlicher Risk-Limit-Check"
args = { script = "scripts/check_live_risk_limits.py", config = "config/live_limits.toml" }
schedule_type = "interval"
interval_seconds = 3600
tags = ["risk", "hourly", "live"]
```

### Parameter-Sweep

```toml
[[job]]
name = "weekly_sweep_ma"
description = "Wöchentlicher Parameter-Sweep"
args = { script = "scripts/sweep_parameters.py", strategy = "ma_crossover", tag = "weekly-sweep" }
schedule_type = "interval"
interval_seconds = 604800
enabled = false  # Manuell aktivieren bei Bedarf
tags = ["sweep", "weekly", "heavy"]
```

---

## Integration

### Registry-Logging

Jede Job-Ausführung wird automatisch in der Experiment-Registry geloggt:

```python
# Automatisch durch run_scheduler.py
log_scheduler_job_run(
    job_name="daily_forward_btc",
    command="python",
    args={"script": "scripts/run_forward_signals.py", ...},
    return_code=0,
    started_at=...,
    finished_at=...,
    tag="scheduler",
)
```

Abfrage in der Registry:

```bash
python scripts/list_experiments.py --run-type scheduler_job
```

### Notifications

Bei Job-Ende werden Alerts gesendet:

- **Erfolg**: `level="info"`, `source="scheduler"`
- **Fehler**: `level="warning"` oder `level="critical"`

Konfiguriere Notifier in `.env` oder Konfigurationsdateien.

---

## Deployment-Optionen

### Option 1: Screen/tmux Session

```bash
# In einer Screen-Session
screen -S peak_scheduler
python scripts/run_scheduler.py --config config/scheduler/jobs.toml --poll-interval 60
# Ctrl+A, D zum Detachen
```

### Option 2: systemd Service (Linux)

Erstelle `/etc/systemd/system/peak_scheduler.service`:

```ini
[Unit]
Description=Peak_Trade Scheduler
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/path/to/Peak_Trade
ExecStart=/path/to/Peak_Trade/.venv/bin/python scripts/run_scheduler.py --config config/scheduler/jobs.toml --poll-interval 60
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable peak_scheduler
sudo systemctl start peak_scheduler
```

### Option 3: Cron als Trigger

Starte den Scheduler im `--once`-Modus via cron:

```cron
# Alle 5 Minuten prüfen
*/5 * * * * cd /path/to/Peak_Trade && .venv/bin/python scripts/run_scheduler.py --once
```

### Option 4: launchd (macOS)

Erstelle `~/Library/LaunchAgents/com.peaktrade.scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.peaktrade.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/Peak_Trade/.venv/bin/python</string>
        <string>/path/to/Peak_Trade/scripts/run_scheduler.py</string>
        <string>--config</string>
        <string>/path/to/Peak_Trade/config/scheduler/jobs.toml</string>
        <string>--poll-interval</string>
        <string>60</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/Peak_Trade</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.peaktrade.scheduler.plist
```

---

## Graceful Shutdown

Der Scheduler reagiert auf SIGINT (Ctrl+C) und SIGTERM:

1. Wartet auf laufenden Job (falls vorhanden)
2. Loggt finalen Status
3. Beendet sauber

```bash
# Graceful shutdown
kill -TERM $(pgrep -f run_scheduler.py)
```

---

## Troubleshooting

### "Job not executed"

1. Prüfe `enabled = true` in der Job-Config
2. Prüfe Schedule-Typ und -Zeit
3. Nutze `--verbose` für Debug-Output

```bash
python scripts/run_scheduler.py --dry-run --verbose --once
```

### "Config not found"

```bash
# Explizit Config angeben
python scripts/run_scheduler.py --config /absolute/path/to/jobs.toml
```

### "Job timeout"

Erhöhe `timeout_seconds` in der Job-Config oder prüfe, warum der Job so lange dauert.

### "Script not found"

Prüfe den `script`-Pfad in `args`. Pfade sind relativ zum Working Directory.

---

## API-Referenz

### Dataclasses

```python
from src.scheduler import JobSchedule, JobDefinition, JobResult

# Schedule
schedule = JobSchedule(
    type="daily",
    daily_time="07:30",
)

# Job-Definition
job = JobDefinition(
    name="my_job",
    args={"script": "scripts/my_script.py", "flag": True},
    schedule=schedule,
    tags=["prod"],
)

# Job-Ergebnis
result = JobResult(
    job_name="my_job",
    started_at=datetime.utcnow(),
    finished_at=datetime.utcnow(),
    return_code=0,
    success=True,
)
```

### Config Loader

```python
from src.scheduler import load_jobs_from_toml
from pathlib import Path

jobs = load_jobs_from_toml(Path("config/scheduler/jobs.toml"))
for job in jobs:
    print(f"{job.name}: {job.schedule.type}")
```

### Runner

```python
from src.scheduler import run_job, is_job_due, get_due_jobs

# Prüfen ob Job fällig
if is_job_due(job):
    result = run_job(job, dry_run=False)
    print(f"Success: {result.success}")

# Alle fälligen Jobs finden
due_jobs = get_due_jobs(jobs)
```

---

## Siehe auch

- [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md) - Schnellreferenz aller CLI-Befehle
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) - Live-Trading-Workflows
- [AUTO_PORTFOLIOS.md](AUTO_PORTFOLIOS.md) - Automatische Portfolio-Generierung
