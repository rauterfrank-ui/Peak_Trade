# Peak_Trade – Emergency Kill Switch Roadmap

**Version:** 1.0  
**Datum:** 2025-12-27  
**Status:** 📋 GEPLANT  
**Layer:** Risk Layer – Defense in Depth Layer 4  
**Priorität:** 🔴 KRITISCH (Blocker für Live-Trading)

---

## 🎯 Executive Summary

Der **Emergency Kill Switch** ist die letzte Verteidigungslinie im 4-Layer Defense-in-Depth System von Peak_Trade. Er ermöglicht das sofortige Stoppen aller Trading-Aktivitäten bei kritischen Ereignissen – unabhängig von allen anderen Systemkomponenten.

**Kernprinzip:** Der Kill Switch muss *immer* funktionieren, auch wenn alle anderen Systeme ausfallen.

---

## 📊 Phasen-Übersicht

| Phase | Name | Dauer | Status | Abhängigkeiten |
|-------|------|-------|--------|----------------|
| **1** | Foundation & State Machine | 3-4 Tage | ⬜ Geplant | Keine |
| **2** | Trigger-Mechanismen | 4-5 Tage | ⬜ Geplant | Phase 1 |
| **3** | Recovery & Reactivation | 3-4 Tage | ⬜ Geplant | Phase 2 |
| **4** | Persistence & Audit | 2-3 Tage | ⬜ Geplant | Phase 3 |
| **5** | Integration & API | 3-4 Tage | ⬜ Geplant | Phase 4 |
| **6** | Testing & Chaos Engineering | 4-5 Tage | ⬜ Geplant | Phase 5 |
| **7** | Dokumentation & Runbooks | 2-3 Tage | ⬜ Geplant | Phase 6 |

**Geschätzte Gesamtdauer:** 21-28 Tage (4-5 Wochen)

---

## 🔴 Phase 1: Foundation & State Machine

**Ziel:** Kernarchitektur des Kill Switch mit robuster State Machine implementieren.

**Dauer:** 3-4 Tage

### 1.1 State Machine Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    KILL SWITCH STATE MACHINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌──────────┐       trigger()       ┌──────────────┐         │
│    │  ACTIVE  │ ───────────────────▶  │   KILLED     │         │
│    │ (normal) │                       │ (emergency)  │         │
│    └──────────┘                       └──────────────┘         │
│         ▲                                    │                  │
│         │         recover()                  │                  │
│         │    (requires approval)             │                  │
│         │                                    ▼                  │
│         │                            ┌──────────────┐          │
│         └─────────────────────────── │  RECOVERING  │          │
│                                      │  (cooldown)  │          │
│                                      └──────────────┘          │
│                                                                 │
│    ┌──────────┐                                                │
│    │ DISABLED │  ◀── Nur via Config (Backtest-Mode)           │
│    └──────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `src/risk_layer/kill_switch/state.py` | State Machine Enum + Transitions |
| `src/risk_layer/kill_switch/core.py` | KillSwitch Hauptklasse |
| `src/risk_layer/kill_switch/__init__.py` | Public API Exports |
| `tests/risk_layer/kill_switch/test_state_machine.py` | State Transition Tests |
| `config/risk/kill_switch.toml` | Konfiguration |

### 1.3 Implementierung

```python
# src/risk_layer/kill_switch/state.py
"""Kill Switch State Machine für Peak_Trade."""

from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class KillSwitchState(Enum):
    """Zustände des Kill Switch."""
    ACTIVE = auto()      # Normal-Betrieb, Trading erlaubt
    KILLED = auto()      # Notfall-Stopp, kein Trading
    RECOVERING = auto()  # Cooldown nach Recovery-Anfrage
    DISABLED = auto()    # Deaktiviert (nur Backtest)


@dataclass(frozen=True)
class KillSwitchEvent:
    """Immutable Event für Audit-Trail."""
    timestamp: datetime
    previous_state: KillSwitchState
    new_state: KillSwitchState
    trigger_reason: str
    triggered_by: str  # "system", "manual", "threshold"
    metadata: dict


class StateTransitionError(Exception):
    """Ungültiger State-Übergang."""
    pass
```

