# Risk-Layer Production Alerting – Architecture (Phase 1)

**Projekt:** Peak_Trade  
**Modul:** Risk-Layer Alerting  
**Phase:** 1 (Foundation & Alert Framework)  
**Stand:** 2025-12-27  
**Status:** ✅ Implemented

---

## 🎯 Übersicht

Das Risk-Layer Production Alerting System bietet eine zentrale, konfigurierbare Infrastruktur für Produktions-Alerts aus allen Risk-Layer-Komponenten (VaR Gates, Kill Switch, Liquidity Gates, etc.).

**Phase 1 Scope:**
- Core alert types und event model
- TOML-basierte Konfiguration mit Environment Variable Substitution
- Alert Manager für Registrierung, Filterung und Buffering
- Alert Dispatcher (Phase 1: In-Memory Sink für Testing)
- Vollständige Unit-Test-Coverage

**Future Phases:**
- Phase 2: Channel Integrations (Slack, Email, PagerDuty)
- Phase 3: Alert Aggregation & Deduplication
- Phase 4: Escalation Policies & On-Call Integration

---

## 📦 Module Structure

```
src/risk_layer/alerting/
├── __init__.py              # Public API
├── alert_types.py           # AlertSeverity, AlertCategory enums
├── alert_event.py           # AlertEvent dataclass
├── alert_config.py          # AlertConfig loader (TOML + env vars)
├── alert_manager.py         # AlertManager (registration, filtering, buffer)
└── alert_dispatcher.py      # AlertDispatcher (Phase 1: in-memory sink)

tests/risk_layer/alerting/
├── __init__.py
├── test_alert_types.py      # Enum tests
├── test_alert_event.py      # AlertEvent tests
├── test_alert_config.py     # Config loading tests
├── test_alert_dispatcher.py # Dispatcher tests
└── test_alert_manager.py    # Manager integration tests
```

---

## 🔧 Core Components

### 1. AlertSeverity Enum

Definiert Schweregrade für Alerts mit Vergleichsoperatoren für Filterung:

```python
from src.risk_layer.alerting import AlertSeverity

# Severity Levels (aufsteigend)
AlertSeverity.DEBUG
AlertSeverity.INFO
AlertSeverity.WARNING
AlertSeverity.ERROR
AlertSeverity.CRITICAL

# Vergleiche für Filterung
assert AlertSeverity.ERROR > AlertSeverity.WARNING
assert AlertSeverity.WARNING >= AlertSeverity.WARNING
```

### 2. AlertCategory Enum

Kategorien für funktionale Gruppierung und Routing:

```python
from src.risk_layer.alerting import AlertCategory

AlertCategory.RISK_LIMIT          # VaR/CVaR/Exposure Limits
AlertCategory.POSITION_VIOLATION  # Position Size/Weight Violations
AlertCategory.EXECUTION_ERROR     # Order Execution Failures
AlertCategory.DATA_QUALITY        # Missing/Invalid Market Data
AlertCategory.SYSTEM_HEALTH       # System Status/Health Checks
AlertCategory.COMPLIANCE          # Regulatory/Compliance Issues
AlertCategory.PERFORMANCE         # Performance Degradation
AlertCategory.OTHER               # Catch-all
```

### 3. AlertEvent Dataclass

Immutable event mit vollständigem Kontext:

```python
from src.risk_layer.alerting import AlertEvent, AlertSeverity, AlertCategory

event = AlertEvent(
    severity=AlertSeverity.ERROR,
    category=AlertCategory.RISK_LIMIT,
    source="var_gate",
    message="VaR limit breached: 0.05 > 0.03",
    context={
        "position": "BTC-EUR",
        "current_var": 0.05,
        "limit": 0.03,
        "timestamp": "2025-12-27T10:30:00Z",
    }
)

# Automatisch generiert:
# - event.event_id: Unique UUID
# - event.timestamp: UTC datetime
```

**Validation:**
- `source` und `message` dürfen nicht leer sein
- `severity` muss `AlertSeverity` Enum sein
- `category` muss `AlertCategory` Enum sein
- Frozen dataclass (immutable)

### 4. AlertConfig

TOML-basierte Konfiguration mit Environment Variable Substitution:

