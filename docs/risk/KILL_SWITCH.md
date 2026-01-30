# Peak_Trade Emergency Kill Switch – Technische Dokumentation

**Version:** 1.0  
**Datum:** 2025-12-28  
**Status:** ✅ IMPLEMENTIERT

---

## 📖 Übersicht

Der Emergency Kill Switch ist **Layer 4** des Defense-in-Depth Risk Management Systems von Peak_Trade. Er bietet die letzte Verteidigungslinie gegen unkontrollierte Trading-Verluste.

### Kernprinzip

> **Der Kill Switch muss IMMER funktionieren, unabhängig von allen anderen Systemkomponenten.**

### Features

✅ **Robuste State Machine** mit validierten Übergängen  
✅ **Thread-safe** durch RLock  
✅ **Multiple Trigger-Mechanismen** (Threshold, Manual, Watchdog, External)  
✅ **Kontrollierte Recovery** mit Approval, Cooldown und Gradual Restart  
✅ **Persistenter State** (crash-safe)  
✅ **Lückenloser Audit Trail**  
✅ **CLI & Execution Gate Integration**  
✅ **Minimal Dependencies** (stdlib + optional psutil)

---

## 🏗️ Architektur

Siehe [KILL_SWITCH_ARCHITECTURE.md](KILL_SWITCH_ARCHITECTURE.md) für Details.

### Layer-Struktur

```
┌─────────────────────────────────────────┐
│ Layer 4: Kill Switch (Emergency Stop)  │  ← Letzte Verteidigungslinie
├─────────────────────────────────────────┤
│ Layer 3: Portfolio Risk Management      │
├─────────────────────────────────────────┤
│ Layer 2: Position Risk Management       │
├─────────────────────────────────────────┤
│ Layer 1: Pre-Trade Risk Checks          │
└─────────────────────────────────────────┘
```

### Package-Struktur

```
src/risk_layer/kill_switch/
├── __init__.py           # Public API
├── state.py              # State Machine
├── core.py               # KillSwitch Core
├── config.py             # Configuration
│
├── triggers/             # Trigger System
│   ├── __init__.py       # TriggerRegistry
│   ├── base.py           # BaseTrigger
│   ├── threshold.py      # Threshold Triggers
│   ├── manual.py         # Manual Triggers
│   ├── watchdog.py       # Watchdog Triggers
│   └── external.py       # External Triggers
│
├── recovery.py           # RecoveryManager
├── health_check.py       # HealthChecker
├── persistence.py        # State Persistence
├── audit.py              # Audit Trail
├── execution_gate.py     # Execution Gate
└── cli.py                # CLI Interface
```

---

## 🔄 State Machine

### States

| State | Beschreibung | Trading erlaubt? |
|-------|--------------|------------------|
| `ACTIVE` | Normal-Betrieb | ✅ Ja |
| `KILLED` | Notfall-Stopp | ❌ Nein |
| `RECOVERING` | Recovery-Phase mit Cooldown | ❌ Nein |
| `DISABLED` | Deaktiviert (nur Backtest) | ✅ Ja (ignoriert) |

### Transitions

```
ACTIVE → KILLED          (trigger)
KILLED → RECOVERING      (request_recovery + Approval)
RECOVERING → ACTIVE      (complete_recovery nach Cooldown)
RECOVERING → KILLED      (trigger bei neuem Emergency)
```

### Validierung

Alle State-Transitions werden validiert. Ungültige Transitions werfen `StateTransitionError`.

---

## 🎯 Trigger-System

### Trigger-Typen

#### 1. ThresholdTrigger

Metric-basierte Trigger mit konfigurierbaren Schwellwerten.

**Konfiguration:**
```toml
[kill_switch.triggers.drawdown]
enabled = true
type = "threshold"
metric = "portfolio_drawdown"
threshold = -0.15
operator = "lt"  # less than
cooldown_seconds = 0
```

**Operators:**
- `lt`: less than
- `le`: less or equal
- `gt`: greater than
- `ge`: greater or equal
- `eq`: equal
- `ne`: not equal

**Beispiel-Metriken:**
- `portfolio_drawdown`: Portfolio Drawdown
- `daily_pnl`: Tages-PnL
- `realized_volatility_1h`: Stündliche Volatilität

#### 2. ManualTrigger

Operator-initiierte Trigger via CLI/API.

```python
from src.risk_layer.kill_switch import KillSwitch

ks = KillSwitch(config)
ks.trigger("Manual stop for maintenance", triggered_by="manual_cli")
```

#### 3. WatchdogTrigger

System-Health-Monitoring.

**Überwacht:**
- Heartbeat (Prozess lebt)
- Memory Usage
- CPU Usage

**Abhängigkeit:** `psutil` (optional, degrades gracefully)

```bash
pip install psutil
```

