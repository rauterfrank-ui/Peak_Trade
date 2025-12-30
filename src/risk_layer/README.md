# Risk Layer (Live Trading)

**Location:** `src/risk_layer/`  
**Purpose:** Operational risk management for live trading  
**Status:** Production-ready (Layer 4 Defense-in-Depth)

---

## Purpose

This module provides **operational risk management** for live trading:
1. **Kill Switch:** Emergency halt mechanism (Layer 4)
2. **Alerting:** Risk event notification and dispatch
3. **VaR Backtesting:** Validation of VaR models (Kupiec POF, traffic light)

**Primary Use Cases:**
- Emergency stop (kill switch trigger/recovery)
- Real-time alert dispatch (Slack, email, webhook, etc.)
- VaR model validation (regulatory compliance)

---

## Relationship to `src/risk/`

**Two Separate Systems (By Design):**

| Aspect | `src/risk_layer/` (This Module) | `src/risk/` |
|--------|--------------------------------|-------------|
| **Purpose** | Live Trading Risk | Backtest/Research Risk |
| **Context** | Real-time trading | Offline analysis |
| **Primary Use** | Order blocking | Metrics calculation |
| **Components** | Kill Switch, Alerting | VaR, Stress Test, Monte Carlo |
| **State** | Stateful (persistent) | Stateless (per-backtest) |

**Key Distinction:**
- **`src/risk_layer/`** = "Should we take this risk now?" (pre-trade gate)
- **`src/risk/`** = "What risk did we take?" (post-hoc analysis)

---

## Key Components

### Kill Switch (`kill_switch/`)

**Purpose:** Emergency halt mechanism (Layer 4 of Defense-in-Depth)

**Components:**
- `core.py` - KillSwitch class (state machine)
- `state.py` - State definitions (ACTIVE, KILLED, RECOVERING)
- `execution_gate.py` - ExecutionGate (blocks orders when killed)
- `triggers/` - Trigger mechanisms (manual, threshold, watchdog, external)
- `persistence.py` - State persistence (survive restarts)
- `audit.py` - Audit trail
- `cli.py` - Command-line interface

**State Machine:**
```
ACTIVE → KILLED (trigger)
KILLED → RECOVERING (request_recovery)
RECOVERING → ACTIVE (complete_recovery, after cooldown)
```

**Usage:**
```python
from src.risk_layer.kill_switch import KillSwitch, ExecutionGate

# Create kill switch
ks = KillSwitch(config)

# Create execution gate
gate = ExecutionGate(ks)

# Before executing order
try:
    gate.check_can_execute()  # Raises TradingBlockedError if killed
    # Execute order...
except TradingBlockedError:
    # Handle blocked order
    pass
```

**CLI:**
```bash
# Status
python -m src.risk_layer.kill_switch.cli status

# Trigger
python -m src.risk_layer.kill_switch.cli trigger --reason "Emergency"

# Recover
python -m src.risk_layer.kill_switch.cli recover --approved-by "operator"
python -m src.risk_layer.kill_switch.cli complete-recovery
```

---

### Alerting (`alerting/`)

**Purpose:** Risk event notification and dispatch

**Components:**
- `alert_manager.py` - AlertManager (event handling)
- `alert_dispatcher.py` - AlertDispatcher (routing)
- `alert_types.py` - Alert severity and types
- `alert_event.py` - AlertEvent dataclass
- `channels/` - Notification channels

**Channels:**
- `slack_channel.py` - Slack notifications
- `email_channel.py` - Email notifications
- `webhook_channel.py` - HTTP webhook
- `telegram_channel.py` - Telegram bot
- `file_channel.py` - File logging
- `console_channel.py` - Console output

**Usage:**
```python
from src.risk_layer.alerting import AlertManager, AlertSeverity

manager = AlertManager(config)

# Send alert
manager.send_alert(
    severity=AlertSeverity.CRITICAL,
    title="Risk Limit Breach",
    message="Daily loss exceeded $100",
    metadata={"pnl": -120.0}
)
```

---

### VaR Backtesting (`var_backtest/`)

**Purpose:** Validation of VaR models (regulatory compliance)

