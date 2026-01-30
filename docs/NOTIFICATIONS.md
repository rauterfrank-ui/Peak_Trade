# Peak_Trade Notification Layer

## Übersicht

Der Notification Layer ist ein leichtgewichtiges Alerting-System für Peak_Trade. Er verarbeitet Events aus verschiedenen Quellen und generiert daraus strukturierte Alerts.

**Hauptfunktionen:**
- Alerts mit Levels (INFO, WARNING, CRITICAL)
- Console- und Datei-Ausgabe
- Erweiterbare Architektur für E-Mail/Telegram/Webhook (zukünftig)
- Integration in Forward-Signals und Live-Risk-Checks

## Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Forward-Signals │    │  Live-Risk      │    │   Analytics     │
│     Script      │    │    Script       │    │    Script       │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                          ┌─────▼─────┐
                          │   Alert   │
                          │ Dataclass │
                          └─────┬─────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
              │  Console  │ │ File  │ │  Future   │
              │  Notifier │ │Notifier│ │ Notifiers │
              └───────────┘ └───────┘ └───────────┘
```

## Komponenten

### Alert (Dataclass)

```python
from src.notifications import Alert
from datetime import datetime

alert = Alert(
    level="warning",           # "info" | "warning" | "critical"
    source="forward_signal",   # Herkunft des Alerts
    message="BTC/EUR: LONG signal detected",
    timestamp=datetime.utcnow(),
    context={                  # Zusätzliche strukturierte Daten
        "symbol": "BTC/EUR",
        "strategy_key": "ma_crossover",
        "last_signal": 1.0,
    },
)
```

**Alert-Levels:**
| Level | Bedeutung | Beispiel |
|-------|-----------|----------|
| `info` | Normale Information | Signal berechnet, Check bestanden |
| `warning` | Aufmerksamkeit erforderlich | Starkes Signal, Analytics-Warnung |
| `critical` | Sofortige Aktion nötig | Risk-Verletzung, System-Fehler |

### ConsoleNotifier

Gibt Alerts auf stdout/stderr aus:

```python
from src.notifications import ConsoleNotifier

notifier = ConsoleNotifier(
    min_level="info",      # Mindest-Level für Ausgabe
    use_stderr=True,       # CRITICAL auf stderr
    show_context=False,    # Context mit ausgeben
)
notifier.send(alert)
```

**Ausgabe:**
```
[2025-01-01T12:00:00] [WARNING] [forward_signal] BTC/EUR: LONG signal detected
```

### FileNotifier

Schreibt Alerts in eine Logdatei:

```python
from pathlib import Path
from src.notifications import FileNotifier

notifier = FileNotifier(
    Path("logs/alerts.log"),
    min_level="info",      # Mindest-Level für Logging
    format="tsv",          # "tsv" oder "json"
)
notifier.send(alert)
```

**TSV-Format (Default):**
```
2025-01-01T12:00:00	warning	forward_signal	BTC/EUR: LONG signal detected
```

**JSON-Format (JSONL):**
```json
{"timestamp": "2025-01-01T12:00:00", "level": "warning", "source": "forward_signal", "message": "BTC/EUR: LONG signal detected", "context": {"symbol": "BTC/EUR"}}
```

### CombinedNotifier

Kombiniert mehrere Notifier:

```python
from src.notifications import CombinedNotifier, ConsoleNotifier, FileNotifier

notifier = CombinedNotifier([
    ConsoleNotifier(),
    FileNotifier(Path("logs/alerts.log")),
])
notifier.send(alert)  # Sendet an beide
```

## Integration

### Forward-Signals

`scripts/run_forward_signals.py` sendet automatisch Alerts nach der Signal-Berechnung:

```bash
# Mit Alerts (default)
python3 scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR

# Ohne Alerts
python3 scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR --no-alerts