```toml
# config/config.toml
[alerting]
enabled = true
min_severity = "warning"
buffer_size = 2000

[alerting.channels.slack]
enabled = false  # Default: disabled (safe)
webhook_url = "${SLACK_WEBHOOK_URL}"

[alerting.channels.email]
enabled = false
smtp_host = "${SMTP_HOST}"
smtp_user = "${SMTP_USER}"
smtp_password = "${SMTP_PASSWORD}"
```

**Laden der Config:**

```python
from src.risk_layer.alerting import load_alert_config

# Default: config/config.toml, section [alerting]
config = load_alert_config()

# Custom path/section
config = load_alert_config(
    config_path=Path("custom.toml"),
    section="custom_alerts"
)

# Check channel status
if config.is_channel_enabled("slack"):
    slack_cfg = config.get_channel_config("slack")
    webhook = slack_cfg["webhook_url"]
```

**Environment Variable Substitution:**
- Pattern: `${ENV_VAR_NAME}` (uppercase, underscores erlaubt)
- Fehlt eine Variable → `ValueError` beim Laden
- Keine Secrets im Code/Config → nur Platzhalter

**Default Values (Safe):**
- `enabled = False` (Alerting disabled by default)
- `min_severity = "warning"` (Filter low-priority alerts)
- `buffer_size = 1000` (In-memory event buffer)
- `channels = {}` (No channels enabled)

### 5. AlertManager

Zentrale Koordination für Alert-Lifecycle:

```python
from src.risk_layer.alerting import AlertManager, load_alert_config
from src.risk_layer.alerting import AlertSeverity, AlertCategory

# Setup
config = load_alert_config()
manager = AlertManager(config)

# Register alert
event = manager.register_alert(
    severity=AlertSeverity.ERROR,
    category=AlertCategory.RISK_LIMIT,
    source="var_gate",
    message="VaR limit breached",
    context={"current_var": 0.05, "limit": 0.03},
)

# Query recent events
recent = manager.get_recent_events(
    limit=10,
    min_severity=AlertSeverity.WARNING,
    categories=[AlertCategory.RISK_LIMIT],
    sources=["var_gate", "stress_gate"],
)

# Statistics
stats = manager.get_stats()
print(stats["total_events"])
print(stats["by_severity"])
print(stats["by_category"])
```

**Funktionen:**
- **Registrierung:** `register_alert()` erstellt AlertEvent
- **Filterung:** Severity-Filter (min_severity aus Config)
- **Buffering:** FIFO-Buffer (max buffer_size Events)
- **Dispatching:** An AlertDispatcher wenn `enabled=True`
- **Queries:** `get_recent_events()` mit Multi-Filter-Support

### 6. AlertDispatcher

Phase 1: In-Memory Sink für Testing:

```python
from src.risk_layer.alerting import AlertDispatcher

dispatcher = AlertDispatcher()

# Dispatch event (Phase 1: stores in memory)
dispatcher.dispatch(event)

# Testing/Inspection
events = dispatcher.get_dispatched_events()
count = dispatcher.count()
dispatcher.clear()
```

**Phase 2+ Roadmap:**
- Slack Webhook Integration
- Email via SMTP
- PagerDuty API
- Custom Webhooks
- Log File Appender

---

## 🔐 Security & Safety

### No Secrets in Code/Config

**❌ FALSCH:**
```toml
[alerting.channels.slack]
webhook_url = "https://hooks.slack.com/services/T00/B00/XXX"
```

**✅ RICHTIG:**
```toml
[alerting.channels.slack]
webhook_url = "${SLACK_WEBHOOK_URL}"
```

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/XXX"
```

### Default-Safe Design

- **Alerting disabled by default** (`enabled = false`)
- **No channels enabled by default** (alle channels: `enabled = false`)
- **Missing config file → safe defaults** (keine Exceptions)
- **Missing env vars → ValueError** (fail-fast bei Fehlkonfiguration)

### Test Isolation

- **Keine externen Services in Tests** (alle gemockt)
- **In-Memory Dispatcher** für deterministische Tests
- **Temp Files** für Config-Tests (automatisch cleanup)

---

## 📊 Usage Examples

### Example 1: VaR Gate Integration

```python
from src.risk_layer.alerting import AlertManager, AlertSeverity, AlertCategory

