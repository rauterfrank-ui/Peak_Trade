# PR0: Integration Architecture & Public API

**Agent:** A (Architecture/Integration)  
**Datum:** 2025-12-28  
**Status:** 📋 BEREIT FÜR IMPLEMENTATION  
**PR-Titel:** `feat(risk): add integration architecture and public API for risk layer roadmap`

---

## 🎯 Ziel

Minimaler PR0 zur Vorbereitung der Risk Layer Roadmap-Implementation:
- Public API Types definieren
- Integration Points spezifizieren
- Compatibility Layer für beide Risk-Systeme
- Test-Scaffolding

**Prinzip:** Kleine, reviewbare Changes. Keine Breaking Changes.

---

## 📊 Repo-Inventar (Zusammenfassung)

Basierend auf der vollständigen Inventarisierung:

### Bestehende Risk-Module

```
src/risk/                          # Risk Layer v1.0 (Agent A6)
├── var.py                         # VaR/CVaR (Historical, Parametric)
├── component_var.py               # Marginal/Incremental VaR
├── monte_carlo.py                 # Monte Carlo VaR
├── stress_tester.py               # Stress Testing
└── risk_layer_manager.py          # Orchestrator

src/risk_layer/                    # Defense-in-Depth (Neuere Architektur)
├── kill_switch/                   # Kill Switch (97% fertig)
├── var_backtest/                  # VaR Validation (100% fertig)
├── alerting/                      # Alerting (100% fertig)
└── risk_gate.py                   # Risk Gate

src/core/risk.py                   # Integration Layer (BacktestEngine)
```

### Config-Patterns

```python
# Standard Pattern im Repo
from src.core.peak_config import load_config

cfg = load_config()  # Lädt config/config.toml
value = cfg.get("risk_layer_v1.var.window", 252)  # Dot-notation
```

### Alerting/Notifications

```
src/risk_layer/alerting/           # Vollständig implementiert!
├── alert_manager.py
├── alert_dispatcher.py
└── channels/                      # Console, Email, Slack, Telegram, Webhook
```

### Audit Logging

```
src/risk_layer/audit_log.py        # AuditLogWriter
src/risk_layer/kill_switch/audit.py  # Kill Switch Audit Trail
```

---

## 🏗️ Architektur-Entscheidungen (Final)

### 1. Kanonischer Package-Pfad

**Entscheidung:** `src/risk_layer/` ist primärer Pfad für **neue Features**.

**Begründung:**
- Neuere Defense-in-Depth Architektur
- Kill Switch, VaR Backtest, Alerting bereits dort
- Bessere Trennung von Concerns

**Compatibility:**
- `src/risk/` bleibt functional (keine Breaking Changes)
- Neue Features werden via Re-Exports in `src/risk/__init__.py` verfügbar gemacht

### 2. Public API Struktur

**Hierarchie:**
```
src/risk_layer/
├── __init__.py                    # Main Public API
├── types.py                       # Gemeinsame Types (ERWEITERT)
├── exceptions.py                  # Risk Layer Exceptions (NEU)
│
├── var_backtest/
│   └── __init__.py                # VaR Backtest API (bereits vorhanden)
│
├── attribution/                   # NEU (Agent D)
│   └── __init__.py                # Attribution API
│
├── stress/                        # NEU (Agent E)
│   └── __init__.py                # Stress Testing API
│
└── kill_switch/
    └── __init__.py                # Kill Switch API (bereits vorhanden)
```

### 3. Integration Points

**Minimal Wiring:**
- Keine erzwungene Integration in BacktestEngine
- Opt-in via Config-Flags
- Adapter-Pattern für bestehende RiskManager

---

## 📦 PR0 Deliverables

### 1. Erweiterte Types (`src/risk_layer/types.py`)

**Datei:** `src/risk_layer/types.py` (ERWEITERN)

