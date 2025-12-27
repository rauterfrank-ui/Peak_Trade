# Peak_Trade Risk-Layer — Production Alerting Roadmap

**Datum:** 2025-12-27  
**Status:** 📋 ROADMAP READY  
**Projekt:** Peak_Trade Risk-Layer Modernisierung  
**Verantwortlich:** Peak_Risk (Chief Risk Officer)

---

## 🎯 Ziel

Implementierung eines robusten, mehrstufigen Alerting-Systems für den Risk-Layer, das:
- **Frühwarnung** bei Risiko-Schwellenwerten liefert
- **Eskalation** bei kritischen Events automatisiert
- **Audit-Trail** für Compliance und Post-Mortem-Analyse bereitstellt
- **Defense-in-Depth** Prinzipien unterstützt (4-Layer-Architektur)

---

## 📊 Phasen-Übersicht

| Phase | Name | Dauer | Priorität | Status |
|-------|------|-------|-----------|--------|
| **1** | Foundation & Alert Framework | 1 Woche | 🔴 Critical | ⬜ TODO |
| **2** | Risk Threshold Alerts | 1-2 Wochen | 🔴 Critical | ⬜ TODO |
| **3** | Notification Channels | 1 Woche | 🟡 High | ⬜ TODO |
| **4** | Escalation & Severity Tiers | 1 Woche | 🟡 High | ⬜ TODO |
| **5** | Audit Logging & Compliance | 1 Woche | 🟡 High | ⬜ TODO |
| **6** | Dashboard & Visualization | 1-2 Wochen | 🟢 Medium | ⬜ TODO |
| **7** | Integration Testing & Hardening | 1 Woche | 🔴 Critical | ⬜ TODO |

**Gesamt:** 7-10 Wochen

---

## 📦 Phase 1: Foundation & Alert Framework

**Ziel:** Basis-Infrastruktur für das Alerting-System aufbauen.

### Deliverables

```
src/risk/alerting/
├── __init__.py                    # Zentrale Exports
├── alert_types.py                 # Alert-Enums, Severity-Levels
├── alert_event.py                 # AlertEvent Dataclass
├── alert_manager.py               # Zentrale Alert-Verwaltung
├── alert_dispatcher.py            # Routing zu Channels
└── alert_config.py                # Config-Loading aus TOML

config/
└── alerting.toml                  # Alerting-Konfiguration

tests/risk/alerting/
├── test_alert_types.py
├── test_alert_event.py
└── test_alert_manager.py
```

### Akzeptanzkriterien

- [ ] `AlertEvent` Dataclass mit: `id`, `timestamp`, `severity`, `category`, `message`, `context`, `acknowledged`
- [ ] Severity-Levels: `DEBUG`, `INFO`, `WARNING`, `CRITICAL`, `EMERGENCY`
- [ ] Alert-Kategorien: `POSITION`, `PORTFOLIO`, `DRAWDOWN`, `EXECUTION`, `SYSTEM`
- [ ] `AlertManager` kann Events registrieren, filtern und dispatchen
- [ ] Config-driven: Alle Schwellenwerte aus `alerting.toml`
- [ ] 100% Unit-Test-Coverage für Core-Module
- [ ] Dokumentation: `docs/risk/ALERTING_ARCHITECTURE.md`

### Code-Struktur

```python
# src/risk/alerting/alert_event.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid

class AlertSeverity(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    CRITICAL = 3
    EMERGENCY = 4

class AlertCategory(Enum):
    POSITION = "position"
    PORTFOLIO = "portfolio"
    DRAWDOWN = "drawdown"
    EXECUTION = "execution"
    SYSTEM = "system"
    KILL_SWITCH = "kill_switch"

@dataclass
class AlertEvent:
    severity: AlertSeverity
    category: AlertCategory
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
```

### Config-Template

```toml
# config/alerting.toml
[alerting]
enabled = true
default_severity = "WARNING"

[alerting.retention]
days = 90
max_events = 100000

[alerting.deduplication]
enabled = true
window_seconds = 60
```

### Risiken & Mitigationen

| Risiko | Mitigation |
|--------|------------|
| Alert-Flooding | Deduplication + Rate-Limiting implementieren |
| Config-Fehler | Schema-Validation + Default-Values |
| Performance-Impact | Async-Dispatch, Batching für High-Volume |