```python
# src/risk_layer/kill_switch/core.py
"""Kill Switch Core Implementation."""

from datetime import datetime, timedelta
from typing import Optional, Callable, List
from threading import RLock
import logging

from .state import KillSwitchState, KillSwitchEvent, StateTransitionError


class KillSwitch:
    """
    Emergency Kill Switch für Peak_Trade.

    Layer 4 der Defense-in-Depth Architektur.
    Letzte Verteidigungslinie - muss IMMER funktionieren.

    Thread-safe durch RLock.
    """

    # Erlaubte State-Übergänge
    VALID_TRANSITIONS = {
        KillSwitchState.ACTIVE: {KillSwitchState.KILLED},
        KillSwitchState.KILLED: {KillSwitchState.RECOVERING},
        KillSwitchState.RECOVERING: {KillSwitchState.ACTIVE, KillSwitchState.KILLED},
        KillSwitchState.DISABLED: set(),  # Keine Transitions
    }

    def __init__(
        self,
        config: dict,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialisiert den Kill Switch.

        Args:
            config: Konfiguration aus kill_switch.toml
            logger: Optional Logger Instance
        """
        self._lock = RLock()
        self._state = KillSwitchState.ACTIVE
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

        # Event History für Audit
        self._events: List[KillSwitchEvent] = []

        # Callbacks für State Changes
        self._on_kill_callbacks: List[Callable] = []
        self._on_recover_callbacks: List[Callable] = []

        # Timestamps
        self._killed_at: Optional[datetime] = None
        self._recovery_started_at: Optional[datetime] = None

        # Cooldown-Konfiguration
        self._recovery_cooldown = timedelta(
            seconds=config.get("recovery_cooldown_seconds", 300)
        )

        self._logger.info(
            f"KillSwitch initialisiert: state={self._state.name}, "
            f"cooldown={self._recovery_cooldown}"
        )

    @property
    def state(self) -> KillSwitchState:
        """Aktueller State (thread-safe read)."""
        with self._lock:
            return self._state

    @property
    def is_killed(self) -> bool:
        """True wenn Trading gestoppt."""
        return self.state in (KillSwitchState.KILLED, KillSwitchState.RECOVERING)

    @property
    def is_active(self) -> bool:
        """True wenn Trading erlaubt."""
        return self.state == KillSwitchState.ACTIVE

    def trigger(
        self,
        reason: str,
        triggered_by: str = "system",
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Aktiviert den Kill Switch (EMERGENCY STOP).

        Args:
            reason: Grund für den Trigger (für Audit)
            triggered_by: Wer hat getriggert ("system", "manual", "threshold")
            metadata: Zusätzliche Daten für Audit

        Returns:
            True wenn erfolgreich getriggert
        """
        with self._lock:
            if self._state == KillSwitchState.DISABLED:
                self._logger.warning("Kill Switch ist DISABLED (Backtest-Mode)")
                return False

            if self._state == KillSwitchState.KILLED:
                self._logger.warning("Kill Switch bereits KILLED")
                return True  # Bereits im gewünschten Zustand

            # State Transition
            previous = self._state
            self._state = KillSwitchState.KILLED
            self._killed_at = datetime.utcnow()

            # Event loggen
            event = KillSwitchEvent(
                timestamp=self._killed_at,
                previous_state=previous,
                new_state=self._state,
                trigger_reason=reason,
                triggered_by=triggered_by,
                metadata=metadata or {},
            )
            self._events.append(event)

            self._logger.critical(
                f"🚨 KILL SWITCH TRIGGERED: {reason} "
                f"(by={triggered_by}, from={previous.name})"
            )

            # Callbacks ausführen
            self._execute_callbacks(self._on_kill_callbacks, event)

            return True

    def request_recovery(
        self,
        approved_by: str,
        approval_code: Optional[str] = None,
    ) -> bool:
        """
        Startet Recovery-Prozess (mit Cooldown).

        Args:
            approved_by: Wer genehmigt die Recovery
            approval_code: Optional Bestätigungscode

        Returns:
            True wenn Recovery gestartet
        """
        with self._lock:
            if self._state != KillSwitchState.KILLED:
                self._logger.warning(
                    f"Recovery nur von KILLED möglich, aktuell: {self._state.name}"
                )
                return False

            # Approval validieren
            if self._config.get("require_approval_code", False):
                if not self._validate_approval_code(approval_code):
                    self._logger.error("Ungültiger Approval Code")
                    return False

            # State Transition
            previous = self._state
            self._state = KillSwitchState.RECOVERING
            self._recovery_started_at = datetime.utcnow()

            event = KillSwitchEvent(
                timestamp=self._recovery_started_at,
                previous_state=previous,
                new_state=self._state,
                trigger_reason=f"Recovery requested by {approved_by}",
                triggered_by="manual",
                metadata={"approved_by": approved_by},
            )
            self._events.append(event)

            self._logger.warning(
                f"⏳ RECOVERY STARTED: cooldown={self._recovery_cooldown}, "
                f"approved_by={approved_by}"
            )

            return True

    def complete_recovery(self) -> bool:
        """
        Schließt Recovery ab (nach Cooldown).

        Returns:
            True wenn erfolgreich reaktiviert
        """
        with self._lock:
            if self._state != KillSwitchState.RECOVERING:
                return False

            # Cooldown prüfen
            if self._recovery_started_at:
                elapsed = datetime.utcnow() - self._recovery_started_at
                if elapsed < self._recovery_cooldown:
                    remaining = self._recovery_cooldown - elapsed
                    self._logger.warning(
                        f"Cooldown noch aktiv: {remaining.seconds}s verbleibend"
                    )
                    return False

            # State Transition
            previous = self._state
            self._state = KillSwitchState.ACTIVE

            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=previous,
                new_state=self._state,
                trigger_reason="Recovery completed",
                triggered_by="system",
                metadata={},
            )
            self._events.append(event)

            # Reset Timestamps
            self._killed_at = None
            self._recovery_started_at = None

            self._logger.info("✅ KILL SWITCH RECOVERED: Trading wieder aktiv")

            # Callbacks ausführen
            self._execute_callbacks(self._on_recover_callbacks, event)

            return True

    def check_and_block(self) -> bool:
        """
        Prüft ob Trading erlaubt ist.

        Returns:
            True wenn Trading BLOCKIERT ist

        Verwendung:
            if kill_switch.check_and_block():
                raise TradingBlockedError("Kill Switch aktiv")
        """
        return self.is_killed

    def register_on_kill(self, callback: Callable[[KillSwitchEvent], None]):
        """Registriert Callback für Kill-Events."""
        self._on_kill_callbacks.append(callback)

    def register_on_recover(self, callback: Callable[[KillSwitchEvent], None]):
        """Registriert Callback für Recovery-Events."""
        self._on_recover_callbacks.append(callback)

    def get_audit_trail(self) -> List[KillSwitchEvent]:
        """Gibt alle Events für Audit zurück."""
        with self._lock:
            return list(self._events)

    def _validate_approval_code(self, code: Optional[str]) -> bool:
        """Validiert Approval Code (Implementierung TBD)."""
        expected = self._config.get("approval_code")
        return code == expected if expected else True

    def _execute_callbacks(
        self,
        callbacks: List[Callable],
        event: KillSwitchEvent,
    ):
        """Führt Callbacks sicher aus."""
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Callback-Fehler: {e}")
```

### 1.4 Konfiguration

```toml
# config/risk/kill_switch.toml

[kill_switch]
# Allgemeine Einstellungen
enabled = true
mode = "active"  # "active" | "disabled" (nur Backtest)

# Recovery-Einstellungen
recovery_cooldown_seconds = 300  # 5 Minuten Cooldown
require_approval_code = true
# approval_code = "EMERGENCY_RECOVERY_2025"  # In .env auslagern!

# Logging
log_level = "INFO"
audit_retention_days = 90

# Persistence
persist_state = true
state_file = "data/kill_switch/state.json"
```

### 1.5 Acceptance Criteria

- [ ] State Machine mit 4 States implementiert
- [ ] Thread-safe durch RLock
- [ ] Alle State-Übergänge validiert
- [ ] Event-History für Audit
- [ ] Callback-System für Kill/Recover
- [ ] Cooldown-Mechanismus funktioniert
- [ ] Unit Tests: 100% State Coverage
- [ ] Config-driven (TOML)

### 1.6 Tests