```python
"""
Risk Layer Types - Unified API
================================

Erweitert die bestehenden Types um neue Roadmap-Features.

Existing Types (bleiben unverändert):
- Violation
- RiskDecision
- RiskResult
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd

# ============================================================================
# Existing Types (aus models.py, NICHT ändern)
# ============================================================================
# Diese werden aus models.py importiert, hier nur zur Dokumentation

# from .models import Violation, RiskDecision, RiskResult


# ============================================================================
# VaR Backtest Types (bereits in var_backtest/kupiec_pof.py)
# ============================================================================
# Diese existieren bereits, hier nur Dokumentation

# from .var_backtest import KupiecPOFOutput, KupiecResult
# from .var_backtest import ChristoffersenResult, TrafficLightZone


# ============================================================================
# NEW: Attribution Types (für Agent D)
# ============================================================================

@dataclass(frozen=True)
class ComponentVaR:
    """Component VaR für eine einzelne Position."""

    asset: str
    weight: float
    marginal_var: float
    component_var: float
    incremental_var: float
    percent_contribution: float

    @property
    def diversification_benefit(self) -> float:
        """Diversifikations-Vorteil: Incremental - Component."""
        return self.incremental_var - self.component_var


@dataclass(frozen=True)
class VaRDecomposition:
    """Vollständige VaR-Zerlegung für Portfolio."""

    portfolio_var: float
    components: Dict[str, ComponentVaR]
    diversification_ratio: float

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert zu DataFrame für Reporting."""
        data = []
        for asset, comp in self.components.items():
            data.append({
                "asset": asset,
                "weight": comp.weight,
                "marginal_var": comp.marginal_var,
                "component_var": comp.component_var,
                "incremental_var": comp.incremental_var,
                "percent_contribution": comp.percent_contribution,
                "diversification_benefit": comp.diversification_benefit,
            })
        return pd.DataFrame(data)


@dataclass(frozen=True)
class PnLAttribution:
    """P&L Attribution für Portfolio."""

    total_pnl: float
    asset_contributions: Dict[str, float]
    factor_contributions: Optional[Dict[str, float]] = None

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert zu DataFrame."""
        data = [
            {"asset": asset, "pnl_contribution": pnl}
            for asset, pnl in self.asset_contributions.items()
        ]
        return pd.DataFrame(data)


# ============================================================================
# NEW: Stress Testing Types (für Agent E)
# ============================================================================

@dataclass(frozen=True)
class StressScenario:
    """Stress-Test-Szenario."""

    name: str
    description: str
    shocks: Dict[str, float]  # {asset: shock_return}
    metadata: Optional[Dict] = None


@dataclass(frozen=True)
class ReverseStressResult:
    """Ergebnis eines Reverse Stress Tests."""

    target_loss: float
    scenarios: List[StressScenario]
    portfolio_value: float
    current_positions: Dict[str, float]

    def to_dataframe(self) -> pd.DataFrame:
        """Konvertiert Szenarien zu DataFrame."""
        data = []
        for scenario in self.scenarios:
            for asset, shock in scenario.shocks.items():
                data.append({
                    "scenario": scenario.name,
                    "asset": asset,
                    "shock_return": shock,
                    "description": scenario.description,
                })
        return pd.DataFrame(data)


@dataclass(frozen=True)
class ForwardStressResult:
    """Ergebnis eines Forward Stress Tests."""

    scenario: StressScenario
    portfolio_loss: float
    portfolio_loss_pct: float
    asset_contributions: Dict[str, float]
    var_breach: bool

    def to_dict(self) -> Dict:
        """Konvertiert zu Dict für Reporting."""
        return {
            "scenario": self.scenario.name,
            "description": self.scenario.description,
            "portfolio_loss": self.portfolio_loss,
            "portfolio_loss_pct": self.portfolio_loss_pct,
            "var_breach": self.var_breach,
            "asset_contributions": self.asset_contributions,
        }


# ============================================================================
# Unified Results (für High-Level API)
# ============================================================================

@dataclass(frozen=True)
class RiskLayerResult:
    """
    Unified Result für vollständige Risk Layer Analyse.

    Enthält alle Komponenten der Risk Layer Roadmap.
    """

    # VaR Core (bereits vorhanden)
    var: Optional[float] = None
    cvar: Optional[float] = None

    # VaR Validation (bereits vorhanden)
    kupiec_result: Optional[object] = None  # KupiecPOFOutput
    traffic_light: Optional[str] = None     # TrafficLightZone

    # Attribution (NEU)
    var_decomposition: Optional[VaRDecomposition] = None
    pnl_attribution: Optional[PnLAttribution] = None

    # Stress Testing (NEU + erweitert)
    stress_results: Optional[List[ForwardStressResult]] = None
    reverse_stress: Optional[ReverseStressResult] = None

    # Kill Switch (bereits vorhanden)
    kill_switch_active: bool = False

    # Metadata
    timestamp: datetime = None
    portfolio_value: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

    def summary(self) -> Dict:
        """Kompakte Zusammenfassung für Logging."""
        return {
            "var": self.var,
            "cvar": self.cvar,
            "kill_switch_active": self.kill_switch_active,
            "has_attribution": self.var_decomposition is not None,
            "has_stress": self.stress_results is not None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# ============================================================================
# Sign Convention Helpers
# ============================================================================

def validate_var_positive(var: float, name: str = "VaR") -> None:
    """
    Validiert dass VaR als positive Zahl vorliegt.

    Convention: VaR ist IMMER positiv (potentieller Verlust).

    Raises:
        ValueError: Wenn VaR negativ
    """
    if var < 0:
        raise ValueError(
            f"{name} muss positiv sein (potentieller Verlust). "
            f"Erhalten: {var}. "
            f"Tipp: Verwende abs() oder negiere das Ergebnis."
        )


def validate_confidence_level(confidence: float) -> None:
    """
    Validiert Confidence Level (0, 1).

    Raises:
        ValueError: Wenn außerhalb (0, 1)
    """
    if not 0 < confidence < 1:
        raise ValueError(
            f"Confidence Level muss in (0, 1) liegen. Erhalten: {confidence}"
        )
```