---

## 📦 Phase 2: Risk Threshold Alerts

**Ziel:** Konkrete Risk-Metriken mit Alert-Schwellenwerten verbinden.

### Deliverables

```
src/risk/alerting/
├── threshold_monitor.py           # Überwacht Risk-Metriken
├── thresholds/
│   ├── __init__.py
│   ├── position_thresholds.py     # Positions-bezogene Alerts
│   ├── portfolio_thresholds.py    # Portfolio-Level Alerts
│   ├── drawdown_thresholds.py     # Drawdown-Monitoring
│   └── var_thresholds.py          # VaR/CVaR Breach Alerts

tests/risk/alerting/thresholds/
├── test_position_thresholds.py
├── test_portfolio_thresholds.py
└── test_drawdown_thresholds.py
```

### Alert-Definitionen

#### Layer 1: Pre-Trade Validation Alerts

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| `POSITION_SIZE_WARNING` | Position > 80% Max | WARNING | Log + Notify |
| `POSITION_SIZE_BREACH` | Position > 100% Max | CRITICAL | Block Trade |
| `ASSET_CONCENTRATION_HIGH` | Asset > 25% Portfolio | WARNING | Notify |
| `ASSET_CONCENTRATION_BREACH` | Asset > 40% Portfolio | CRITICAL | Block Trade |

#### Layer 2: Position Risk Alerts

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| `STOP_LOSS_TRIGGERED` | Price hits SL | INFO | Log + Execute SL |
| `TAKE_PROFIT_TRIGGERED` | Price hits TP | INFO | Log + Execute TP |
| `POSITION_LOSS_WARNING` | Unrealized Loss > 5% | WARNING | Notify |
| `POSITION_LOSS_CRITICAL` | Unrealized Loss > 10% | CRITICAL | Force Close Review |

#### Layer 3: Portfolio Risk Alerts

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| `DAILY_LOSS_WARNING` | Daily PnL < -2% | WARNING | Notify + Review |
| `DAILY_LOSS_BREACH` | Daily PnL < -5% | CRITICAL | Reduce Exposure |
| `VAR_BREACH_WARNING` | VaR > 80% Limit | WARNING | Notify |
| `VAR_BREACH_CRITICAL` | VaR > 100% Limit | CRITICAL | Emergency Reduce |
| `DRAWDOWN_WARNING` | DD > 10% | WARNING | Notify |
| `DRAWDOWN_CRITICAL` | DD > 15% | CRITICAL | Halt New Trades |
| `DRAWDOWN_EMERGENCY` | DD > 20% | EMERGENCY | Kill Switch |

#### Layer 4: Kill Switch Alerts

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| `KILL_SWITCH_TRIGGERED` | Manual oder Auto | EMERGENCY | Close All + Notify All Channels |
| `KILL_SWITCH_ARMED` | System ready | INFO | Log |
| `KILL_SWITCH_DISARMED` | Manual override | WARNING | Log + Require Confirmation |

### Config-Template

```toml
# config/alerting.toml (erweitert)

[alerting.thresholds.position]
max_size_warning_pct = 80
max_size_breach_pct = 100
loss_warning_pct = 5
loss_critical_pct = 10

[alerting.thresholds.portfolio]
daily_loss_warning_pct = 2
daily_loss_breach_pct = 5
var_warning_pct = 80
var_breach_pct = 100
max_drawdown_warning_pct = 10
max_drawdown_critical_pct = 15
max_drawdown_emergency_pct = 20

[alerting.thresholds.concentration]
single_asset_warning_pct = 25
single_asset_breach_pct = 40
sector_warning_pct = 50
sector_breach_pct = 70
```

### Akzeptanzkriterien

- [ ] Alle 4 Defense-Layers haben definierte Alert-Typen
- [ ] Threshold-Werte 100% config-driven (keine Hard-Codes)
- [ ] `ThresholdMonitor` prüft kontinuierlich alle Metriken
- [ ] Jeder Alert hat klare Severity + Action-Mapping
- [ ] Unit-Tests für jeden Threshold-Typ
- [ ] Integration-Test: Backtest-Run triggert erwartete Alerts

---

## 📦 Phase 3: Notification Channels

**Ziel:** Multi-Channel Alerting mit Fallback-Logik.