class VaRGate:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager

    def check_var_limit(self, current_var: float, limit: float) -> bool:
        if current_var > limit:
            self.alert_manager.register_alert(
                severity=AlertSeverity.ERROR,
                category=AlertCategory.RISK_LIMIT,
                source="var_gate",
                message=f"VaR limit breached: {current_var:.4f} > {limit:.4f}",
                context={
                    "current_var": current_var,
                    "limit": limit,
                    "breach_pct": (current_var - limit) / limit * 100,
                }
            )
            return False
        return True
```

### Example 2: Kill Switch Integration

```python
from src.risk_layer.alerting import AlertManager, AlertSeverity, AlertCategory

class KillSwitch:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.is_active = False

    def activate(self, reason: str):
        self.is_active = True
        self.alert_manager.register_alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM_HEALTH,
            source="kill_switch",
            message=f"Kill switch activated: {reason}",
            context={"reason": reason, "action": "all_trading_halted"}
        )
```

### Example 3: Monitoring Dashboard

```python
from src.risk_layer.alerting import AlertManager, AlertSeverity

def get_dashboard_data(manager: AlertManager) -> dict:
    """Get data for monitoring dashboard."""
    stats = manager.get_stats()

    # Recent critical/error events
    critical_events = manager.get_recent_events(
        limit=5,
        min_severity=AlertSeverity.ERROR,
    )

    return {
        "stats": stats,
        "recent_critical": [e.to_dict() for e in critical_events],
        "alerting_enabled": manager.config.enabled,
    }
```

---

## 🧪 Testing

### Run All Tests

```bash
# Run alerting tests
python3 -m pytest tests/risk_layer/alerting/ -v

# With coverage
python3 -m pytest tests/risk_layer/alerting/ --cov=src/risk_layer/alerting --cov-report=term-missing
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| `alert_types.py` | 8 | 100% |
| `alert_event.py` | 15 | 100% |
| `alert_config.py` | 15 | 100% |
| `alert_dispatcher.py` | 5 | 100% |
| `alert_manager.py` | 20 | 100% |
| **TOTAL** | **63** | **100%** |

### Test Categories

1. **Unit Tests:** Alle Module isoliert getestet
2. **Integration Tests:** AlertManager + Dispatcher
3. **Config Tests:** TOML loading + env var substitution
4. **Validation Tests:** Input validation + error cases
5. **Filter Tests:** Multi-criteria filtering

---

## 🚀 Integration Guide

### Step 1: Add to Risk Gate

```python
# src/risk_layer/var_gate.py
from src.risk_layer.alerting import AlertManager, AlertSeverity, AlertCategory

class VaRGate:
    def __init__(self, alert_manager: Optional[AlertManager] = None):
        self.alert_manager = alert_manager

    def check_limit(self, var: float, limit: float) -> bool:
        if var > limit and self.alert_manager:
            self.alert_manager.register_alert(
                severity=AlertSeverity.ERROR,
                category=AlertCategory.RISK_LIMIT,
                source="var_gate",
                message=f"VaR limit breached: {var:.4f} > {limit:.4f}",
                context={"var": var, "limit": limit}
            )
        return var <= limit
```

### Step 2: Initialize in Main

```python
# scripts/run_live_trading.py
from src.risk_layer.alerting import load_alert_config, AlertManager
from src.risk_layer.var_gate import VaRGate

def main():
    # Load config
    alert_config = load_alert_config()
    alert_manager = AlertManager(alert_config)

    # Initialize risk gates with alerting
    var_gate = VaRGate(alert_manager=alert_manager)

    # ... rest of setup
```

### Step 3: Configure Alerting

```toml
# config/config.toml
[alerting]
enabled = true
min_severity = "warning"
buffer_size = 2000

# Phase 1: No channels enabled yet
# Phase 2+: Enable Slack, Email, etc.
```

---

## 📈 Roadmap

### ✅ Phase 1: Foundation (Current)

- [x] AlertSeverity + AlertCategory enums
- [x] AlertEvent dataclass
- [x] AlertConfig loader (TOML + env vars)
- [x] AlertManager (register, filter, buffer)
- [x] AlertDispatcher (in-memory sink)
- [x] Unit tests (63 tests, 100% coverage)
- [x] Documentation

### 🔲 Phase 2: Channel Integrations (Next)

- [ ] Slack Webhook Channel
- [ ] Email SMTP Channel
- [ ] PagerDuty API Channel
- [ ] Custom Webhook Channel
- [ ] Log File Appender
- [ ] Channel retry logic + backoff
- [ ] Channel health monitoring