---

### 2. Exceptions (`src/risk_layer/exceptions.py`)

**Datei:** `src/risk_layer/exceptions.py` (NEU)

```python
"""
Risk Layer Exceptions
======================

Unified exception hierarchy for Risk Layer.
"""


class RiskLayerError(Exception):
    """Base exception for all Risk Layer errors."""
    pass


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(RiskLayerError):
    """Input validation failed."""
    pass


class InsufficientDataError(RiskLayerError):
    """Not enough data for calculation."""

    def __init__(self, required: int, actual: int, message: str = ""):
        self.required = required
        self.actual = actual
        msg = f"Insufficient data: required {required}, got {actual}"
        if message:
            msg = f"{msg}. {message}"
        super().__init__(msg)


class ConfigurationError(RiskLayerError):
    """Configuration is invalid or missing."""
    pass


# ============================================================================
# Calculation Errors
# ============================================================================

class CalculationError(RiskLayerError):
    """Calculation failed."""
    pass


class ConvergenceError(CalculationError):
    """Optimization did not converge."""

    def __init__(self, message: str = "Optimization failed to converge"):
        super().__init__(message)


class NumericalError(CalculationError):
    """Numerical instability detected."""
    pass


# ============================================================================
# Integration Errors
# ============================================================================

class IntegrationError(RiskLayerError):
    """Integration with other systems failed."""
    pass


class TradingBlockedError(RiskLayerError):
    """Trading is blocked by Risk Layer."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Trading blocked: {reason}")


# ============================================================================
# Kill Switch Errors
# ============================================================================

class KillSwitchError(RiskLayerError):
    """Kill Switch specific error."""
    pass


class InvalidStateTransitionError(KillSwitchError):
    """Invalid Kill Switch state transition."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: {from_state} → {to_state}"
        )
```

---

### 3. Public API Exports (`src/risk_layer/__init__.py`)

**Datei:** `src/risk_layer/__init__.py` (ERWEITERN)