### Deliverables

```
src/risk/alerting/channels/
├── __init__.py
├── base_channel.py                # Abstract Base Class
├── console_channel.py             # Stdout/Stderr (Default)
├── file_channel.py                # JSON/CSV Logging
├── email_channel.py               # SMTP Email
├── slack_channel.py               # Slack Webhook
├── telegram_channel.py            # Telegram Bot
├── webhook_channel.py             # Generic HTTP Webhook
└── channel_router.py              # Severity → Channel Mapping

tests/risk/alerting/channels/
├── test_console_channel.py
├── test_file_channel.py
├── test_channel_router.py
└── conftest.py                    # Mock-Fixtures
```

### Channel-Severity-Matrix

| Severity | Console | File | Email | Slack | Telegram |
|----------|---------|------|-------|-------|----------|
| DEBUG | ✅ | ✅ | ❌ | ❌ | ❌ |
| INFO | ✅ | ✅ | ❌ | ❌ | ❌ |
| WARNING | ✅ | ✅ | ❌ | ✅ | ❌ |
| CRITICAL | ✅ | ✅ | ✅ | ✅ | ✅ |
| EMERGENCY | ✅ | ✅ | ✅ | ✅ | ✅ |

### Config-Template

```toml
# config/alerting.toml (erweitert)

[alerting.channels.console]
enabled = true
min_severity = "DEBUG"
format = "structured"  # "simple" | "structured" | "json"

[alerting.channels.file]
enabled = true
min_severity = "INFO"
path = "logs/alerts/"
format = "jsonl"
rotation = "daily"
retention_days = 90

[alerting.channels.email]
enabled = false  # Erst bei Testnet aktivieren
min_severity = "CRITICAL"
smtp_host = "${SMTP_HOST}"
smtp_port = 587
from_address = "alerts@peak-trade.local"
to_addresses = ["operator@example.com"]
use_tls = true

[alerting.channels.slack]
enabled = false  # Erst bei Testnet aktivieren
min_severity = "WARNING"
webhook_url = "${SLACK_WEBHOOK_URL}"
channel = "#peak-trade-alerts"
mention_on_critical = ["@channel"]

[alerting.channels.telegram]
enabled = false  # Erst bei Testnet aktivieren
min_severity = "CRITICAL"
bot_token = "${TELEGRAM_BOT_TOKEN}"
chat_id = "${TELEGRAM_CHAT_ID}"
```

### Code-Struktur

```python
# src/risk/alerting/channels/base_channel.py
from abc import ABC, abstractmethod
from ..alert_event import AlertEvent, AlertSeverity

class AlertChannel(ABC):
    """Abstract Base Class für Alert-Channels."""

    def __init__(self, config: dict, min_severity: AlertSeverity):
        self.config = config
        self.min_severity = min_severity
        self._enabled = config.get("enabled", True)

    def should_send(self, event: AlertEvent) -> bool:
        """Prüft ob Event an diesen Channel gesendet werden soll."""
        if not self._enabled:
            return False
        return event.severity.value >= self.min_severity.value

    @abstractmethod
    async def send(self, event: AlertEvent) -> bool:
        """Sendet Alert an Channel. Returns True bei Erfolg."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Prüft ob Channel erreichbar ist."""
        pass
```

### Akzeptanzkriterien

- [ ] Mindestens 5 Channels implementiert (Console, File, Email, Slack, Telegram)
- [ ] Severity-basiertes Routing funktioniert
- [ ] Fallback-Logik: Wenn Channel X failed → Channel Y
- [ ] Async-Dispatch: Alerting blockiert nicht den Haupt-Thread
- [ ] Secrets via Environment-Variables (NIEMALS im Config-File)
- [ ] Health-Check für jeden Channel
- [ ] Mock-Tests für externe Channels (kein echter SMTP/Slack in Tests)

### Sicherheitshinweise ⚠️

```
CRITICAL: Secrets-Handling

1. NIEMALS Secrets in config.toml speichern
2. Nutze Environment-Variables: ${SLACK_WEBHOOK_URL}
3. .env File für lokale Entwicklung (in .gitignore!)
4. In CI/CD: GitHub Secrets oder Vault
5. Logging: NIEMALS Secrets loggen (auch nicht partial)
```

---

