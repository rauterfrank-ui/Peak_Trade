# Phase 49 – Live Alerts & Notifications

## Übersicht

Phase 49 implementiert ein **leichtgewichtiges, erweiterbares Alert-System** für Peak_Trade, das aus bestehenden Live-Komponenten **Warnungen und Alarme** generiert, sobald relevante Risk-Checks verletzt sind oder kritische Zustände auftreten.

**Wichtig:**
- Phase 49 bleibt **read-only** – keine Auto-Liquidation oder Auto-Stop.
- Alerts werden zunächst über **Logging / Konsole** ausgegeben, aber so designt, dass später **Slack/Webhook/Mail-Sinks** einfach ergänzt werden können.
- Alerts integrieren sich mit:
  - `LiveRiskLimits.check_orders(...)`
  - `LiveRiskLimits.evaluate_portfolio(...)`
  - CLI-Scripts (`preview_live_orders.py`, `preview_live_portfolio.py`)

---

## Architektur

### Komponenten-Übersicht

```
LiveRiskLimits.check_orders / evaluate_portfolio
    ↓ erzeugt LiveRiskCheckResult
    ↓ (bei Violation)
LiveAlerts (AlertEvent)
    ↓
AlertSink(s) → Logging / stderr / (später Slack/Webhook)
```

### Datenfluss

1. **LiveRiskLimits** führt Risk-Check durch
2. Bei Violation wird **AlertEvent** erzeugt
3. **AlertSink** sendet Alert an konfigurierte Sinks (Logging, stderr, etc.)
4. Alerts sind **nicht-blockierend** und dürfen den Live-Betrieb nicht stören

### Read-Only-Design

Phase 49 implementiert **keine**:
- Auto-Liquidation
- Auto-Stop
- Trade-Trigger

Alles ist **lesend** – Alerts informieren, der Operator behält die volle Kontrolle.

---

## Komponenten

### 1. `src/live/alerts.py`

#### AlertLevel (Enum)

```python
class AlertLevel(IntEnum):
    INFO = 10
    WARNING = 20
    CRITICAL = 30
```

#### AlertEvent (Dataclass)

```python
@dataclass
class AlertEvent:
    ts: datetime
    level: AlertLevel
    source: str          # z.B. "live_risk.orders", "live_risk.portfolio"
    code: str           # z.B. "RISK_LIMIT_VIOLATION_TOTAL_EXPOSURE"
    message: str        # Menschenlesbare Kurzbeschreibung
    context: Mapping[str, Any]  # Zusätzliche Kontext-Daten
```

#### AlertSink-Interface

```python
class AlertSink(Protocol):
    def send(self, alert: AlertEvent) -> None: ...
```

#### Standard-Sinks

- **LoggingAlertSink**: Sendet Alerts über Python-Logging
- **StderrAlertSink**: Sendet Alerts auf stderr
- **MultiAlertSink**: Leitet Alerts an mehrere Sinks weiter

#### LiveAlertsConfig

```python
@dataclass
class LiveAlertsConfig:
    enabled: bool = True
    min_level: AlertLevel = AlertLevel.WARNING
    sinks: list[str] = field(default_factory=lambda: ["log"])
    log_logger_name: str = "peak_trade.live.alerts"
```

### 2. Integration in `LiveRiskLimits`

**`LiveRiskLimits`** wurde erweitert um:
- Optionalen `alert_sink` Parameter im Konstruktor
- `_emit_risk_alert()` Methode für Alert-Generierung
- Automatische Alert-Emission bei Violations in:
  - `check_orders(...)`
  - `evaluate_portfolio(...)`

### 3. Integration in CLI-Scripts

- **`preview_live_portfolio.py`**: Lädt Alert-Config und injiziert Alert-Sink
- **`preview_live_orders.py`**: Nutzt `run_live_risk_check()`, das automatisch Alerts erzeugt

---

## Konfiguration

### Config-Beispiel (`config/config.toml`)

```toml
[live_alerts]
# Live Alerts & Notifications (Phase 49)
# ======================================
# Konfiguration für Alert-System bei Risk-Violations und kritischen Zuständen.
#
# enabled: Ob Alerts aktiviert sind
# min_level: Minimaler Alert-Level ("info", "warning", "critical")
# sinks: Liste der aktiven Sink-Namen (z.B. ["log", "stderr"])
# log_logger_name: Logger-Name für Logging-Sink
enabled = true
min_level = "warning"
sinks = ["log"]
log_logger_name = "peak_trade.live.alerts"
```

