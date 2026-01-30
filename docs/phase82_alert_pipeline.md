# Phase 82 – Alert-Pipeline (Slack/Mail) v1

## Übersicht

Phase 82 implementiert eine robuste, konfigurierbare **Alert-Pipeline**, die kritische Ereignisse im Live-/Shadow-/Testnet-Track automatisch an menschliche Operatoren meldet – primär über **Slack**, optional über **E-Mail**.

## Implementierte Komponenten

### 1. Domain-Model (`src/live/alert_pipeline.py`)

#### AlertSeverity (Enum)
```python
class AlertSeverity(IntEnum):
    INFO = 10      # Informativ, keine Aktion nötig
    WARN = 20      # Aufmerksamkeit erforderlich
    CRITICAL = 30  # Sofortige Aktion nötig
```

Mapping von Risk-Status:
- `GREEN` → `INFO`
- `YELLOW` → `WARN`
- `RED` → `CRITICAL`

#### AlertCategory (Enum)
```python
class AlertCategory(str, Enum):
    RISK = "RISK"           # Risk-Management-Events
    EXECUTION = "EXECUTION"  # Order-Pipeline-Events
    SYSTEM = "SYSTEM"        # System-Health-Events
```

#### AlertMessage (Dataclass)
```python
@dataclass
class AlertMessage:
    title: str                      # Kurzer Titel
    body: str                       # Detaillierte Beschreibung
    severity: AlertSeverity         # Dringlichkeit
    category: AlertCategory         # Kategorie für Routing
    source: str                     # Quelle (z.B. "live_risk_severity")
    session_id: Optional[str]       # Session-Kontext
    timestamp: datetime             # UTC-Zeitstempel
    context: Dict[str, Any]         # Zusätzliche Daten
```

### 2. Alert-Channels

#### SlackAlertChannel
- Incoming Webhook-basiert
- Strukturierte Slack-Blocks mit Severity-Farben
- Konfigurierbare Optionen: `channel`, `username`, `icon_emoji`
- Robuste Fehlerbehandlung (kein Crash bei Netzwerkfehlern)

#### EmailAlertChannel
- SMTP mit TLS/STARTTLS-Support
- HTML + Plain-Text E-Mails
- Passwort aus Environment-Variable (sicher)
- Empfohlen für CRITICAL-Alerts als Backup

#### NullAlertChannel
- No-Op-Channel für deaktivierte Alerts

### 3. AlertPipelineManager

Zentrale Routing-Komponente:
- Multi-Channel-Support
- Severity-basiertes Filtering pro Channel
- Robuste Fehlerbehandlung (Channel-Fehler blockieren nicht andere)

```python
from src.live.alert_pipeline import build_alert_pipeline_from_config

# Aus Config erstellen
manager = build_alert_pipeline_from_config(config)

# Alert senden
manager.send(alert)

# Convenience-Methoden
manager.send_risk_alert(title="...", body="...", severity=AlertSeverity.WARN, source="...")
```

### 4. SeverityTransitionTracker

Erkennt Risk-Severity-Übergänge und generiert automatisch Alerts:

```python
from src.live.alert_pipeline import SeverityTransitionTracker

tracker = SeverityTransitionTracker(manager)

# Bei jedem Risk-Check
tracker.update("green")   # Initial, kein Alert
tracker.update("yellow")  # → WARN Alert
tracker.update("red")     # → CRITICAL Alert
tracker.update("yellow")  # → Recovery Alert (optional)
```

**Transition-Mapping:**
| Von    | Nach   | Severity  | Pflicht |
|--------|--------|-----------|---------|
| GREEN  | YELLOW | WARN      | ✅       |
| YELLOW | RED    | CRITICAL  | ✅       |
| GREEN  | RED    | CRITICAL  | ✅       |
| RED    | YELLOW | WARN      | Optional |
| RED    | GREEN  | INFO      | Optional |

## Konfiguration

### config.toml

```toml
[alerts]
enabled = true
default_min_severity = "WARN"
send_recovery_alerts = true

[alerts.slack]
enabled = true
webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
min_severity = "WARN"
channel = "#peak-trade-alerts"
username = "peak-trade-bot"
icon_emoji = ":rotating_light:"
timeout_seconds = 5.0

[alerts.email]
enabled = false
min_severity = "CRITICAL"
smtp_host = "smtp.example.com"
smtp_port = 587
use_tls = true
username = "alerts@example.com"
password_env_var = "PEAK_TRADE_SMTP_PASSWORD"
from_addr = "alerts@example.com"
to_addrs = ["ops@example.com"]
timeout_seconds = 30.0
```

### Environment Variables

- `PEAK_TRADE_SMTP_PASSWORD`: SMTP-Passwort für Email-Channel

## Integration

### Mit Risk-Limits

```python
from src.live.alert_pipeline import build_alert_pipeline_from_config
from src.live.risk_alert_helpers import trigger_risk_pipeline_alert

# Pipeline erstellen
manager = build_alert_pipeline_from_config(config)

# Bei Risk-Check
result = limits.check_orders(orders)
trigger_risk_pipeline_alert(result, manager, session_id="sess_123")
```

### Severity-Transition-Tracking

```python
from src.live.alert_pipeline import SeverityTransitionTracker

# Tracker initialisieren
tracker = SeverityTransitionTracker(manager, send_recovery_alerts=True)

# Bei jedem Risk-Check
result = limits.evaluate_portfolio(snapshot)
tracker.update(result.risk_status, session_id=session_id, context=result.metrics)
```

## Tests

62 Unit-Tests in `tests/test_alert_pipeline.py`:

```bash
python3 -m pytest tests/test_alert_pipeline.py -v
```

**Akzeptanzkriterien (getestet):**
1. ✅ GREEN → YELLOW erzeugt WARN Alert
2. ✅ YELLOW → RED erzeugt CRITICAL Alert
3. ✅ Hard-Limit-Breach erzeugt CRITICAL Alert
4. ✅ Channel-spezifische min_severity wird respektiert
5. ✅ Globale Deaktivierung unterdrückt alle Alerts
6. ✅ Ungültige Config führt zu Log, nicht Crash

## Nächste Schritte (Folgephasen)

- **Phase 83:** Alert-Historie & Status im Web-Dashboard
- **Phase 84:** Incident-Runbook-Integration (verlinkte Runbooks)
- **Phase 85:** On-Call / Schedule-Integration

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/live/alert_pipeline.py` | Haupt-Modul mit allen Komponenten |
| `src/live/risk_alert_helpers.py` | Integration mit Risk-System |
| `src/live/__init__.py` | Exports für einfachen Import |
| `config/config.toml` | Konfigurationsbeispiel |
| `tests/test_alert_pipeline.py` | Unit-Tests |
| `docs/phase82_alert_pipeline.md` | Diese Dokumentation |