## 📦 Phase 4: Escalation & Severity Tiers

**Ziel:** Automatische Eskalation bei anhaltenden oder sich verschlechternden Alerts.

### Deliverables

```
src/risk/alerting/
├── escalation_engine.py           # Eskalations-Logik
├── escalation_rules.py            # Rule Definitions
├── escalation_state.py            # State Management
└── cooldown_manager.py            # Prevents Alert-Spam

tests/risk/alerting/
├── test_escalation_engine.py
├── test_escalation_rules.py
└── test_cooldown_manager.py
```

### Eskalations-Regeln

#### Zeit-basierte Eskalation

```
Regel: UNACKNOWLEDGED_ESCALATION
─────────────────────────────────
Wenn: Alert mit Severity >= WARNING
      UND Alert nicht acknowledged
      UND Zeit seit Alert > X Minuten

Dann:
  - Nach 5 min: Severity +1 (WARNING → CRITICAL)
  - Nach 15 min: Severity +1 (CRITICAL → EMERGENCY)
  - Nach 30 min: Kill Switch Evaluation
```

#### Häufigkeits-basierte Eskalation

```
Regel: FREQUENCY_ESCALATION
───────────────────────────
Wenn: Gleicher Alert-Typ
      UND > N Occurrences in X Minuten

Dann:
  - 3x in 5 min: Severity +1
  - 5x in 10 min: Severity +2, Deduplicate
  - 10x in 15 min: Meta-Alert "Alert Storm", Kill Switch Review
```

#### Threshold-basierte Eskalation

```
Regel: THRESHOLD_ESCALATION
───────────────────────────
Wenn: Metrik verschlechtert sich kontinuierlich
      z.B. Drawdown: 10% → 12% → 14% in 1h

Dann:
  - Trend-Alert mit Projektion
  - Severity basierend auf Geschwindigkeit
  - Proaktive Maßnahmen empfehlen
```

### Config-Template

```toml
# config/alerting.toml (erweitert)

[alerting.escalation]
enabled = true

[alerting.escalation.time_based]
enabled = true
warning_to_critical_minutes = 5
critical_to_emergency_minutes = 15
emergency_kill_switch_minutes = 30

[alerting.escalation.frequency_based]
enabled = true
window_minutes = 15
escalate_at_count = 3
deduplicate_at_count = 5
storm_alert_at_count = 10

[alerting.escalation.threshold_based]
enabled = true
trend_window_minutes = 60
min_datapoints = 3

[alerting.cooldown]
enabled = true
default_seconds = 60
per_category = { position = 30, portfolio = 120, system = 300 }
```

### State Machine

```
┌──────────────────────────────────────────────────────────┐
│                    Alert Lifecycle                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────┐    ┌─────────────┐    ┌──────────────┐   │
│   │ CREATED │───▶│ DISPATCHED  │───▶│ ACKNOWLEDGED │   │
│   └─────────┘    └─────────────┘    └──────────────┘   │
│        │              │                    │            │
│        │              │ (timeout)          │            │
│        │              ▼                    ▼            │
│        │         ┌──────────┐      ┌───────────┐       │
│        │         │ ESCALATED│      │ RESOLVED  │       │
│        │         └──────────┘      └───────────┘       │
│        │              │                    │            │
│        │              │ (timeout)          │            │
│        │              ▼                    │            │
│        │         ┌───────────┐             │            │
│        └────────▶│ EXPIRED   │◀────────────┘            │
│                  └───────────┘                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Akzeptanzkriterien

- [ ] 3 Eskalations-Typen implementiert (Zeit, Häufigkeit, Threshold)
- [ ] Cooldown verhindert Alert-Spam (config-driven)
- [ ] Eskalation führt zu Channel-Erweiterung (z.B. + Telegram bei CRITICAL)
- [ ] State-Tracking für jeden Alert (Lifecycle)
- [ ] Manuelle Acknowledgement-Funktion
- [ ] Auto-Resolve bei Metrik-Normalisierung
- [ ] Integration-Test: Simulierte Eskalations-Szenarien

---

## 📦 Phase 5: Audit Logging & Compliance

**Ziel:** Vollständiger, unveränderlicher Audit-Trail für alle Risk-Events.

### Deliverables

```
src/risk/alerting/audit/
├── __init__.py
├── audit_logger.py                # Hauptklasse
├── audit_event.py                 # Audit-Event Dataclass
├── audit_storage.py               # Storage Backend (SQLite/File)
├── audit_query.py                 # Query-Interface
└── audit_export.py                # Export für Compliance