```python
"""
Risk Layer Core Module
=======================

Public API für alle Risk Layer Features.

Usage:
    from src.risk_layer import (
        # Core Types
        RiskDecision, RiskResult, Violation,

        # VaR Backtest
        kupiec_pof_test, KupiecPOFOutput,

        # Attribution (NEU)
        VaRDecomposition, ComponentVaR, PnLAttribution,

        # Stress Testing (NEU)
        StressScenario, ReverseStressResult, ForwardStressResult,

        # Kill Switch
        KillSwitch, KillSwitchState, ExecutionGate,

        # Alerting
        AlertManager, AlertSeverity,

        # Exceptions
        RiskLayerError, TradingBlockedError,
    )
"""

# ============================================================================
# Core Models (bereits vorhanden)
# ============================================================================
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.risk_gate import RiskGate

# ============================================================================
# Kill Switch (bereits vorhanden)
# ============================================================================
from src.risk_layer.kill_switch import KillSwitch, KillSwitchState, ExecutionGate

# ============================================================================
# VaR Backtest (bereits vorhanden)
# ============================================================================
from src.risk_layer.var_backtest import (
    kupiec_pof_test,
    KupiecPOFOutput,
    KupiecResult,
)

# Christoffersen & Traffic Light (optional, wenn benötigt)
try:
    from src.risk_layer.var_backtest import (
        christoffersen_independence_test,
        traffic_light_test,
        TrafficLightZone,
    )
except ImportError:
    pass  # Optional features

# ============================================================================
# Alerting (bereits vorhanden)
# ============================================================================
# Import available but not in __all__ to keep core API minimal
# Use: from src.risk_layer.alerting import AlertManager, AlertSeverity

# ============================================================================
# NEW: Attribution Types (für Agent D)
# ============================================================================
from src.risk_layer.types import (
    ComponentVaR,
    VaRDecomposition,
    PnLAttribution,
)

# ============================================================================
# NEW: Stress Testing Types (für Agent E)
# ============================================================================
from src.risk_layer.types import (
    StressScenario,
    ReverseStressResult,
    ForwardStressResult,
)

# ============================================================================
# NEW: Unified Results
# ============================================================================
from src.risk_layer.types import RiskLayerResult

# ============================================================================
# NEW: Exceptions
# ============================================================================
from src.risk_layer.exceptions import (
    RiskLayerError,
    ValidationError,
    InsufficientDataError,
    ConfigurationError,
    CalculationError,
    ConvergenceError,
    TradingBlockedError,
    KillSwitchError,
    InvalidStateTransitionError,
)

# ============================================================================
# Legacy Aliases (Backward Compatibility)
# ============================================================================
KillSwitchLayer = KillSwitch
KillSwitchStatus = KillSwitchState

# ============================================================================
# Public API
# ============================================================================
__all__ = [
    # Core
    "Violation",
    "RiskDecision",
    "RiskResult",
    "RiskLayerResult",
    "AuditLogWriter",
    "RiskGate",

    # Kill Switch
    "KillSwitch",
    "KillSwitchState",
    "ExecutionGate",
    "KillSwitchLayer",  # Legacy
    "KillSwitchStatus",  # Legacy

    # VaR Backtest
    "kupiec_pof_test",
    "KupiecPOFOutput",
    "KupiecResult",

    # Attribution (NEU)
    "ComponentVaR",
    "VaRDecomposition",
    "PnLAttribution",

    # Stress Testing (NEU)
    "StressScenario",
    "ReverseStressResult",
    "ForwardStressResult",

    # Exceptions
    "RiskLayerError",
    "ValidationError",
    "InsufficientDataError",
    "ConfigurationError",
    "CalculationError",
    "ConvergenceError",
    "TradingBlockedError",
    "KillSwitchError",
    "InvalidStateTransitionError",
]
```

---

### 4. Compatibility Layer (`src/risk/__init__.py`)

**Datei:** `src/risk/__init__.py` (ERWEITERN)