### Konfigurations-Optionen

| Option | Typ | Beschreibung |
|--------|-----|--------------|
| `enabled` | boolean | Ob Alerts aktiviert sind (Default: `true`) |
| `min_level` | string | Minimaler Alert-Level: `"info"`, `"warning"`, `"critical"` (Default: `"warning"`) |
| `sinks` | list[string] | Liste der aktiven Sink-Namen: `["log"]`, `["stderr"]`, `["log", "stderr"]` (Default: `["log"]`) |
| `log_logger_name` | string | Logger-Name für Logging-Sink (Default: `"peak_trade.live.alerts"`) |

### Alert-Level

- **INFO**: Informative Alerts (nur wenn `min_level = "info"`)
- **WARNING**: Warnungen (Default-Minimum)
- **CRITICAL**: Kritische Alerts (immer ausgegeben, außer `enabled = false`)

---

## Verwendung & Beispiele

### Beispiel 1: Order-Violation → Alert

```bash
# preview_live_orders.py mit Risk-Violation
python scripts/preview_live_orders.py \
  --signals reports/forward/..._signals.csv \
  --enforce-live-risk
```

**Log-Ausgabe:**
```
ERROR [peak_trade.live.alerts] [CRITICAL] live_risk.orders - RISK_LIMIT_VIOLATION_ORDERS: Live risk limit violation for proposed order batch. | context={'n_orders': 5, 'total_notional': 6000.0, ...}
```

### Beispiel 2: Portfolio-Violation → Alert

```bash
# preview_live_portfolio.py mit Portfolio-Violation
python scripts/preview_live_portfolio.py --config config/config.toml
```

**Log-Ausgabe:**
```
ERROR [peak_trade.live.alerts] [CRITICAL] live_risk.portfolio - RISK_LIMIT_VIOLATION_PORTFOLIO: Live risk limit violation for current portfolio snapshot. | context={'as_of': '2025-12-07T12:34:56', 'total_notional': 6000.0, ...}
```

### Beispiel 3: Stderr-Ausgabe

```toml
[live_alerts]
enabled = true
min_level = "warning"
sinks = ["stderr"]
```

**Stderr-Ausgabe:**
```
[2025-12-07T12:34:56.123456+00:00] [CRITICAL] live_risk.orders - RISK_LIMIT_VIOLATION_ORDERS: Live risk limit violation for proposed order batch. | context={'n_orders': 5, ...}
```

### Beispiel 4: Alerts deaktivieren

```toml
[live_alerts]
enabled = false
```

→ Keine Alerts werden erzeugt, auch bei Violations.

---

## Python-API

### Alert-Sink erstellen

```python
from src.live.alerts import LiveAlertsConfig, build_alert_sink_from_config

# Config aus PeakConfig laden
live_alerts_raw = cfg.get("live_alerts", {})
alerts_cfg = LiveAlertsConfig.from_dict(live_alerts_raw)
alert_sink = build_alert_sink_from_config(alerts_cfg)
```

### Alert manuell senden

```python
from src.live.alerts import AlertEvent, AlertLevel
from datetime import datetime, timezone

alert = AlertEvent(
    ts=datetime.now(timezone.utc),
    level=AlertLevel.WARNING,
    source="custom.source",
    code="CUSTOM_ALERT",
    message="Custom alert message",
    context={"key": "value"},
)

if alert_sink:
    alert_sink.send(alert)
```

### LiveRiskLimits mit Alert-Sink

```python
from src.live.risk_limits import LiveRiskLimits
from src.live.alerts import build_alert_sink_from_config, LiveAlertsConfig

# Alert-Sink erstellen
alerts_cfg = LiveAlertsConfig.from_dict(cfg.get("live_alerts", {}))
alert_sink = build_alert_sink_from_config(alerts_cfg)

# LiveRiskLimits mit Alert-Sink
risk_limits = LiveRiskLimits.from_config(
    cfg,
    starting_cash=10000.0,
    alert_sink=alert_sink,
)

# Bei Violation wird automatisch Alert erzeugt
result = risk_limits.check_orders(orders)
# → Alert wird automatisch gesendet, falls result.allowed == False
```