tests/risk/alerting/audit/
├── test_audit_logger.py
├── test_audit_storage.py
└── test_audit_export.py

docs/risk/
└── AUDIT_COMPLIANCE.md            # Compliance-Dokumentation
```

### Audit-Event-Struktur

```python
@dataclass
class AuditEvent:
    """Unveränderlicher Audit-Eintrag."""

    # Identifikation
    id: str                         # UUID
    timestamp: datetime             # UTC, ISO-8601

    # Event-Details
    event_type: AuditEventType      # ALERT_CREATED, TRADE_BLOCKED, etc.
    severity: AlertSeverity
    category: AlertCategory

    # Kontext
    alert_id: str | None            # Referenz auf Alert
    trade_id: str | None            # Referenz auf Trade
    position_id: str | None         # Referenz auf Position

    # Details
    message: str
    details: dict[str, Any]

    # Aktion
    action_taken: str               # "BLOCKED", "NOTIFIED", "ESCALATED"
    action_reason: str

    # Actor
    actor_type: str                 # "SYSTEM", "USER", "KILL_SWITCH"
    actor_id: str | None

    # Integrität
    checksum: str                   # SHA-256 des Events
    previous_checksum: str | None   # Chain für Integrität
```

### Audit-Event-Typen

| Event Type | Beschreibung | Retention |
|------------|--------------|-----------|
| `ALERT_CREATED` | Neuer Alert | 90 Tage |
| `ALERT_ESCALATED` | Severity erhöht | 90 Tage |
| `ALERT_ACKNOWLEDGED` | Manuell bestätigt | 90 Tage |
| `ALERT_RESOLVED` | Alert aufgelöst | 90 Tage |
| `TRADE_BLOCKED` | Trade durch Risk abgelehnt | 1 Jahr |
| `POSITION_FORCE_CLOSED` | Zwangsschließung | 1 Jahr |
| `KILL_SWITCH_ACTIVATED` | Notfall-Stop | Permanent |
| `KILL_SWITCH_DEACTIVATED` | Notfall-Stop aufgehoben | Permanent |
| `CONFIG_CHANGED` | Risk-Config geändert | 1 Jahr |
| `THRESHOLD_BREACHED` | Schwellenwert überschritten | 90 Tage |

### Config-Template

```toml
# config/alerting.toml (erweitert)

[alerting.audit]
enabled = true
storage_backend = "sqlite"  # "sqlite" | "file" | "postgres"
database_path = "data/audit/audit.db"

[alerting.audit.retention]
default_days = 90
trade_blocked_days = 365
kill_switch_days = -1  # Permanent

[alerting.audit.integrity]
checksum_algorithm = "sha256"
chain_validation = true
validate_on_read = true

[alerting.audit.export]
formats = ["json", "csv"]
compress = true
encrypt = false  # Optional für Compliance
```

### Compliance-Report-Template

```markdown
# Peak_Trade Risk Audit Report

**Period:** 2025-01-01 to 2025-01-31
**Generated:** 2025-02-01T00:00:00Z

## Summary

| Metric | Value |
|--------|-------|
| Total Alerts | 1,234 |
| Critical Alerts | 45 |
| Emergency Alerts | 2 |
| Trades Blocked | 23 |
| Kill Switch Activations | 0 |

## Alert Distribution

| Category | Count | % |
|----------|-------|---|
| Position | 456 | 37% |
| Portfolio | 321 | 26% |
| Drawdown | 234 | 19% |
| Execution | 123 | 10% |
| System | 100 | 8% |

## Risk Breaches

[Detailed list of threshold breaches...]

## Audit Trail Integrity