```python
# tests/risk_layer/kill_switch/test_state_machine.py

import pytest
from src.risk.kill_switch import KillSwitch, KillSwitchState


@pytest.fixture
def kill_switch():
    """Erstellt KillSwitch mit Test-Config."""
    config = {
        "enabled": True,
        "recovery_cooldown_seconds": 1,  # Kurz für Tests
        "require_approval_code": False,
    }
    return KillSwitch(config)


class TestStateTransitions:
    """Tests für State Machine."""

    def test_initial_state_is_active(self, kill_switch):
        """Initial State sollte ACTIVE sein."""
        assert kill_switch.state == KillSwitchState.ACTIVE
        assert kill_switch.is_active
        assert not kill_switch.is_killed

    def test_trigger_changes_to_killed(self, kill_switch):
        """Trigger sollte zu KILLED wechseln."""
        result = kill_switch.trigger("Test Trigger")

        assert result is True
        assert kill_switch.state == KillSwitchState.KILLED
        assert kill_switch.is_killed
        assert not kill_switch.is_active

    def test_double_trigger_is_idempotent(self, kill_switch):
        """Doppelter Trigger sollte safe sein."""
        kill_switch.trigger("First")
        result = kill_switch.trigger("Second")

        assert result is True
        assert kill_switch.state == KillSwitchState.KILLED

    def test_recovery_starts_cooldown(self, kill_switch):
        """Recovery sollte Cooldown starten."""
        kill_switch.trigger("Test")
        result = kill_switch.request_recovery("operator")

        assert result is True
        assert kill_switch.state == KillSwitchState.RECOVERING

    def test_recovery_requires_killed_state(self, kill_switch):
        """Recovery nur von KILLED möglich."""
        result = kill_switch.request_recovery("operator")

        assert result is False
        assert kill_switch.state == KillSwitchState.ACTIVE

    def test_complete_recovery_after_cooldown(self, kill_switch):
        """Complete Recovery nach Cooldown."""
        import time

        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        # Cooldown abwarten (1 Sekunde in Test-Config)
        time.sleep(1.1)

        result = kill_switch.complete_recovery()

        assert result is True
        assert kill_switch.state == KillSwitchState.ACTIVE

    def test_complete_recovery_blocked_during_cooldown(self, kill_switch):
        """Complete Recovery blockiert während Cooldown."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")

        # Sofort versuchen (vor Cooldown)
        result = kill_switch.complete_recovery()

        assert result is False
        assert kill_switch.state == KillSwitchState.RECOVERING


class TestAuditTrail:
    """Tests für Audit-Funktionalität."""

    def test_events_are_recorded(self, kill_switch):
        """Events sollten aufgezeichnet werden."""
        kill_switch.trigger("Test Reason", triggered_by="manual")

        events = kill_switch.get_audit_trail()

        assert len(events) == 1
        assert events[0].trigger_reason == "Test Reason"
        assert events[0].triggered_by == "manual"
        assert events[0].previous_state == KillSwitchState.ACTIVE
        assert events[0].new_state == KillSwitchState.KILLED


class TestCheckAndBlock:
    """Tests für Trading-Gate."""

    def test_check_and_block_returns_false_when_active(self, kill_switch):
        """check_and_block() False wenn aktiv."""
        assert kill_switch.check_and_block() is False

    def test_check_and_block_returns_true_when_killed(self, kill_switch):
        """check_and_block() True wenn killed."""
        kill_switch.trigger("Test")
        assert kill_switch.check_and_block() is True

    def test_check_and_block_returns_true_when_recovering(self, kill_switch):
        """check_and_block() True während Recovery."""
        kill_switch.trigger("Test")
        kill_switch.request_recovery("operator")
        assert kill_switch.check_and_block() is True
```

---

## 🟠 Phase 2: Trigger-Mechanismen

**Ziel:** Automatische und manuelle Trigger für verschiedene Szenarien.

**Dauer:** 4-5 Tage

### 2.1 Trigger-Typen

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRIGGER-MECHANISMEN                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ MANUELLE TRIGGER│    │ AUTO TRIGGER    │                    │
│  ├─────────────────┤    ├─────────────────┤                    │
│  │ • CLI Command   │    │ • Drawdown Limit│                    │
│  │ • API Endpoint  │    │ • Daily Loss    │                    │
│  │ • Hotkey        │    │ • Volatility    │                    │
│  │ • Panic Button  │    │ • System Health │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
│           │                      │                              │
│           └──────────┬───────────┘                              │
│                      ▼                                          │
│              ┌───────────────┐                                  │
│              │  KILL SWITCH  │                                  │
│              └───────────────┘                                  │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ EXTERNAL TRIGGER│    │ WATCHDOG        │                    │
│  ├─────────────────┤    ├─────────────────┤                    │
│  │ • Exchange Down │    │ • Heartbeat     │                    │
│  │ • Network Error │    │ • Process Check │                    │
│  │ • API Limit     │    │ • Memory/CPU    │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `src/risk_layer/kill_switch/triggers/__init__.py` | Trigger Module |
| `src/risk_layer/kill_switch/triggers/base.py` | Abstract Base Trigger |
| `src/risk_layer/kill_switch/triggers/threshold.py` | Threshold-basierte Trigger |
| `src/risk_layer/kill_switch/triggers/manual.py` | Manuelle Trigger |
| `src/risk_layer/kill_switch/triggers/watchdog.py` | System Watchdog |
| `src/risk_layer/kill_switch/triggers/external.py` | Externe Trigger (Exchange, Network) |
| `tests/risk_layer/kill_switch/test_triggers.py` | Trigger Tests |

### 2.3 Threshold-Trigger Konfiguration

```toml
# config/risk/kill_switch.toml

[kill_switch.triggers.drawdown]
enabled = true
type = "threshold"
metric = "portfolio_drawdown"
threshold = -0.15  # -15% Drawdown
operator = "lt"    # less than
cooldown_seconds = 0  # Sofort triggern

[kill_switch.triggers.daily_loss]
enabled = true
type = "threshold"
metric = "daily_pnl"
threshold = -0.05  # -5% Tagesverlust
operator = "lt"
cooldown_seconds = 0

[kill_switch.triggers.volatility_spike]
enabled = true
type = "threshold"
metric = "realized_volatility_1h"
threshold = 0.10  # 10% stündliche Volatilität
operator = "gt"   # greater than
cooldown_seconds = 3600  # 1h Cooldown nach Trigger

[kill_switch.triggers.exchange_disconnect]
enabled = true
type = "external"
check_interval_seconds = 30
max_consecutive_failures = 3

[kill_switch.triggers.system_health]
enabled = true
type = "watchdog"
heartbeat_interval_seconds = 60
max_missed_heartbeats = 3
memory_threshold_percent = 90
cpu_threshold_percent = 95
```

### 2.4 Implementierung

```python
# src/risk_layer/kill_switch/triggers/base.py
"""Base Trigger Interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TriggerResult:
    """Ergebnis einer Trigger-Prüfung."""
    should_trigger: bool
    reason: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: dict = None

    def __post_init__(self):
        self.metadata = self.metadata or {}


class BaseTrigger(ABC):
    """Abstract Base Class für Trigger."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self._last_triggered: Optional[datetime] = None
        self._cooldown_seconds = config.get("cooldown_seconds", 0)

    @abstractmethod
    def check(self, context: dict) -> TriggerResult:
        """
        Prüft ob Trigger ausgelöst werden soll.

        Args:
            context: Aktueller System-Kontext (Metriken, State)

        Returns:
            TriggerResult mit Entscheidung
        """
        pass

    def is_on_cooldown(self) -> bool:
        """Prüft ob Trigger noch im Cooldown ist."""
        if not self._last_triggered or self._cooldown_seconds == 0:
            return False

        elapsed = (datetime.utcnow() - self._last_triggered).total_seconds()
        return elapsed < self._cooldown_seconds

    def mark_triggered(self):
        """Markiert Trigger als ausgelöst."""
        self._last_triggered = datetime.utcnow()
```