```python
"""
Risk Module - Compatibility Layer
===================================

Provides backward compatibility and re-exports from risk_layer.

Existing Code (BLEIBT UNVERÄNDERT):
- VaR calculations
- Component VaR
- Monte Carlo
- Stress Testing
- Risk Layer Manager
"""

# ============================================================================
# Existing Exports (UNVERÄNDERT)
# ============================================================================

# VaR Core (bleibt wie es ist)
from src.risk.var import (
    var_historical,
    cvar_historical,
    var_parametric,
    var_ewma,
    # ... andere Funktionen
)

# Component VaR
from src.risk.component_var import (
    ComponentVarCalculator,
    # ... andere
)

# Monte Carlo
from src.risk.monte_carlo import (
    MonteCarloVaRCalculator,
    # ... andere
)

# Risk Layer Manager
from src.risk.risk_layer_manager import (
    RiskLayerManager,
    RiskAssessmentResult,
)

# Enforcement
from src.risk.enforcement import (
    RiskEnforcer,
    RiskLimitsV2,
)

# ============================================================================
# NEW: Re-exports from risk_layer (Compatibility)
# ============================================================================

# VaR Backtest
from src.risk_layer import (
    kupiec_pof_test,
    KupiecPOFOutput,
    KupiecResult,
)

# Attribution
from src.risk_layer import (
    ComponentVaR as ComponentVaRResult,  # Alias to avoid naming conflict
    VaRDecomposition,
    PnLAttribution,
)

# Stress Testing
from src.risk_layer import (
    StressScenario,
    ReverseStressResult,
    ForwardStressResult,
)

# Kill Switch (optional, für direkten Zugriff)
from src.risk_layer import (
    KillSwitch,
    KillSwitchState,
)

# Exceptions
from src.risk_layer import (
    RiskLayerError,
    TradingBlockedError,
)

# ============================================================================
# Public API (ERWEITERT)
# ============================================================================
__all__ = [
    # Existing (UNVERÄNDERT)
    "var_historical",
    "cvar_historical",
    "var_parametric",
    "var_ewma",
    "ComponentVarCalculator",
    "MonteCarloVaRCalculator",
    "RiskLayerManager",
    "RiskAssessmentResult",
    "RiskEnforcer",
    "RiskLimitsV2",

    # NEW: VaR Backtest
    "kupiec_pof_test",
    "KupiecPOFOutput",
    "KupiecResult",

    # NEW: Attribution
    "ComponentVaRResult",
    "VaRDecomposition",
    "PnLAttribution",

    # NEW: Stress Testing
    "StressScenario",
    "ReverseStressResult",
    "ForwardStressResult",

    # NEW: Kill Switch
    "KillSwitch",
    "KillSwitchState",

    # NEW: Exceptions
    "RiskLayerError",
    "TradingBlockedError",
]
```

---

### 5. Integration Adapter (`src/risk_layer/integration.py`)

**Datei:** `src/risk_layer/integration.py` (NEU)

```python
"""
Risk Layer Integration Adapter
================================

Minimal integration layer for BacktestEngine and Risk Managers.

This is an OPT-IN adapter - existing code continues to work without changes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.core.peak_config import PeakConfig
from src.risk_layer import (
    RiskLayerResult,
    KillSwitch,
    kupiec_pof_test,
)

logger = logging.getLogger(__name__)


class RiskLayerAdapter:
    """
    Adapter für Integration von Risk Layer Features.

    Usage:
        >>> from src.core.peak_config import load_config
        >>> from src.risk_layer.integration import RiskLayerAdapter
        >>>
        >>> cfg = load_config()
        >>> adapter = RiskLayerAdapter(cfg)
        >>>
        >>> # Check if trading is allowed
        >>> if adapter.check_trading_allowed():
        ...     # Execute trade
        ...     pass
    """

    def __init__(self, config: PeakConfig):
        """
        Initialize adapter with config.

        Args:
            config: PeakConfig instance
        """
        self.config = config
        self._kill_switch: Optional[KillSwitch] = None

        # Lazy initialization based on config
        self._init_components()

    def _init_components(self):
        """Initialize Risk Layer components based on config."""
        # Kill Switch (optional)
        if self.config.get("risk_layer_v1.kill_switch.enabled", False):
            try:
                from src.risk_layer.kill_switch import KillSwitch
                kill_switch_config = self.config.get("risk_layer_v1.kill_switch", {})
                self._kill_switch = KillSwitch(kill_switch_config)
                logger.info("Kill Switch initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Kill Switch: {e}")

        # Weitere Komponenten können hier hinzugefügt werden

    def check_trading_allowed(self) -> bool:
        """
        Prüft ob Trading erlaubt ist (Kill Switch Check).

        Returns:
            True wenn Trading erlaubt, False wenn blockiert
        """
        if self._kill_switch is None:
            return True  # Kein Kill Switch = Trading erlaubt

        return not self._kill_switch.check_and_block()

    @property
    def kill_switch(self) -> Optional[KillSwitch]:
        """Gibt Kill Switch Instanz zurück (oder None)."""
        return self._kill_switch


def create_risk_layer_adapter(
    config: Optional[PeakConfig] = None,
) -> RiskLayerAdapter:
    """
    Factory function für RiskLayerAdapter.

    Args:
        config: Optional PeakConfig, lädt default wenn None

    Returns:
        RiskLayerAdapter instance
    """
    if config is None:
        from src.core.peak_config import load_config
        config = load_config()

    return RiskLayerAdapter(config)
```