✅ Chain validation: PASSED
✅ Checksum validation: PASSED
✅ No gaps detected
```

### Akzeptanzkriterien

- [ ] Jedes Risk-Event wird geloggt (keine Ausnahmen)
- [ ] Audit-Events sind unveränderlich (Append-Only)
- [ ] Checksum-Chain für Integritätsprüfung
- [ ] Retention-Policies automatisch enforced
- [ ] Export in JSON und CSV
- [ ] Query-Interface für Analyse
- [ ] Compliance-Report-Generator
- [ ] Backup-Strategie dokumentiert

---

## 📦 Phase 6: Dashboard & Visualization

**Ziel:** Real-Time Monitoring Dashboard für Risk-Alerts.

### Deliverables

```
src/risk/alerting/dashboard/
├── __init__.py
├── dashboard_server.py            # FastAPI/Flask Server
├── dashboard_api.py               # REST API Endpoints
├── websocket_handler.py           # Real-Time Updates
└── templates/
    └── dashboard.html             # HTML Template

src/risk/alerting/dashboard/static/
├── css/
│   └── dashboard.css
├── js/
│   └── dashboard.js
└── img/
    └── peak_trade_logo.svg

tests/risk/alerting/dashboard/
├── test_dashboard_api.py
└── test_websocket_handler.py
```

### Dashboard-Komponenten

```
┌──────────────────────────────────────────────────────────────────┐
│                    Peak_Trade Risk Dashboard                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  System Status  │  │  Active Alerts  │  │  Kill Switch    │  │
│  │  🟢 HEALTHY     │  │     12 ⚠️       │  │  🔴 ARMED       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    Alert Timeline                          │   │
│  │  ──●──────●────●─────────●──────●────●──────────▶ time    │   │
│  │    ⚠️      ⚠️    🔴       ⚠️      ⚠️    ⚠️               │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐   │
│  │    Current Metrics      │  │    Alert Distribution       │   │
│  │                         │  │                             │   │
│  │  Portfolio DD: 8.5%     │  │  Position:  ████░░ 45%      │   │
│  │  Daily PnL:   -1.2%     │  │  Portfolio: ███░░░ 30%      │   │
│  │  VaR Usage:   65%       │  │  Drawdown:  ██░░░░ 15%      │   │
│  │  Open Pos:    5         │  │  System:    █░░░░░ 10%      │   │
│  └─────────────────────────┘  └─────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    Recent Alerts                           │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │  🔴 14:32:15  CRITICAL  Drawdown exceeded 15%             │   │
│  │  ⚠️  14:28:03  WARNING   VaR usage at 80%                 │   │
│  │  ⚠️  14:15:22  WARNING   Position BTC/EUR loss > 5%       │   │
│  │  ℹ️  14:00:00  INFO      Daily reset completed            │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### API-Endpoints

```
GET  /api/v1/alerts                    # Liste aller Alerts (paginated)
GET  /api/v1/alerts/{id}               # Einzelner Alert
POST /api/v1/alerts/{id}/acknowledge   # Alert bestätigen
GET  /api/v1/alerts/stats              # Statistiken

GET  /api/v1/metrics/current           # Aktuelle Risk-Metriken
GET  /api/v1/metrics/history           # Historische Metriken

GET  /api/v1/system/status             # System-Status
POST /api/v1/system/kill-switch        # Kill Switch aktivieren (!)

WS   /ws/alerts                        # Real-Time Alert Stream
WS   /ws/metrics                       # Real-Time Metrik Updates
```

### Config-Template

```toml
# config/alerting.toml (erweitert)

[alerting.dashboard]
enabled = false  # Erst bei Shadow Trading aktivieren
host = "127.0.0.1"  # Nur localhost!
port = 8080
debug = false

[alerting.dashboard.auth]
enabled = true
type = "basic"  # "basic" | "token" | "oauth"
username = "${DASHBOARD_USER}"
password = "${DASHBOARD_PASSWORD}"

[alerting.dashboard.websocket]
enabled = true
max_connections = 10
heartbeat_seconds = 30

[alerting.dashboard.api]
rate_limit_per_minute = 60
cors_origins = ["http://localhost:3000"]
```

### Akzeptanzkriterien

- [ ] REST API für Alert-Management
- [ ] WebSocket für Real-Time Updates
- [ ] Responsive HTML Dashboard
- [ ] Auth-Protection (Basic Auth minimum)
- [ ] Rate-Limiting für API
- [ ] CORS-Konfiguration
- [ ] Nur localhost per Default (Sicherheit!)
- [ ] Kill-Switch-Button mit Confirmation-Dialog
- [ ] Integration-Tests für alle Endpoints