```python
# src/risk_layer/kill_switch/triggers/threshold.py
"""Threshold-basierte Trigger."""

from typing import Callable, Dict, Any
import operator as op

from .base import BaseTrigger, TriggerResult


class ThresholdTrigger(BaseTrigger):
    """
    Trigger basierend auf Metrik-Schwellwerten.

    Beispiel:
        - Drawdown > -15% → Kill
        - Daily Loss > -5% → Kill
        - Volatility > 10% → Kill
    """

    OPERATORS: Dict[str, Callable] = {
        "lt": op.lt,      # less than
        "le": op.le,      # less or equal
        "gt": op.gt,      # greater than
        "ge": op.ge,      # greater or equal
        "eq": op.eq,      # equal
        "ne": op.ne,      # not equal
    }

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.metric_name = config["metric"]
        self.threshold = config["threshold"]
        self.operator_name = config.get("operator", "lt")
        self.operator = self.OPERATORS[self.operator_name]

    def check(self, context: dict) -> TriggerResult:
        """Prüft Metrik gegen Threshold."""
        if not self.enabled:
            return TriggerResult(
                should_trigger=False,
                reason=f"Trigger '{self.name}' disabled"
            )

        if self.is_on_cooldown():
            return TriggerResult(
                should_trigger=False,
                reason=f"Trigger '{self.name}' on cooldown"
            )

        # Metrik aus Context holen
        metric_value = context.get(self.metric_name)

        if metric_value is None:
            return TriggerResult(
                should_trigger=False,
                reason=f"Metric '{self.metric_name}' not found in context"
            )

        # Threshold prüfen
        should_trigger = self.operator(metric_value, self.threshold)

        if should_trigger:
            self.mark_triggered()
            return TriggerResult(
                should_trigger=True,
                reason=(
                    f"{self.metric_name}={metric_value:.4f} "
                    f"{self.operator_name} {self.threshold}"
                ),
                metric_value=metric_value,
                threshold=self.threshold,
                metadata={
                    "trigger_name": self.name,
                    "trigger_type": "threshold",
                    "operator": self.operator_name,
                }
            )

        return TriggerResult(
            should_trigger=False,
            reason=f"Threshold not reached: {metric_value:.4f}",
            metric_value=metric_value,
            threshold=self.threshold,
        )
```

```python
# src/risk_layer/kill_switch/triggers/watchdog.py
"""System Watchdog Trigger."""

import psutil
from datetime import datetime, timedelta
from typing import Optional

from .base import BaseTrigger, TriggerResult


class WatchdogTrigger(BaseTrigger):
    """
    System Health Watchdog.

    Überwacht:
    - Heartbeat (Prozess lebt)
    - Memory Usage
    - CPU Usage
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.heartbeat_interval = timedelta(
            seconds=config.get("heartbeat_interval_seconds", 60)
        )
        self.max_missed = config.get("max_missed_heartbeats", 3)
        self.memory_threshold = config.get("memory_threshold_percent", 90)
        self.cpu_threshold = config.get("cpu_threshold_percent", 95)

        self._last_heartbeat: Optional[datetime] = None
        self._missed_heartbeats = 0

    def heartbeat(self):
        """Registriert einen Heartbeat."""
        self._last_heartbeat = datetime.utcnow()
        self._missed_heartbeats = 0

    def check(self, context: dict) -> TriggerResult:
        """Prüft System Health."""
        if not self.enabled:
            return TriggerResult(
                should_trigger=False,
                reason=f"Watchdog '{self.name}' disabled"
            )

        issues = []

        # Heartbeat prüfen
        if self._last_heartbeat:
            elapsed = datetime.utcnow() - self._last_heartbeat
            if elapsed > self.heartbeat_interval:
                self._missed_heartbeats += 1
                if self._missed_heartbeats >= self.max_missed:
                    issues.append(
                        f"Missed {self._missed_heartbeats} heartbeats"
                    )

        # Memory prüfen
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            issues.append(
                f"Memory critical: {memory.percent:.1f}% > {self.memory_threshold}%"
            )

        # CPU prüfen
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > self.cpu_threshold:
            issues.append(
                f"CPU critical: {cpu:.1f}% > {self.cpu_threshold}%"
            )

        if issues:
            return TriggerResult(
                should_trigger=True,
                reason="; ".join(issues),
                metadata={
                    "trigger_name": self.name,
                    "trigger_type": "watchdog",
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu,
                    "missed_heartbeats": self._missed_heartbeats,
                }
            )

        return TriggerResult(
            should_trigger=False,
            reason="System health OK",
            metadata={
                "memory_percent": memory.percent,
                "cpu_percent": cpu,
            }
        )
```

### 2.5 Acceptance Criteria

- [ ] ThresholdTrigger für Drawdown, Daily Loss, Volatility
- [ ] WatchdogTrigger für Heartbeat, Memory, CPU
- [ ] ExternalTrigger für Exchange-Verbindung
- [ ] ManualTrigger für CLI/API
- [ ] Cooldown-Mechanismus pro Trigger
- [ ] Trigger-Registry für dynamische Konfiguration
- [ ] Unit Tests für jeden Trigger-Typ
- [ ] Integration Test: Trigger → Kill Switch

---

## 🟡 Phase 3: Recovery & Reactivation

**Ziel:** Sichere, kontrollierte Wiederaufnahme des Tradings.

**Dauer:** 3-4 Tage

### 3.1 Recovery-Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      RECOVERY WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌────────────┐                                              │
│    │   KILLED   │                                              │
│    └─────┬──────┘                                              │
│          │                                                      │
│          ▼                                                      │
│    ┌────────────────────────────────────────┐                  │
│    │ 1. RECOVERY REQUEST                     │                  │
│    │    • Operator initiiert                │                  │
│    │    • Approval Code eingeben            │                  │
│    │    • Reason dokumentieren              │                  │
│    └─────────────────┬──────────────────────┘                  │
│                      │                                          │
│                      ▼                                          │
│    ┌────────────────────────────────────────┐                  │
│    │ 2. VALIDATION                          │                  │
│    │    • Approval Code prüfen              │                  │
│    │    • System Health Check               │                  │
│    │    • Trigger-Conditions prüfen         │                  │
│    └─────────────────┬──────────────────────┘                  │
│                      │                                          │
│                      ▼                                          │
│    ┌────────────────────────────────────────┐                  │
│    │ 3. COOLDOWN                            │                  │
│    │    • Wartezeit (default: 5 min)        │                  │
│    │    • Keine neuen Orders                │                  │
│    │    • Monitoring aktiv                  │                  │
│    └─────────────────┬──────────────────────┘                  │
│                      │                                          │
│                      ▼                                          │
│    ┌────────────────────────────────────────┐                  │
│    │ 4. GRADUAL RESTART                     │                  │
│    │    • Position Limits reduziert (50%)   │                  │
│    │    • Nach 1h: Normal Limits            │                  │
│    │    • Enhanced Monitoring               │                  │
│    └─────────────────┬──────────────────────┘                  │
│                      │                                          │
│                      ▼                                          │
│    ┌────────────────────────────────────────┐                  │
│    │ 5. ACTIVE                              │                  │
│    │    • Trading wieder erlaubt            │                  │
│    │    • Audit Event logged                │                  │
│    └────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `src/risk_layer/kill_switch/recovery.py` | Recovery Manager |
| `src/risk_layer/kill_switch/health_check.py` | Pre-Recovery Health Checks |
| `tests/risk_layer/kill_switch/test_recovery.py` | Recovery Tests |

**Geplant (TODO):**
- gradual_restart.py - Gradual Restart Logic

### 3.3 Recovery-Konfiguration