---

### 6. Test Scaffolding

**Datei:** `tests/risk_layer/test_integration_api.py` (NEU)

```python
"""
Integration API Smoke Tests
=============================

Stellt sicher dass die Public API korrekt funktioniert.
"""

import pytest


def test_import_core_types():
    """Test dass Core Types importierbar sind."""
    from src.risk_layer import (
        RiskDecision,
        RiskResult,
        Violation,
        RiskLayerResult,
    )

    # Sollte keine ImportError werfen
    assert RiskDecision is not None
    assert RiskResult is not None
    assert Violation is not None
    assert RiskLayerResult is not None


def test_import_var_backtest():
    """Test dass VaR Backtest API importierbar ist."""
    from src.risk_layer import (
        kupiec_pof_test,
        KupiecPOFOutput,
        KupiecResult,
    )

    assert kupiec_pof_test is not None
    assert KupiecPOFOutput is not None
    assert KupiecResult is not None


def test_import_attribution_types():
    """Test dass Attribution Types importierbar sind."""
    from src.risk_layer import (
        ComponentVaR,
        VaRDecomposition,
        PnLAttribution,
    )

    assert ComponentVaR is not None
    assert VaRDecomposition is not None
    assert PnLAttribution is not None


def test_import_stress_types():
    """Test dass Stress Testing Types importierbar sind."""
    from src.risk_layer import (
        StressScenario,
        ReverseStressResult,
        ForwardStressResult,
    )

    assert StressScenario is not None
    assert ReverseStressResult is not None
    assert ForwardStressResult is not None


def test_import_kill_switch():
    """Test dass Kill Switch importierbar ist."""
    from src.risk_layer import (
        KillSwitch,
        KillSwitchState,
        ExecutionGate,
    )

    assert KillSwitch is not None
    assert KillSwitchState is not None
    assert ExecutionGate is not None


def test_import_exceptions():
    """Test dass Exceptions importierbar sind."""
    from src.risk_layer import (
        RiskLayerError,
        ValidationError,
        TradingBlockedError,
    )

    assert RiskLayerError is not None
    assert ValidationError is not None
    assert TradingBlockedError is not None


def test_backward_compatibility_imports():
    """Test dass backward compatibility imports funktionieren."""
    from src.risk import (
        kupiec_pof_test,
        VaRDecomposition,
        KillSwitch,
    )

    assert kupiec_pof_test is not None
    assert VaRDecomposition is not None
    assert KillSwitch is not None


def test_risk_layer_result_creation():
    """Test RiskLayerResult creation."""
    from src.risk_layer import RiskLayerResult

    result = RiskLayerResult(
        var=1000.0,
        cvar=1500.0,
        kill_switch_active=False,
    )

    assert result.var == 1000.0
    assert result.cvar == 1500.0
    assert result.kill_switch_active is False
    assert result.timestamp is not None

    summary = result.summary()
    assert summary["var"] == 1000.0
    assert summary["kill_switch_active"] is False


def test_integration_adapter_creation():
    """Test RiskLayerAdapter creation."""
    from src.core.peak_config import PeakConfig
    from src.risk_layer.integration import RiskLayerAdapter

    config = PeakConfig(raw={})
    adapter = RiskLayerAdapter(config)

    # Trading sollte erlaubt sein (kein Kill Switch)
    assert adapter.check_trading_allowed() is True

    # Kill Switch sollte None sein (nicht konfiguriert)
    assert adapter.kill_switch is None
```