### Sicherheitshinweise ⚠️

```
CRITICAL: Dashboard Security

1. Default: Nur localhost binding (127.0.0.1)
2. Auth IMMER aktiviert in Production
3. HTTPS wenn exposed (nginx reverse proxy)
4. Kill-Switch-Endpoint erfordert 2FA-Confirmation
5. Rate-Limiting gegen Brute-Force
6. Keine Secrets in Frontend-Code
```

---

## 📦 Phase 7: Integration Testing & Hardening

**Ziel:** End-to-End Validation und Security Hardening.

### Deliverables

```
tests/integration/alerting/
├── test_e2e_alert_flow.py         # Vollständiger Alert-Lifecycle
├── test_escalation_scenarios.py   # Eskalations-Szenarien
├── test_channel_failover.py       # Channel-Fallback
├── test_audit_integrity.py        # Audit-Chain Validation
└── test_dashboard_security.py     # Security Tests

tests/stress/alerting/
├── test_alert_throughput.py       # Performance unter Last
├── test_concurrent_alerts.py      # Parallelität
└── test_memory_usage.py           # Memory-Leaks

docs/risk/
├── ALERTING_RUNBOOK.md            # Operator-Handbuch
├── ALERTING_TROUBLESHOOTING.md    # Troubleshooting Guide
└── ALERTING_SECURITY.md           # Security Best Practices
```

### Test-Szenarien

#### Szenario 1: Normal Operation

```
Given: System im Normalbetrieb
When:  Position-Loss erreicht 5% Warning-Threshold
Then:  
  - WARNING Alert wird erstellt
  - Console + File Channel erhalten Alert
  - Audit-Log Eintrag erstellt
  - Dashboard zeigt Alert
```

#### Szenario 2: Eskalation

```
Given: WARNING Alert aktiv, nicht acknowledged
When:  5 Minuten vergangen
Then:  
  - Alert wird zu CRITICAL eskaliert
  - Email + Slack Channels werden aktiviert
  - Audit-Log zeigt Eskalation
  - Dashboard zeigt Severity-Change
```

#### Szenario 3: Channel-Failover

```
Given: Slack Channel konfiguriert aber nicht erreichbar
When:  CRITICAL Alert wird dispatched
Then:  
  - Slack-Dispatch failed, Error geloggt
  - Fallback zu Email Channel
  - Email erfolgreich gesendet
  - Audit zeigt Failover
```

#### Szenario 4: Kill Switch

```
Given: Drawdown erreicht 20% (EMERGENCY)
When:  Kill Switch automatisch aktiviert
Then:  
  - ALLE Channels erhalten Alert
  - Alle offenen Positionen werden für Schließung markiert
  - Neue Trades blockiert
  - Audit-Log: KILL_SWITCH_ACTIVATED (permanent)
  - Dashboard: Roter Banner, alle Metriken frozen
```

#### Szenario 5: Stress Test

```
Given: 1000 Alerts in 60 Sekunden
When:  Alert-Storm simuliert
Then:  
  - Deduplication reduziert auf ~100 unique Alerts
  - Meta-Alert "Alert Storm" wird erstellt
  - System bleibt responsive (<100ms Latenz)
  - Kein Memory-Leak nach 1h
```

### Security Hardening Checklist

```markdown
## Security Hardening

### Input Validation
- [ ] Alle User-Inputs sanitized
- [ ] SQL-Injection Prevention (parameterized queries)
- [ ] XSS Prevention (HTML escaping)

### Authentication & Authorization
- [ ] Dashboard Auth erzwungen
- [ ] API Tokens mit Expiry
- [ ] Kill-Switch erfordert elevated privileges

### Secrets Management
- [ ] Keine Secrets in Code/Config
- [ ] Environment Variables für alle Secrets
- [ ] Secrets nicht in Logs

### Network Security
- [ ] Default: localhost only
- [ ] TLS für alle externen Verbindungen
- [ ] Rate-Limiting aktiv

### Audit & Logging
- [ ] Alle Security-Events geloggt
- [ ] Log-Rotation konfiguriert
- [ ] Keine PII in Logs

### Error Handling
- [ ] Keine Stack-Traces an User
- [ ] Graceful Degradation bei Errors
- [ ] Alert bei unerwarteten Exceptions
```

### Performance Benchmarks