### 🔲 Phase 3: Advanced Features

- [ ] Alert Aggregation (deduplicate similar alerts)
- [ ] Alert Throttling (rate limiting)
- [ ] Alert Templates (customizable messages)
- [ ] Alert History (persistent storage)
- [ ] Alert Dashboard (Web UI)

### 🔲 Phase 4: Escalation & On-Call

- [ ] Escalation Policies (multi-tier)
- [ ] On-Call Rotation Integration
- [ ] Alert Acknowledgement
- [ ] Incident Management Integration
- [ ] SLA Tracking

---

## 🔗 Related Documentation

- **[Risk Layer Roadmap](RISK_LAYER_ROADMAP.md)** - Overall risk layer development plan
- **[Risk Layer V1 Operator Guide](RISK_LAYER_V1_OPERATOR_GUIDE.md)** - Operator guide for risk layer
- **[Live Risk Limits](../LIVE_RISK_LIMITS.md)** - Risk limit configuration
- **[Notifications](../NOTIFICATIONS.md)** - General notification system

---

## 📝 API Reference

### Public API

```python
from src.risk_layer.alerting import (
    # Enums
    AlertSeverity,
    AlertCategory,

    # Data Classes
    AlertEvent,
    AlertConfig,

    # Core Classes
    AlertManager,
    AlertDispatcher,

    # Functions
    load_alert_config,
)
```

### AlertSeverity

```python
class AlertSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

### AlertCategory

```python
class AlertCategory(str, Enum):
    RISK_LIMIT = "risk_limit"
    POSITION_VIOLATION = "position_violation"
    EXECUTION_ERROR = "execution_error"
    DATA_QUALITY = "data_quality"
    SYSTEM_HEALTH = "system_health"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    OTHER = "other"
```

### AlertEvent

```python
@dataclass(frozen=True)
class AlertEvent:
    severity: AlertSeverity
    category: AlertCategory
    source: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]: ...
    def matches_filter(
        self,
        min_severity: Optional[AlertSeverity] = None,
        categories: Optional[list[AlertCategory]] = None,
        sources: Optional[list[str]] = None,
    ) -> bool: ...
```

### AlertConfig

```python
@dataclass
class AlertConfig:
    enabled: bool = False
    min_severity: AlertSeverity = AlertSeverity.WARNING
    buffer_size: int = 1000
    channels: Dict[str, Dict[str, Any]] = None
    raw: Dict[str, Any] = None

    def get_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]: ...
    def is_channel_enabled(self, channel_name: str) -> bool: ...
```

### AlertManager

```python
class AlertManager:
    def __init__(
        self,
        config: AlertConfig,
        dispatcher: Optional[AlertDispatcher] = None,
    ): ...

    def register_alert(
        self,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        message: str,
        context: Optional[dict] = None,
    ) -> Optional[AlertEvent]: ...

    def get_recent_events(
        self,
        limit: Optional[int] = None,
        min_severity: Optional[AlertSeverity] = None,
        categories: Optional[List[AlertCategory]] = None,
        sources: Optional[List[str]] = None,
    ) -> List[AlertEvent]: ...

    def list_all_events(self) -> List[AlertEvent]: ...
    def clear_buffer(self) -> None: ...
    def get_event_count(self) -> int: ...
    def get_stats(self) -> dict: ...
```

### AlertDispatcher

```python
class AlertDispatcher:
    def dispatch(self, event: AlertEvent) -> None: ...
    def get_dispatched_events(self) -> List[AlertEvent]: ...
    def clear(self) -> None: ...
    def count(self) -> int: ...
```

---

## 🤝 Contributing

### Adding a New Alert Source

1. Import AlertManager in your module
2. Accept `alert_manager: Optional[AlertManager]` in constructor
3. Call `alert_manager.register_alert()` when conditions trigger
4. Choose appropriate severity and category
5. Include relevant context data

### Adding Tests

1. Place tests in `tests/risk_layer/alerting/`
2. Follow existing test patterns
3. Mock external dependencies
4. Test both success and error cases
5. Aim for 100% coverage

---

**Status:** ✅ Phase 1 Complete  
**Next:** Phase 2 - Channel Integrations  
**Contact:** Peak_Trade Risk Management Team