#### 4. ExternalTrigger

Externe System-Zustände.

**Überwacht:**
- Exchange Connection Status
- Price Feed Freshness
- API Error Rate

### TriggerRegistry

Verwaltet alle Trigger und bietet unified check interface.

```python
from src.risk_layer.kill_switch.triggers import TriggerRegistry

registry = TriggerRegistry.from_config(config)

# Check all triggers
context = {
    "portfolio_drawdown": -0.12,
    "daily_pnl": -0.03,
    "exchange_connected": True,
}

results = registry.check_all(context)

# Act on triggered conditions
for result in results:
    if result.should_trigger:
        kill_switch.trigger(result.reason, triggered_by="threshold")
```

---

## 🔄 Recovery-System

### Multi-Stage Recovery

```
KILLED → Request Recovery → Validation → Cooldown → Gradual Restart → ACTIVE
```

### 1. Recovery Request

```python
kill_switch.request_recovery(
    approved_by="operator_name",
    approval_code="SECRET_CODE"
)
```

### 2. Health Checks

Vor Recovery wird System-Health geprüft:
- Memory verfügbar
- CPU nicht überlastet
- Exchange verbunden
- Price Feed aktuell

```python
from src.risk_layer.kill_switch.health_check import HealthChecker

checker = HealthChecker(recovery_config)
result = checker.check_all(context)

if not result.is_healthy:
    print(f"Health check failed: {result.issues}")
```

### 3. Cooldown

Default: 5 Minuten Wartezeit nach Recovery-Request.

```toml
[kill_switch.recovery]
cooldown_seconds = 300  # 5 Minuten
```

### 4. Gradual Restart

Position Limits werden schrittweise erhöht:

| Zeit | Limit Factor | Position Size |
|------|--------------|---------------|
| Start | 0.5 | 50% |
| +1h | 0.75 | 75% |
| +2h | 1.0 | 100% |

```python
from src.risk_layer.kill_switch.recovery import RecoveryManager

manager = RecoveryManager(recovery_config, health_checker)
factor = manager.position_limit_factor  # 0.5 → 0.75 → 1.0

# In Position Sizing:
max_position = base_position_size * factor
```

---

## 💾 Persistence & Audit

### State Persistence

**Features:**
- Atomic writes (crash-safe via tmp → rename)
- Automatic backup vor Überschreiben
- State recovery on startup

**Speicherort:** `data&#47;kill_switch&#47;state.json`

```python
from src.risk_layer.kill_switch.persistence import StatePersistence

persistence = StatePersistence("data/kill_switch/state.json")

# Save
persistence.save(
    state=KillSwitchState.KILLED,
    killed_at=datetime.utcnow(),
    trigger_reason="Drawdown limit"
)

# Load
state_data = persistence.load()
```

### Audit Trail

**Format:** JSONL (JSON Lines)  
**Rotation:** Daily + Size-based (10 MB)  
**Retention:** 90 Tage  
**Compression:** Alte Logs werden mit gzip komprimiert

**Speicherort:** `data/kill_switch/audit/`

```python
from src.risk_layer.kill_switch.audit import AuditTrail

audit = AuditTrail("data/kill_switch/audit")

# Log event
audit.log_event(kill_switch_event)

# Query events
events = audit.get_events(
    since=datetime.now() - timedelta(days=7),
    limit=100
)
```

---

## 🔌 Integration

### Execution Gate

**Verwendung im Trading Code:**

```python
from src.risk_layer.kill_switch import KillSwitch
from src.risk_layer.kill_switch.execution_gate import ExecutionGate, TradingBlockedError

# Initialize
kill_switch = KillSwitch(config)
gate = ExecutionGate(kill_switch)

# Option 1: Check before execution
try:
    gate.check_can_execute()
    # Execute order...
except TradingBlockedError as e:
    logger.error(f"Trading blocked: {e}")

# Option 2: Context manager
with gate:
    # Execute order...
    pass

# Option 3: Wrapper
result = gate.execute_with_gate(order_function, *args, **kwargs)
```

### CLI Integration

```bash
# Status
python3 -m src.risk_layer.kill_switch.cli status

# Trigger
python3 -m src.risk_layer.kill_switch.cli trigger --reason "Maintenance" --confirm

# Recover
python3 -m src.risk_layer.kill_switch.cli recover --code "SECRET" --reason "Fixed"

# Audit
python3 -m src.risk_layer.kill_switch.cli audit --since 24h --limit 50

# Health
python3 -m src.risk_layer.kill_switch.cli health
```

### Operator Script

```bash
# Simpler wrapper
./scripts/ops/kill_switch_ctl.sh status
./scripts/ops/kill_switch_ctl.sh trigger "Reason"
./scripts/ops/kill_switch_ctl.sh recover
./scripts/ops/kill_switch_ctl.sh audit
./scripts/ops/kill_switch_ctl.sh health
```