```toml
# config/risk/kill_switch.toml

[kill_switch.recovery]
# Basis-Einstellungen
cooldown_seconds = 300           # 5 Minuten Cooldown
require_approval_code = true
require_health_check = true
require_trigger_clear = true     # Trigger muss "clear" sein

# Gradual Restart
gradual_restart_enabled = true
initial_position_limit_factor = 0.5  # 50% der normalen Limits
escalation_intervals = [3600, 7200]  # Nach 1h: 75%, nach 2h: 100%
escalation_factors = [0.75, 1.0]

# Health Check Requirements
min_memory_available_mb = 512
max_cpu_percent = 80
require_exchange_connection = true
require_price_feed = true

# Zweistufige Approval (für Production)
require_dual_approval = false   # Später für Live
second_approver_required = false
```

### 3.4 Implementierung

```python
# src/risk_layer/kill_switch/recovery.py
"""Recovery Manager für Kill Switch."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum, auto
import logging

from .state import KillSwitchState
from .health_check import HealthChecker, HealthCheckResult


class RecoveryStage(Enum):
    """Recovery-Phasen."""
    PENDING = auto()        # Warte auf Approval
    VALIDATING = auto()     # Health Checks
    COOLDOWN = auto()       # Cooldown-Phase
    GRADUAL_RESTART = auto() # Limitierter Neustart
    COMPLETE = auto()       # Vollständig recovered


@dataclass
class RecoveryRequest:
    """Recovery-Anfrage."""
    requested_at: datetime
    requested_by: str
    approval_code: str
    reason: str
    stage: RecoveryStage = RecoveryStage.PENDING
    approved_at: Optional[datetime] = None
    health_check_result: Optional[HealthCheckResult] = None


class RecoveryManager:
    """
    Verwaltet den Recovery-Prozess nach Kill Switch Trigger.

    Stellt sicher, dass Recovery:
    - Autorisiert ist (Approval Code)
    - System-Gesundheit geprüft wurde
    - Kontrolliert erfolgt (Cooldown + Gradual Restart)
    """

    def __init__(
        self,
        config: dict,
        health_checker: HealthChecker,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config
        self.health_checker = health_checker
        self._logger = logger or logging.getLogger(__name__)

        self._current_request: Optional[RecoveryRequest] = None
        self._position_limit_factor = 1.0  # Normal

        # Gradual Restart Config
        self._gradual_enabled = config.get("gradual_restart_enabled", True)
        self._initial_factor = config.get("initial_position_limit_factor", 0.5)
        self._intervals = config.get("escalation_intervals", [3600, 7200])
        self._factors = config.get("escalation_factors", [0.75, 1.0])

    def request_recovery(
        self,
        requested_by: str,
        approval_code: str,
        reason: str,
    ) -> RecoveryRequest:
        """
        Startet Recovery-Anfrage.

        Args:
            requested_by: Operator-Name
            approval_code: Bestätigungscode
            reason: Grund für Recovery

        Returns:
            RecoveryRequest Objekt
        """
        self._current_request = RecoveryRequest(
            requested_at=datetime.utcnow(),
            requested_by=requested_by,
            approval_code=approval_code,
            reason=reason,
        )

        self._logger.info(
            f"Recovery requested by {requested_by}: {reason}"
        )

        return self._current_request

    def validate_approval(self, expected_code: str) -> bool:
        """Validiert Approval Code."""
        if not self._current_request:
            return False

        if self._current_request.approval_code != expected_code:
            self._logger.warning("Invalid approval code")
            return False

        self._current_request.approved_at = datetime.utcnow()
        self._current_request.stage = RecoveryStage.VALIDATING

        return True

    def run_health_checks(self) -> HealthCheckResult:
        """Führt Health Checks durch."""
        if not self._current_request:
            raise ValueError("No active recovery request")

        result = self.health_checker.check_all()
        self._current_request.health_check_result = result

        if result.is_healthy:
            self._current_request.stage = RecoveryStage.COOLDOWN
            self._logger.info("Health checks passed")
        else:
            self._logger.error(f"Health checks failed: {result.issues}")

        return result

    def check_cooldown_complete(self, cooldown_seconds: int) -> bool:
        """Prüft ob Cooldown abgelaufen ist."""
        if not self._current_request or not self._current_request.approved_at:
            return False

        elapsed = (datetime.utcnow() - self._current_request.approved_at).total_seconds()
        return elapsed >= cooldown_seconds

    def start_gradual_restart(self):
        """Startet Gradual Restart."""
        if not self._gradual_enabled:
            self._position_limit_factor = 1.0
            self._current_request.stage = RecoveryStage.COMPLETE
            return

        self._position_limit_factor = self._initial_factor
        self._current_request.stage = RecoveryStage.GRADUAL_RESTART

        self._logger.info(
            f"Gradual restart started: position_limit_factor={self._initial_factor}"
        )

    def update_gradual_restart(self) -> float:
        """
        Aktualisiert Gradual Restart basierend auf Zeit.

        Returns:
            Aktueller position_limit_factor
        """
        if not self._current_request or not self._current_request.approved_at:
            return self._position_limit_factor

        if self._current_request.stage != RecoveryStage.GRADUAL_RESTART:
            return self._position_limit_factor

        elapsed = (datetime.utcnow() - self._current_request.approved_at).total_seconds()

        # Finde passenden Factor basierend auf Zeit
        new_factor = self._initial_factor
        for interval, factor in zip(self._intervals, self._factors):
            if elapsed >= interval:
                new_factor = factor

        if new_factor != self._position_limit_factor:
            self._logger.info(
                f"Position limit escalated: {self._position_limit_factor} → {new_factor}"
            )
            self._position_limit_factor = new_factor

        # Check ob vollständig
        if self._position_limit_factor >= 1.0:
            self._current_request.stage = RecoveryStage.COMPLETE
            self._logger.info("Gradual restart complete")

        return self._position_limit_factor

    @property
    def position_limit_factor(self) -> float:
        """Aktueller Position Limit Factor."""
        return self._position_limit_factor

    @property
    def current_stage(self) -> Optional[RecoveryStage]:
        """Aktuelle Recovery Stage."""
        if self._current_request:
            return self._current_request.stage
        return None
```

### 3.5 Acceptance Criteria

- [ ] Multi-Stage Recovery Workflow
- [ ] Approval Code Validation
- [ ] Health Check vor Recovery
- [ ] Cooldown mit konfigurierbarer Dauer
- [ ] Gradual Restart mit Position Limits
- [ ] Eskalation der Limits über Zeit
- [ ] Dual-Approval Option (für Production)
- [ ] Integration Tests für kompletten Workflow

---

## 🟢 Phase 4: Persistence & Audit

**Ziel:** Persistente State-Speicherung und lückenloser Audit-Trail.

**Dauer:** 2-3 Tage