**Datei:** `tests/risk_layer/test_exceptions.py` (NEU)

```python
"""Tests für Risk Layer Exceptions."""

import pytest
from src.risk_layer import (
    RiskLayerError,
    ValidationError,
    InsufficientDataError,
    TradingBlockedError,
    InvalidStateTransitionError,
)


def test_risk_layer_error_hierarchy():
    """Test Exception-Hierarchie."""
    assert issubclass(ValidationError, RiskLayerError)
    assert issubclass(InsufficientDataError, RiskLayerError)
    assert issubclass(TradingBlockedError, RiskLayerError)


def test_insufficient_data_error():
    """Test InsufficientDataError."""
    error = InsufficientDataError(required=250, actual=100)

    assert error.required == 250
    assert error.actual == 100
    assert "250" in str(error)
    assert "100" in str(error)


def test_trading_blocked_error():
    """Test TradingBlockedError."""
    error = TradingBlockedError("Kill Switch active")

    assert error.reason == "Kill Switch active"
    assert "Kill Switch active" in str(error)


def test_invalid_state_transition_error():
    """Test InvalidStateTransitionError."""
    error = InvalidStateTransitionError("ACTIVE", "RECOVERING")

    assert error.from_state == "ACTIVE"
    assert error.to_state == "RECOVERING"
    assert "ACTIVE" in str(error)
    assert "RECOVERING" in str(error)
```

---

## 📊 PR0 File Changes

### Neue Dateien (CREATE)

```
src/risk_layer/
├── exceptions.py                  # NEU: 150 lines
├── types.py                       # ERWEITERT: +200 lines (NEU: Attribution, Stress Types)
└── integration.py                 # NEU: 100 lines

tests/risk_layer/
├── test_integration_api.py        # NEU: 150 lines
└── test_exceptions.py             # NEU: 50 lines
```

### Modifizierte Dateien (MODIFY)

```
src/risk_layer/__init__.py         # ERWEITERT: +50 lines (neue Exports)
src/risk/__init__.py                # ERWEITERT: +30 lines (Re-exports)
```

**Gesamt:** ~680 Lines Code (klein, reviewbar!)

---

## 🧪 Test-Strategie

### Smoke Tests (PR0)
- ✅ Import-Tests für alle Public API Types
- ✅ Exception-Tests
- ✅ RiskLayerResult Creation
- ✅ Backward Compatibility Imports
- ✅ Integration Adapter Creation

### Keine Unit Tests für Implementierung
- PR0 enthält nur Types/Scaffolding
- Implementierung wird in Agent D/E/F PRs getestet

---

## 📝 Config Schema Dokumentation

**Datei:** `docs/risk/CONFIG_SCHEMA.md` (NEU)

```markdown
# Risk Layer Configuration Schema

## Overview

Risk Layer verwendet `config/config.toml` als Haupt-Config.

## Structure

### VaR Configuration

```toml
[risk_layer_v1.var]
methods = ["historical", "parametric", "ewma"]
confidence_level = 0.95
window = 252
```

### VaR Backtest Configuration

```toml
[risk_layer_v1.backtest]
enabled = true
min_observations = 250
significance_level = 0.05
```

### Attribution Configuration (NEU)

```toml
[risk_layer_v1.attribution]
enabled = true
method = "parametric"  # oder "historical"
compute_incremental = true  # Numerisch teuer
```

### Stress Testing Configuration (NEU)

```toml
[risk_layer_v1.stress]
enabled = true
scenarios_dir = "config/scenarios"

[risk_layer_v1.stress.reverse]
enabled = true
max_shock = 0.50  # Max 50% Shock
min_shock = -0.50