---

## ⚙️ Konfiguration

Siehe `config/risk/kill_switch.toml` für vollständige Konfiguration.

### Wichtige Parameter

```toml
[kill_switch]
enabled = true
mode = "active"  # "active" | "disabled"
recovery_cooldown_seconds = 300
require_approval_code = true
approval_code_env = "KILL_SWITCH_APPROVAL_CODE"

[kill_switch.triggers.drawdown]
enabled = true
threshold = -0.15  # -15%

[kill_switch.recovery]
gradual_restart_enabled = true
initial_position_limit_factor = 0.5
escalation_intervals = [3600, 7200]
escalation_factors = [0.75, 1.0]
```

### Umgebungsvariablen

```bash
# Approval Code (erforderlich für Recovery)
export KILL_SWITCH_APPROVAL_CODE='your_secret_code_here'
```

**Wichtig:** Approval Code NIEMALS in Git committen!

---

## 🧪 Testing

### Unit Tests

```bash
# Alle Tests
python3 -m pytest tests/risk_layer/kill_switch/ -v

# Nur State Machine
python3 -m pytest tests/risk_layer/kill_switch/test_state_machine.py -v

# Nur Triggers
python3 -m pytest tests/risk_layer/kill_switch/test_triggers.py -v

# Mit Coverage
python3 -m pytest tests/risk_layer/kill_switch/ --cov=src/risk_layer/kill_switch
```

### Integration Tests

```bash
python3 -m pytest tests/risk_layer/kill_switch/test_integration.py -v
```

### Test-Fixtures

Siehe `tests/risk_layer/kill_switch/conftest.py` für vorgefertigte Fixtures.

---

## 🔒 Security

### Approval Code

- Wird als Environment Variable gespeichert
- NIEMALS in Config-Files
- NIEMALS in Git
- Rotation empfohlen (monatlich)

### Audit Trail

- Append-only (keine Manipulation möglich)
- Immutable Events
- Compression für alte Logs

### Thread-Safety

- RLock für alle State-Änderungen
- Keine Race Conditions
- Chaos Engineering validiert

---

## 📊 Monitoring

### Metriken

Empfohlene Prometheus Metriken (TODO: Implementierung):

```python
# Counter
kill_switch_triggers_total{reason="drawdown"}
kill_switch_recoveries_total

# Gauge
kill_switch_state{state="ACTIVE"}
kill_switch_position_limit_factor

# Histogram
kill_switch_trigger_latency_seconds
kill_switch_recovery_duration_seconds
```

### Alerts

Empfohlene Alerts:

1. **Kill Switch Triggered** → P1 (immediate)
2. **Recovery Failed** → P2
3. **Health Check Failed** → P3
4. **Watchdog Missed Heartbeats** → P3

---

## 🚀 Deployment

### Installation

```bash
# 1. Package ist bereits im src/ vorhanden

# 2. Optional: psutil für Watchdog
pip install psutil

# 3. Config erstellen/anpassen
cp config/risk/kill_switch.toml config/risk/kill_switch.production.toml
vim config/risk/kill_switch.production.toml

# 4. Approval Code setzen
export KILL_SWITCH_APPROVAL_CODE='production_code'

# 5. Directories erstellen
mkdir -p data/kill_switch/{audit,backups}

# 6. Script ausführbar machen
chmod +x scripts/ops/kill_switch_ctl.sh
```

### Startup Check

```bash
# Status prüfen
./scripts/ops/kill_switch_ctl.sh status

# Health Check
./scripts/ops/kill_switch_ctl.sh health

# Trigger testen (im Staging!)
./scripts/ops/kill_switch_ctl.sh trigger "Test in Staging" --confirm
./scripts/ops/kill_switch_ctl.sh recover
```

---

## 📚 Weitere Dokumentation

- [Architektur](KILL_SWITCH_ARCHITECTURE.md) - Technische Architektur & Design
- [Operator Runbook](../ops/KILL_SWITCH_RUNBOOK.md) - Operationelle Verfahren
- [Roadmap](roadmaps/ROADMAP_EMERGENCY_KILL_SWITCH.md) - Implementierungs-Roadmap

---

## 🐛 Known Issues & Limitations

### Aktuelle Limitationen

1. **Keine Prometheus Integration** (geplant für v1.1)
2. **Keine Email/Slack Notifications** (geplant für v1.1)
3. **Kein Dual-Approval** (geplant für Production)

### TODOs

- [ ] Prometheus Metrics Export
- [ ] Slack/Email Notifications
- [ ] Dual-Approval für Production
- [ ] REST API Endpoint
- [ ] Web UI Dashboard

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-12-28  
**Maintainer:** Peak_Trade Risk Team