### 4.1 Persistence-Strategie

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE & AUDIT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────┐                 │
│  │ STATE PERSISTENCE                         │                 │
│  ├───────────────────────────────────────────┤                 │
│  │ • JSON File (simple, portable)            │                 │
│  │ • Atomic writes (tmp → rename)            │                 │
│  │ • Backup before overwrite                 │                 │
│  │ • Load on startup                         │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  ┌───────────────────────────────────────────┐                 │
│  │ AUDIT TRAIL                               │                 │
│  ├───────────────────────────────────────────┤                 │
│  │ • Append-only Log (JSONL)                 │                 │
│  │ • Rotation (daily/size-based)             │                 │
│  │ • Immutable Events                        │                 │
│  │ • Retention Policy (90 days)              │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  ┌───────────────────────────────────────────┐                 │
│  │ MONITORING EXPORT                         │                 │
│  ├───────────────────────────────────────────┤                 │
│  │ • Prometheus Metrics (optional)           │                 │
│  │ • Alerting Webhooks                       │                 │
│  │ • Email Notifications                     │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `src/risk_layer/kill_switch/persistence.py` | State Persistence |
| `src/risk_layer/kill_switch/audit.py` | Audit Trail Logger |
| `tests/risk_layer/kill_switch/test_persistence.py` | Persistence Tests |

**Geplant (TODO):**
- notifications.py - Alert/Notification System
- test_audit.py - Audit Tests

### 4.3 Implementierung

```python
# src/risk_layer/kill_switch/persistence.py
"""State Persistence für Kill Switch."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from .state import KillSwitchState


class StatePersistence:
    """
    Persistiert Kill Switch State auf Disk.

    Features:
    - Atomic writes (Crash-safe)
    - Automatic backup
    - State recovery on startup
    """

    def __init__(
        self,
        state_file: str,
        backup_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.state_file = Path(state_file)
        self.backup_dir = Path(backup_dir) if backup_dir else self.state_file.parent / "backups"
        self._logger = logger or logging.getLogger(__name__)

        # Directories erstellen
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        state: KillSwitchState,
        killed_at: Optional[datetime] = None,
        trigger_reason: Optional[str] = None,
    ):
        """
        Speichert aktuellen State.

        Args:
            state: Aktueller Kill Switch State
            killed_at: Zeitpunkt des Triggers (falls KILLED)
            trigger_reason: Grund für Trigger
        """
        data = {
            "state": state.name,
            "saved_at": datetime.utcnow().isoformat(),
            "killed_at": killed_at.isoformat() if killed_at else None,
            "trigger_reason": trigger_reason,
            "version": "1.0",
        }

        # Atomic write: tmp → rename
        tmp_file = self.state_file.with_suffix(".tmp")

        try:
            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=2)

            # Backup existierende Datei
            if self.state_file.exists():
                backup_name = f"state_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy(self.state_file, self.backup_dir / backup_name)

            # Atomic rename
            tmp_file.rename(self.state_file)

            self._logger.debug(f"State saved: {state.name}")

        except Exception as e:
            self._logger.error(f"Failed to save state: {e}")
            if tmp_file.exists():
                tmp_file.unlink()
            raise

    def load(self) -> Optional[dict]:
        """
        Lädt gespeicherten State.

        Returns:
            State-Dict oder None wenn nicht vorhanden
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file) as f:
                data = json.load(f)

            self._logger.info(f"State loaded: {data.get('state')}")
            return data

        except json.JSONDecodeError as e:
            self._logger.error(f"Corrupt state file: {e}")
            return None

    def clear(self):
        """Löscht gespeicherten State."""
        if self.state_file.exists():
            self.state_file.unlink()
            self._logger.info("State cleared")
```

```python
# src/risk_layer/kill_switch/audit.py
"""Audit Trail für Kill Switch Events."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging
import gzip
import shutil

from .state import KillSwitchEvent


class AuditTrail:
    """
    Append-only Audit Log für Kill Switch Events.

    Features:
    - JSONL Format (ein Event pro Zeile)
    - Automatische Rotation
    - Retention Policy
    - Compression für alte Logs
    """

    def __init__(
        self,
        audit_dir: str,
        retention_days: int = 90,
        max_file_size_mb: int = 10,
        logger: Optional[logging.Logger] = None,
    ):
        self.audit_dir = Path(audit_dir)
        self.retention_days = retention_days
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self._logger = logger or logging.getLogger(__name__)

        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = self._get_current_file()

    def _get_current_file(self) -> Path:
        """Gibt aktuelle Audit-Datei zurück."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.audit_dir / f"kill_switch_audit_{today}.jsonl"

    def log_event(self, event: KillSwitchEvent):
        """
        Loggt ein Event in den Audit Trail.

        Args:
            event: Kill Switch Event
        """
        # Prüfe ob Rotation nötig
        self._maybe_rotate()

        # Event serialisieren
        event_data = {
            "timestamp": event.timestamp.isoformat(),
            "previous_state": event.previous_state.name,
            "new_state": event.new_state.name,
            "trigger_reason": event.trigger_reason,
            "triggered_by": event.triggered_by,
            "metadata": event.metadata,
        }

        # Append to file
        with open(self._current_file, "a") as f:
            f.write(json.dumps(event_data) + "\n")

        self._logger.debug(f"Audit event logged: {event.new_state.name}")

    def get_events(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        Liest Events aus dem Audit Trail.

        Args:
            since: Events ab diesem Zeitpunkt
            until: Events bis zu diesem Zeitpunkt
            limit: Maximale Anzahl Events

        Returns:
            Liste von Event-Dicts
        """
        events = []

        # Alle relevanten Dateien finden
        for audit_file in sorted(self.audit_dir.glob("kill_switch_audit_*.jsonl")):
            with open(audit_file) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event["timestamp"])

                        if since and event_time < since:
                            continue
                        if until and event_time > until:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            return events

                    except json.JSONDecodeError:
                        continue

        return events

    def _maybe_rotate(self):
        """Rotiert Datei wenn nötig."""
        # Check ob neue Datei für neuen Tag
        new_file = self._get_current_file()
        if new_file != self._current_file:
            self._compress_old_file(self._current_file)
            self._current_file = new_file

        # Check Dateigröße
        if self._current_file.exists():
            if self._current_file.stat().st_size > self.max_file_size_bytes:
                # Rotate mit Suffix
                suffix = datetime.utcnow().strftime("%H%M%S")
                rotated = self._current_file.with_suffix(f".{suffix}.jsonl")
                self._current_file.rename(rotated)
                self._compress_old_file(rotated)

    def _compress_old_file(self, file: Path):
        """Komprimiert alte Audit-Datei."""
        if not file.exists():
            return

        gz_file = file.with_suffix(file.suffix + ".gz")
        with open(file, 'rb') as f_in:
            with gzip.open(gz_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        file.unlink()
        self._logger.debug(f"Compressed: {file.name}")

    def cleanup_old_files(self):
        """Löscht Dateien älter als Retention Period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)

        for file in self.audit_dir.glob("kill_switch_audit_*"):
            try:
                # Datum aus Dateiname extrahieren
                date_str = file.stem.split("_")[-1].split(".")[0]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff:
                    file.unlink()
                    self._logger.info(f"Deleted old audit file: {file.name}")

            except (ValueError, IndexError):
                continue
```

### 4.4 Acceptance Criteria

- [ ] State Persistence mit atomic writes
- [ ] Automatic backup vor überschreiben
- [ ] State recovery on startup
- [ ] Append-only Audit Log (JSONL)
- [ ] Automatische Log-Rotation (daily + size)
- [ ] Retention Policy (90 Tage)
- [ ] Compression für alte Logs
- [ ] Query-API für Events
- [ ] Unit Tests für Persistence
- [ ] Unit Tests für Audit Trail