[risk_layer_v1.stress.forward]
enabled = true
predefined_scenarios = ["crypto_crash", "flash_crash", "regulatory_shock"]
```

### Kill Switch Configuration

```toml
[risk_layer_v1.kill_switch]
enabled = true
mode = "active"  # oder "disabled" (Backtest)
recovery_cooldown_seconds = 300
```

## Sign Conventions

- **VaR/CVaR:** IMMER positiv (potentieller Verlust)
- **Returns:** Können positiv/negativ sein
- **Shocks:** Können positiv/negativ sein (+ = Gewinn, - = Verlust)
```

---

## 🚀 PR Description

**Titel:** `feat(risk): add integration architecture and public API for risk layer roadmap`

**Labels:** `enhancement`, `risk`, `architecture`

**Beschreibung:**

```markdown
## 🎯 Ziel

PR0 zur Vorbereitung der Risk Layer Roadmap-Implementation:
- Unified Public API Types
- Integration Architecture
- Backward Compatibility Layer
- Test Scaffolding

## ✨ Änderungen

### 1. Neue Types (`src/risk_layer/types.py`)
- Attribution Types: `ComponentVaR`, `VaRDecomposition`, `PnLAttribution`
- Stress Testing Types: `StressScenario`, `ReverseStressResult`, `ForwardStressResult`
- Unified Result: `RiskLayerResult`
- Sign Convention Helpers

### 2. Exception Hierarchy (`src/risk_layer/exceptions.py`)
- `RiskLayerError` als Base
- `ValidationError`, `InsufficientDataError`, `ConfigurationError`
- `CalculationError`, `ConvergenceError`
- `TradingBlockedError`, `KillSwitchError`

### 3. Public API Exports
- Erweiterte `src/risk_layer/__init__.py` mit neuen Types
- Backward Compatibility in `src/risk/__init__.py`

### 4. Integration Adapter (`src/risk_layer/integration.py`)
- Minimal Wiring für BacktestEngine
- Opt-in Integration (keine Breaking Changes)

## 🧪 Tests

- ✅ Smoke Tests für alle Public API Imports
- ✅ Exception Tests
- ✅ RiskLayerResult Creation Tests
- ✅ Backward Compatibility Tests

## 📚 Dokumentation

- ✅ Config Schema Dokumentation (`docs/risk/CONFIG_SCHEMA.md`)
- ✅ Integration Architecture Doc (`docs/risk/PR0_INTEGRATION_ARCHITECTURE.md`)

## ⚠️ Nicht-Breaking

- Alle bestehenden Imports funktionieren weiter
- Neue Features sind opt-in
- Backward Compatibility via Re-Exports

## 📊 Stats

- **Neue Dateien:** 5
- **Modifizierte Dateien:** 2
- **Lines of Code:** ~680
- **Tests:** 2 neue Test-Files

## 🔗 Related

- Alignment Doc: `docs/risk/RISK_LAYER_ROADMAP_ALIGNMENT.md`
- Roadmap: `docs/risk/roadmaps/ROADMAP_EMERGENCY_KILL_SWITCH.md`
```

---

## ✅ Acceptance Criteria

- [ ] Alle neuen Types sind importierbar
- [ ] Exception-Hierarchie ist vollständig
- [ ] Public API Exports sind korrekt
- [ ] Backward Compatibility funktioniert
- [ ] Smoke Tests passing (100%)
- [ ] Keine Breaking Changes
- [ ] Dokumentation vollständig

---

## ⏱️ Aufwand

**Geschätzt:** 3-4 Stunden

| Task | Zeit |
|------|------|
| Types definieren | 1h |
| Exceptions implementieren | 0.5h |
| API Exports | 0.5h |
| Integration Adapter | 1h |
| Tests schreiben | 0.5h |
| Dokumentation | 0.5h |

---

## 🚦 Next Steps nach PR0

Nach Merge von PR0:

1. **Agent F:** Kill Switch CLI Polish (1 Tag)
2. **Agent D:** Attribution Implementation (5-7 Tage)
3. **Agent E:** Stress Testing Implementation (3-4 Tage)

---

**Erstellt von:** Agent A (Architecture/Integration)  
**Status:** 📋 BEREIT FÜR IMPLEMENTATION  
**Datum:** 2025-12-28