**Components:**
- `kupiec_pof.py` - Kupiec POF test (Proportion of Failures)
- `christoffersen_tests.py` - Christoffersen independence tests
- `traffic_light.py` - Basel traffic light system
- `violation_detector.py` - VaR violation detection
- `duration_diagnostics.py` - Duration diagnostics
- `rolling_evaluation.py` - Rolling window evaluation
- `var_backtest_runner.py` - Orchestration

**Usage:**
```python
from src.risk_layer.var_backtest import VaRBacktestRunner

runner = VaRBacktestRunner(config)
results = runner.run(returns, var_estimates)

# Check traffic light
if results.traffic_light == "RED":
    print("VaR model failed validation!")
```

---

## Integration with Live Trading

### Kill Switch Integration

**Where Integrated:**
- `src/live/shadow_session.py` - Shadow/paper sessions check kill switch
- `src/live/risk_limits.py` - LiveRiskLimits can trigger kill switch
- `src/execution/pipeline.py` - ExecutionPipeline respects execution gate

**Flow:**
```
Order Request
  ↓
LiveRiskLimits.check_orders()
  ↓
ExecutionGate.check_can_execute()
  ↓
[KILLED] → TradingBlockedError → Order blocked
[ACTIVE] → Order proceeds
```

### Alerting Integration

**Where Integrated:**
- `src/live/risk_limits.py` - Sends alerts on risk violations
- `src/risk_layer/kill_switch/core.py` - Sends alerts on kill switch trigger

**Alert Flow:**
```
Risk Event
  ↓
AlertManager.send_alert()
  ↓
AlertDispatcher.dispatch()
  ↓
Channels (Slack, Email, etc.)
  ↓
Operator Notified
```

---

## For Live Trading

**Use this module for:**
- ✅ Kill switch (emergency halt)
- ✅ Execution gate (order blocking)
- ✅ Alert dispatch (risk notifications)
- ✅ VaR model validation

**Do NOT use for:**
- ❌ Backtest risk metrics (use `src/risk/` instead)
- ❌ Position sizing in backtest (use `src/risk/` instead)
- ❌ Monte Carlo simulations (use `src/risk/` instead)

---

## Production Readiness

**Status:** ✅ **PRODUCTION-READY**

**Evidence:**
- 100+ test functions across 7 test files
- Thread-safe (RLock in KillSwitch)
- Idempotent operations (trigger, recovery)
- State persistence (survives restarts)
- Comprehensive audit trail
- CLI for operator control

**Test Coverage:**
```bash
# Run kill switch tests
uv run pytest tests/risk_layer/kill_switch/ -v

# Run alerting tests
uv run pytest tests/risk_layer/alerting/ -v

# Run VaR backtest tests
uv run pytest tests/risk_layer/var_backtest/ -v
```

---

## Emergency Procedures

See: `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md`

**Quick Commands:**
```bash
# Trigger emergency halt
python -m src.risk_layer.kill_switch.cli trigger --reason "Emergency"

# Check status
python -m src.risk_layer.kill_switch.cli status

# Recover (after issue resolved)
python -m src.risk_layer.kill_switch.cli recover --approved-by "operator"
# Wait for cooldown (default 300s)
python -m src.risk_layer.kill_switch.cli complete-recovery
```

---

## Questions?

- **"Which module for live trading?"** → `src/risk_layer/` (this module)
- **"Which module for backtest metrics?"** → `src/risk/`
- **"Can I use both?"** → Yes! Use both in their respective contexts
- **"Are they integrated?"** → No, by design (separation of concerns)

---

## Files in This Module

```
src/risk_layer/
├── __init__.py
├── kill_switch/            # Kill Switch (Layer 4)
│   ├── core.py
│   ├── state.py
│   ├── execution_gate.py
│   ├── triggers/
│   ├── persistence.py
│   ├── audit.py
│   └── cli.py
├── alerting/               # Alert System
│   ├── alert_manager.py
│   ├── alert_dispatcher.py
│   ├── alert_types.py
│   ├── alert_event.py
│   └── channels/
└── var_backtest/           # VaR Backtesting
    ├── kupiec_pof.py
    ├── christoffersen_tests.py
    ├── traffic_light.py
    ├── violation_detector.py
    └── var_backtest_runner.py
```

---

## Revision History

| Date | Version | Changes |
|------|---------|--------|
| 2025-12-30 | 1.0 | Initial README for FND-0002 remediation |