---

## 🔵 Phase 5: Integration & API

**Ziel:** Nahtlose Integration in Peak_Trade und externes API.

**Dauer:** 3-4 Tage

### 5.1 Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION POINTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   RISK LAYER                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Layer 1  │→ │ Layer 2  │→ │ Layer 3  │→ │ Layer 4  │ │   │
│  │  │Pre-Trade │  │ Position │  │Portfolio │  │Kill Switch│ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              EXECUTION LAYER                             │   │
│  │  check_kill_switch() → BLOCK if killed                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CLI / API                                   │   │
│  │  • kill_switch status                                   │   │
│  │  • kill_switch trigger --reason "..."                   │   │
│  │  • kill_switch recover --code "..."                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `src/risk_layer/kill_switch/cli.py` | CLI Commands |

**Geplant (TODO):**
- integration.py - Integration mit Risk Layer
- api.py - REST API (optional)
- execution_gate.py - Kill Switch Gate für Execution
- kill_switch_ctl.sh - Operator Control Script

### 5.3 CLI Interface

```bash
# Kill Switch Control CLI

# Status abfragen
python3 -m peak_trade.risk.kill_switch status
# Output:
# ┌────────────────────────────────────────┐
# │ KILL SWITCH STATUS                     │
# ├────────────────────────────────────────┤
# │ State:         🟢 ACTIVE               │
# │ Last Trigger:  -                       │
# │ Uptime:        3d 14h 22m              │
# │ Triggers:      Drawdown: ✓  Daily: ✓   │
# └────────────────────────────────────────┘

# Manueller Trigger
python3 -m peak_trade.risk.kill_switch trigger \
  --reason "Manual stop for maintenance" \
  --confirm

# Recovery starten
python3 -m peak_trade.risk.kill_switch recover \
  --code "EMERGENCY_RECOVERY_2025" \
  --reason "Maintenance complete"

# Audit Trail anzeigen
python3 -m peak_trade.risk.kill_switch audit \
  --since "2025-01-01" \
  --limit 50

# Health Check
python3 -m peak_trade.risk.kill_switch health
```

### 5.4 Execution Gate

```python
# src/live/execution_gate.py
"""Execution Gate mit Kill Switch Integration."""

from typing import Optional
from src.risk.kill_switch import KillSwitch


class TradingBlockedError(Exception):
    """Trading ist durch Kill Switch blockiert."""
    pass


class ExecutionGate:
    """
    Gate für Order-Execution.

    Prüft Kill Switch vor jeder Order-Ausführung.
    """

    def __init__(self, kill_switch: KillSwitch):
        self._kill_switch = kill_switch

    def check_can_execute(self) -> bool:
        """
        Prüft ob Execution erlaubt ist.

        Returns:
            True wenn erlaubt

        Raises:
            TradingBlockedError wenn Kill Switch aktiv
        """
        if self._kill_switch.check_and_block():
            raise TradingBlockedError(
                f"Trading blocked: Kill Switch is {self._kill_switch.state.name}"
            )
        return True

    def execute_with_gate(self, order_func, *args, **kwargs):
        """
        Führt Order-Funktion mit Gate aus.

        Args:
            order_func: Funktion die Order ausführt
            *args, **kwargs: Argumente für order_func

        Returns:
            Ergebnis von order_func

        Raises:
            TradingBlockedError wenn blockiert
        """
        self.check_can_execute()
        return order_func(*args, **kwargs)
```

### 5.5 Acceptance Criteria

- [ ] Integration mit RiskManager (Layer 1-3)
- [ ] Execution Gate für Live-Trading
- [ ] CLI Commands (status, trigger, recover, audit, health)
- [ ] Operator Control Script (Bash)
- [ ] Event Callbacks für andere Module
- [ ] Position Limit Factor Integration (Gradual Restart)
- [ ] Integration Tests für kompletten Flow

---

## 🟣 Phase 6: Testing & Chaos Engineering

**Ziel:** Robuste Tests und Validierung unter Stress.

**Dauer:** 4-5 Tage

### 6.1 Test-Strategie

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      ┌───────────┐                             │
│                      │   E2E     │  ← Chaos Engineering        │
│                      │   Tests   │    Failure Injection        │
│                      └─────┬─────┘                             │
│                   ┌────────┴────────┐                          │
│                   │  Integration    │  ← Multi-Layer Tests     │
│                   │     Tests       │    Recovery Workflows    │
│                   └────────┬────────┘                          │
│             ┌──────────────┴──────────────┐                    │
│             │        Unit Tests           │  ← State Machine   │
│             │                             │    Triggers        │
│             │                             │    Persistence     │
│             └─────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `tests/risk_layer/kill_switch/test_state_machine.py` | State Machine Unit Tests |
| `tests/risk_layer/kill_switch/test_triggers.py` | Trigger Unit Tests |
| `tests/risk_layer/kill_switch/test_recovery.py` | Recovery Unit Tests |
| `tests/risk_layer/kill_switch/test_persistence.py` | Persistence Unit Tests |
| `tests/risk_layer/kill_switch/test_integration.py` | Integration Tests |

**Geplant (TODO):**
- test_chaos.py - Chaos Engineering Tests
- kill_switch_chaos_test.sh - Chaos Test Runner

### 6.3 Chaos Engineering Szenarien

```python
# tests/risk_layer/kill_switch/test_chaos.py
"""Chaos Engineering Tests für Kill Switch."""

import pytest
import threading
import time
import random
from unittest.mock import patch


class TestChaosScenarios:
    """Chaos Engineering Tests."""

    def test_concurrent_triggers(self, kill_switch):
        """
        Szenario: Mehrere gleichzeitige Trigger.

        Validiert:
        - Thread-Safety
        - State-Konsistenz
        - Keine Race Conditions
        """
        results = []

        def trigger_worker(reason):
            result = kill_switch.trigger(reason)
            results.append((reason, result))

        # 10 parallele Trigger
        threads = [
            threading.Thread(target=trigger_worker, args=(f"Trigger-{i}",))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Genau ein Trigger sollte "erfolgreich" sein (first trigger)
        # Alle anderen sollten True zurückgeben (already killed)
        assert kill_switch.is_killed
        assert all(r[1] for r in results)  # Alle True

    def test_trigger_during_recovery(self, kill_switch):
        """
        Szenario: Trigger während Recovery-Phase.

        Validiert:
        - Recovery wird abgebrochen
        - Zurück zu KILLED State
        """
        kill_switch.trigger("Initial")
        kill_switch.request_recovery("operator")

        assert kill_switch.state.name == "RECOVERING"

        # Trigger während Recovery
        kill_switch.trigger("New Emergency")

        assert kill_switch.state.name == "KILLED"

    def test_persistence_crash_recovery(self, kill_switch, tmp_path):
        """
        Szenario: Crash während State-Änderung.

        Validiert:
        - State Recovery nach Crash
        - Keine korrupten Dateien
        """
        from src.risk.kill_switch.persistence import StatePersistence

        persistence = StatePersistence(str(tmp_path / "state.json"))

        # Trigger und speichern
        kill_switch.trigger("Pre-Crash")
        persistence.save(kill_switch.state, trigger_reason="Pre-Crash")

        # Simulate Crash: Neue Instanz
        new_switch = create_kill_switch()
        loaded = persistence.load()

        assert loaded["state"] == "KILLED"
        assert loaded["trigger_reason"] == "Pre-Crash"

    def test_watchdog_missed_heartbeats(self, watchdog_trigger):
        """
        Szenario: System hängt, kein Heartbeat.

        Validiert:
        - Watchdog erkennt missed heartbeats
        - Trigger nach max_missed
        """
        # Simulate: Kein Heartbeat
        for _ in range(5):
            result = watchdog_trigger.check({})
            if result.should_trigger:
                break
            time.sleep(0.1)

        assert result.should_trigger
        assert "heartbeat" in result.reason.lower()

    def test_rapid_kill_recover_cycles(self, kill_switch):
        """
        Szenario: Schnelle Kill/Recover Zyklen.

        Validiert:
        - Cooldown wird respektiert
        - State-Konsistenz
        - Keine Memory Leaks
        """
        for i in range(100):
            kill_switch.trigger(f"Cycle-{i}")
            kill_switch.request_recovery("operator")

            # Cooldown erzwingen
            with patch.object(kill_switch, "_recovery_cooldown", 0):
                kill_switch.complete_recovery()

        assert kill_switch.is_active
        assert len(kill_switch.get_audit_trail()) == 300  # 3 Events pro Zyklus
```