---

## Alert-Codes

### Order-Risk-Alerts

- **`RISK_LIMIT_VIOLATION_ORDERS`**: Risk-Limit-Verletzung bei Order-Batch

### Portfolio-Risk-Alerts

- **`RISK_LIMIT_VIOLATION_PORTFOLIO`**: Risk-Limit-Verletzung bei Portfolio-Snapshot

### Alert-Sources

- **`live_risk.orders`**: Alerts von Order-Risk-Checks
- **`live_risk.portfolio`**: Alerts von Portfolio-Risk-Checks

---

## Limitierungen & Future Work

### Aktuelle Limitierungen

1. **Nur Logging/stderr**: Keine externen Notification-Channels (Slack/Webhook/Mail)
2. **Keine Deduplizierung**: Jede Violation erzeugt einen Alert (auch bei wiederholten Violations)
3. **Kein Throttling**: Keine Rate-Limiting für Alerts
4. **Keine persistente Historie**: Alerts werden nicht in einer Datenbank gespeichert

### Mögliche Erweiterungen (zukünftige Phasen)

1. **Externe Notification-Sinks**:
   - Slack-Webhook-Sink
   - E-Mail-Sink (SMTP)
   - Discord-Webhook-Sink
   - PagerDuty-Integration

2. **Alert-Deduplizierung**:
   - Gleiche Alerts innerhalb eines Zeitfensters zusammenfassen
   - "N+1 Alerts in den letzten 5 Minuten" → ein Summary-Alert

3. **Alert-Throttling**:
   - Max. N Alerts pro Minute
   - Exponential-Backoff bei wiederholten Violations

4. **Persistente Alert-Historie**:
   - Alerts in Datenbank speichern
   - Alert-Query-API
   - Alert-Dashboard

5. **Alert-Filtering**:
   - Filter nach Source, Code, Level
   - Custom-Filter-Regeln

---

## Integration in bestehende Workflows

### Vor Live-Start

```bash
# Alerts konfigurieren
# → config/config.toml: [live_alerts] Block prüfen

# Test mit Portfolio-Monitoring
python scripts/preview_live_portfolio.py --config config/config.toml
# → Prüfe Logs auf Alerts
```

### Während Live-Trading

```bash
# Regelmäßig Portfolio-Status checken
python scripts/preview_live_portfolio.py --config config/config.toml
# → Alerts werden automatisch bei Violations erzeugt

# Order-Preview mit Risk-Check
python scripts/preview_live_orders.py \
  --signals reports/forward/..._signals.csv \
  --enforce-live-risk
# → Alerts werden automatisch bei Violations erzeugt
```

### Incident-Handling

Bei einem Incident:
1. **Logs prüfen**: Suche nach `[CRITICAL]` oder `[WARNING]` Alerts
2. **Alert-Context analysieren**: Welche Limits sind verletzt?
3. **Entscheidung treffen**: Manuell Positionen schließen oder warten

---

## Tests

### Unit-Tests

```bash
# Alert-System Tests
pytest tests/test_live_alerts.py -v

# Risk-Alert-Integration Tests
pytest tests/test_live_risk_alert_integration.py -v
```

### Integration-Tests

```bash
# Alle Alert-Tests
pytest tests/test_live_alerts*.py -v
```

---

## Siehe auch

- `docs/PHASE_48_LIVE_PORTFOLIO_MONITORING_AND_RISK_BRIDGE.md` - Portfolio-Monitoring
- `docs/PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md` - Webhook & Slack-Sinks (Phase 50)
- `src/live/risk_limits.py` - Live-Risk-Limits-Dokumentation
- `src/live/alerts.py` - Alert-System-Implementierung
- `config/config.toml` - Alert-Konfiguration

---

## Phase 50: Webhook & Slack-Sinks

Phase 50 erweitert das Alert-System um externe Notification-Sinks:
- **Generische HTTP-Webhooks** für beliebige Endpunkte
- **Slack-Webhooks** für direkte Benachrichtigungen in Slack-Kanäle

Siehe [PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md](PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md) für Details.

---

**Built with ❤️ and safety-first alerting**