| Metrik | Target | Akzeptabel |
|--------|--------|------------|
| Alert Creation Latency | <10ms | <50ms |
| Channel Dispatch Latency | <100ms | <500ms |
| Dashboard Load Time | <500ms | <2s |
| WebSocket Latency | <50ms | <200ms |
| Throughput (Alerts/sec) | >100 | >50 |
| Memory Usage (idle) | <100MB | <200MB |
| Memory Usage (under load) | <500MB | <1GB |

### Akzeptanzkriterien

- [ ] Alle 5 Test-Szenarien bestanden
- [ ] Security Hardening Checklist 100% ✅
- [ ] Performance Benchmarks erfüllt
- [ ] Operator-Runbook vollständig
- [ ] Troubleshooting-Guide mit 10+ Common Issues
- [ ] Load-Test: 1h unter 100 Alerts/min ohne Degradation
- [ ] Chaos-Test: Channel-Failures werden graceful gehandelt

---

## 🚀 Deployment-Strategie

### Phase 1-5: Development

```
Environment: Lokale Entwicklung
Channels:    Console + File only
Dashboard:   Deaktiviert
```

### Phase 6: Shadow Trading Integration

```
Environment: Shadow Trading Infrastruktur
Channels:    Console + File + Slack (Test-Channel)
Dashboard:   Aktiviert (localhost)
```

### Phase 7: Testnet

```
Environment: Kraken Testnet
Channels:    Alle Channels aktiv
Dashboard:   Aktiviert (VPN-only)
```

### Production (Post v1.0 + 12 Monate Shadow)

```
Environment: Kraken Live
Channels:    Alle Channels, redundant
Dashboard:   Aktiviert (Auth + VPN + 2FA)
```

---

## 📋 Checkliste für Go-Live

### Pre-Requisites

- [ ] Phase 1-7 alle Akzeptanzkriterien erfüllt
- [ ] 12+ Monate Shadow Trading ohne kritische Alerting-Bugs
- [ ] Operator-Training abgeschlossen
- [ ] Runbook reviewed und approved
- [ ] Backup & Recovery getestet
- [ ] Incident Response Plan dokumentiert

### Go-Live Day

- [ ] Alle Channels Health-Check: ✅
- [ ] Dashboard erreichbar: ✅
- [ ] Test-Alert durch alle Channels: ✅
- [ ] Kill-Switch Test (Dry-Run): ✅
- [ ] On-Call Rotation aktiv: ✅
- [ ] Rollback-Plan ready: ✅

### Post-Go-Live (24h)

- [ ] Keine false-positive Alerts
- [ ] Keine missed Alerts
- [ ] Dashboard stabil
- [ ] Audit-Log vollständig
- [ ] Team Feedback gesammelt

---

## 📚 Referenzen

- [Defense in Depth Architecture](../docs/risk/DEFENSE_IN_DEPTH.md)
- [Kill Switch Specification](../docs/risk/KILL_SWITCH_SPEC.md)
- [Shadow Trading Requirements](../docs/shadow/SHADOW_TRADING_REQS.md)
- [Compliance Requirements](../docs/compliance/RISK_COMPLIANCE.md)

---

## ✅ Summary

| Phase | Deliverables | Dauer | Abhängigkeiten |
|-------|-------------|-------|----------------|
| 1 | Alert Framework | 1 Woche | - |
| 2 | Threshold Alerts | 1-2 Wochen | Phase 1, VaR/CVaR |
| 3 | Notification Channels | 1 Woche | Phase 1 |
| 4 | Escalation Engine | 1 Woche | Phase 1-3 |
| 5 | Audit Logging | 1 Woche | Phase 1-4 |
| 6 | Dashboard | 1-2 Wochen | Phase 1-5 |
| 7 | Testing & Hardening | 1 Woche | Phase 1-6 |

**Gesamt-Aufwand:** 7-10 Wochen

**Kritischer Pfad:** Phase 1 → Phase 2 → Phase 7

**Empfehlung:** Starte mit Phase 1-2 parallel zur VaR/CVaR Implementation, da Threshold Alerts direkt davon abhängen.

---

**Status:** 📋 **ROADMAP READY FOR REVIEW**

**Nächster Schritt:** Phase 1 starten mit `src/risk/alerting/__init__.py`