# Eigene Alert-Logdatei
python3 scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR --alert-log logs/signals.log
```

**Alert-Beispiel (Forward-Signal):**
```
[2025-01-01T12:00:00] [WARNING] [forward_signal] ma_crossover on BTC/EUR (1h): LONG @ 43250.00
```

- `INFO`: Schwaches Signal (abs < 1)
- `WARNING`: Starkes Signal (abs >= 1, LONG oder SHORT)

### Live-Risk-Checks

`scripts/check_live_risk_limits.py` sendet Alerts bei Risk-Checks:

```bash
# Mit Alerts (default)
python3 scripts/check_live_risk_limits.py --orders orders.csv

# Ohne Alerts
python3 scripts/check_live_risk_limits.py --orders orders.csv --no-alerts
```

**Alert-Beispiele (Live-Risk):**

Bestanden:
```
[2025-01-01T12:00:00] [INFO] [live_risk] Live-Risk-Check bestanden: 3 Orders geprüft
```

Verletzung:
```
[2025-01-01T12:00:00] [CRITICAL] [live_risk] Live-Risk-Verletzung: max_order_notional exceeded, max_daily_loss exceeded
```

## Demo-Script

Zum Testen des Notification-Layers:

```bash
# Standard-Demo
python3 scripts/send_alerts_demo.py

# Nur Console-Ausgabe
python3 scripts/send_alerts_demo.py --console-only

# JSON-Format für Datei
python3 scripts/send_alerts_demo.py --json-format

# Eigene Logdatei
python3 scripts/send_alerts_demo.py --alert-log logs/demo_alerts.log
```

## Eigene Notifier implementieren

Das `Notifier`-Protocol definiert das Interface:

```python
from src.notifications.base import Alert, Notifier

class TelegramNotifier:
    """Beispiel: Eigener Notifier für Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, alert: Alert) -> None:
        # Telegram API aufrufen
        message = f"[{alert.level.upper()}] {alert.message}"
        # requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", ...)
        pass

# Verwendung mit CombinedNotifier
from src.notifications import CombinedNotifier, ConsoleNotifier

notifier = CombinedNotifier([
    ConsoleNotifier(),
    TelegramNotifier(bot_token="...", chat_id="..."),
])
```

## Helper-Funktionen

### create_alert()

Erstellt einen Alert mit automatischem Timestamp:

```python
from src.notifications.base import create_alert

alert = create_alert(
    level="warning",
    source="analytics",
    message="Sharpe Ratio negativ",
    context={"sharpe": -0.35},
)
```

### signal_level_from_value()

Bestimmt das Alert-Level basierend auf Signalstärke:

```python
from src.notifications.base import signal_level_from_value

level = signal_level_from_value(1.0)   # "warning"
level = signal_level_from_value(0.5)   # "info"
level = signal_level_from_value(-1.0)  # "warning"
```

## CLI-Optionen

Alle Scripts mit Alert-Integration unterstützen:

| Option | Beschreibung |
|--------|--------------|
| `--alert-log PATH` | Pfad zur Alert-Logdatei (Default: `logs/alerts.log`) |
| `--no-alerts` | Alert-Benachrichtigungen deaktivieren |

## Logdatei

Die Default-Logdatei ist `logs/alerts.log`. Sie wird automatisch erstellt und im Append-Modus geschrieben.

**Anzeigen:**
```bash
cat logs/alerts.log
tail -f logs/alerts.log  # Live-Monitoring
```

**Filtern (nur CRITICAL):**
```bash
grep "critical" logs/alerts.log
```

## Tests

```bash
python3 -m pytest tests/test_notifications_smoke.py -v
```

## Zukünftige Erweiterungen

- **E-Mail-Notifier**: Für tägliche Zusammenfassungen
- **Telegram-Notifier**: Für Echtzeit-Alerts
- **Webhook-Notifier**: Für Integration mit externen Systemen
- **Alert-Aggregation**: Mehrere ähnliche Alerts zusammenfassen
- **Alert-History**: Persistente Speicherung mit Abfrage-Funktionen