### 6.4 Acceptance Criteria

- [ ] Unit Test Coverage > 90%
- [ ] Integration Tests für alle Workflows
- [ ] Chaos Tests für Concurrency
- [ ] Chaos Tests für Crash Recovery
- [ ] Chaos Tests für Rapid Cycles
- [ ] Performance Tests (10k Triggers)
- [ ] Memory Leak Tests
- [ ] Stress Tests unter Last

---

## ⚪ Phase 7: Dokumentation & Runbooks

**Ziel:** Vollständige Operator-Dokumentation.

**Dauer:** 2-3 Tage

### 7.1 Deliverables

| Datei | Beschreibung |
|-------|--------------|
| `docs/risk/KILL_SWITCH.md` | Technische Dokumentation |
| `docs/ops/KILL_SWITCH_RUNBOOK.md` | Operator Runbook |
| `docs/ops/KILL_SWITCH_TROUBLESHOOTING.md` | Troubleshooting Guide |
| `docs/risk/KILL_SWITCH_ARCHITECTURE.md` | Architektur-Diagramme |

### 7.2 Runbook-Inhalte

```markdown
# Kill Switch Operator Runbook

## Emergency Procedures

### 🚨 Manueller Kill Switch Trigger

**Wann:**
- Verdächtiges Marktverhalten
- System-Anomalien
- Geplante Wartung

**Schritte:**
1. Terminal öffnen
2. `cd ~/Peak_Trade && source .venv/bin/activate`
3. `python3 -m peak_trade.risk.kill_switch trigger --reason "GRUND" --confirm`
4. Bestätigung abwarten
5. Status prüfen: `python3 -m peak_trade.risk.kill_switch status`

### 🔄 Recovery nach Kill Switch

**Voraussetzungen:**
- Kill Switch ist im KILLED State
- Trigger-Grund wurde behoben
- System Health ist OK

**Schritte:**
1. Health Check: `python3 -m peak_trade.risk.kill_switch health`
2. Recovery starten:
   ```bash
   python3 -m peak_trade.risk.kill_switch recover \
     --code "EMERGENCY_RECOVERY_2025" \
     --reason "Wartung abgeschlossen"
   ```
3. Cooldown abwarten (5 Minuten)
4. Status prüfen: Position Limits sind zunächst bei 50%
5. Nach 1h: Position Limits auf 75%
6. Nach 2h: Position Limits auf 100%

### 📊 Audit Trail prüfen

```bash
# Letzte 50 Events
python3 -m peak_trade.risk.kill_switch audit --limit 50

# Events der letzten 24h
python3 -m peak_trade.risk.kill_switch audit --since "$(date -v-1d +%Y-%m-%d)"
```
```

### 7.3 Acceptance Criteria

- [ ] Technische Dokumentation vollständig
- [ ] Operator Runbook mit Schritt-für-Schritt
- [ ] Troubleshooting Guide mit häufigen Problemen
- [ ] Architektur-Diagramme (Mermaid/PlantUML)
- [ ] CLI Command Reference
- [ ] API Reference (falls REST API)
- [ ] Beispiel-Konfigurationen

---

## 📈 Metriken & Success Criteria

### MVP Success Criteria

| Kriterium | Ziel | Messung |
|-----------|------|---------|
| State Machine Robustheit | 100% | Unit Test Coverage |
| Trigger Latency | < 100ms | Performance Test |
| Recovery Time | < 10 Minuten | Integration Test |
| Audit Completeness | 100% Events | Audit Test |
| Crash Recovery | 100% | Chaos Test |
| Documentation | 100% | Review |

### Post-MVP Metriken

| Metrik | Tracking |
|--------|----------|
| False Positive Rate | Trigger ohne echten Notfall |
| Mean Time to Recover | Zeit von KILLED zu ACTIVE |
| Trigger Response Time | Zeit bis System tatsächlich stoppt |
| Audit Query Performance | Zeit für Audit-Abfragen |

---

## ⚠️ Risiken & Mitigations

| Risiko | Impact | Wahrscheinlichkeit | Mitigation |
|--------|--------|-------------------|------------|
| Kill Switch selbst versagt | KRITISCH | Niedrig | Watchdog, separate Instanz |
| False Positives | Mittel | Mittel | Tunable Thresholds, Cooldowns |
| Recovery zu früh | Hoch | Niedrig | Cooldown, Approval Code |
| Audit Log korrupt | Mittel | Niedrig | Append-only, Backups |
| Concurrent Access Issues | Hoch | Mittel | RLock, Thread-Safety Tests |

---

## 🎯 Zusammenfassung

**Emergency Kill Switch** ist Layer 4 der Defense-in-Depth Architektur und die **letzte Verteidigungslinie** gegen unkontrollierte Trading-Verluste.

**Key Features:**
- ✅ Robuste State Machine (ACTIVE → KILLED → RECOVERING → ACTIVE)
- ✅ Multiple Trigger-Mechanismen (Threshold, Watchdog, Manual, External)
- ✅ Kontrollierte Recovery (Approval, Cooldown, Gradual Restart)
- ✅ Persistenter State (Crash-safe)
- ✅ Lückenloser Audit Trail
- ✅ CLI & API Integration
- ✅ Chaos Engineering validiert

**Timeline:** 4-5 Wochen für vollständige Implementierung

**Priorität:** 🔴 KRITISCH – Blocker für jegliches Live-Trading

---

**Erstellt von:** Peak_Risk (Chief Risk Officer)  
**Reviewed by:** Peak_Trade Lead Engineer  
**Status:** 📋 GEPLANT – Bereit für Implementation
