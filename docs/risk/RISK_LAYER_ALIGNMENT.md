# Risk Layer v1.0 - Repository Alignment Decision

**Agent:** A0 (Architect & Repo Alignment)  
**Datum:** 2025-12-28  
**Status:** FINAL

---

## Executive Summary

Die Risk Layer v1.0 Roadmap wird in das **bestehende Dual-Package-System** integriert:
- `src/risk/` = Core Risk Calculations & Analytics
- `src/risk_layer/` = Execution Layer (Gates, Enforcement, Backtesting)

Keine Breaking Changes. Alle bestehenden Tests bleiben kompatibel.

---

## 1. Package Location Decision

### ENTSCHEIDUNG: Dual-Package-System beibehalten

**Rationale:**
- Beide Packages (`src/risk/` und `src/risk_layer/`) existieren bereits und sind etabliert
- Klare Trennung der Verantwortlichkeiten (Separation of Concerns):
  - `src/risk/` = "Was berechnen wir?" (VaR, CVaR, Stress Tests, Component VaR)
  - `src/risk_layer/` = "Wie setzen wir es durch?" (Gates, KillSwitch, Alerting, Backtesting)
- Bestehende Imports bleiben gültig
- Kohärenz mit vorhandener Codebase

### Package-Struktur

```
src/
├── risk/                          # Core Risk Calculations
│   ├── __init__.py               # Exports: VaR, CVaR, ComponentVaR, Stress
│   ├── types.py                  # Dataclasses (PositionSnapshot, PortfolioSnapshot, etc.)
│   ├── portfolio.py              # Portfolio Analytics (Exposure, Weights, Correlations)
│   ├── var.py                    # Historical VaR/CVaR
│   ├── parametric_var.py         # Parametric VaR/CVaR
│   ├── component_var.py          # Component VaR (Euler Allocation) ✅ EXISTIERT
│   ├── covariance.py             # Covariance Estimation ✅ EXISTIERT
│   ├── stress.py                 # Stress Testing Framework
│   ├── enforcement.py            # RiskLimitsV2, RiskEnforcer
│   ├── monte_carlo.py            # ⭐ NEU - Monte Carlo VaR (Agent A5)
│   └── limits.py                 # Legacy Limits
│
└── risk_layer/                    # Execution & Enforcement Layer
    ├── __init__.py               # Exports: RiskGate, KillSwitch, AuditLog
    ├── models.py                 # RiskDecision, Violation, RiskResult
    ├── risk_gate.py              # Risk Gate Orchestrator ✅ EXISTIERT
    ├── kill_switch.py            # Kill Switch ✅ EXISTIERT
    ├── audit_log.py              # Audit Logging ✅ EXISTIERT
    ├── var_gate.py               # VaR Gate ✅ EXISTIERT
    ├── liquidity_gate.py         # Liquidity Gate ✅ EXISTIERT
    ├── stress_gate.py            # Stress Gate ✅ EXISTIERT
    ├── metrics.py                # Risk Metrics ✅ EXISTIERT
    ├── alerting/                 # Alert System ✅ EXISTIERT (Phase 1)
    │   ├── __init__.py
    │   ├── alert_manager.py
    │   ├── channels/             # Slack, Email, Telegram, etc.
    │   └── ...
    └── var_backtest/             # VaR Backtesting Suite ✅ EXISTIERT
        ├── __init__.py
        ├── kupiec_pof.py         # Kupiec POF Test ✅ EXISTIERT
        ├── violation_detector.py # Violation Detection ✅ EXISTIERT
        ├── var_backtest_runner.py # Backtest Runner ✅ EXISTIERT
        ├── christoffersen_tests.py # ⭐ NEU - Independence Tests (Agent A3)
        └── traffic_light.py      # ⭐ NEU - Basel Traffic Light (Agent A3)
```

**Legend:**
- ✅ EXISTIERT = Already implemented
- ⭐ NEU = To be implemented by Agents A1-A6

---

## 2. Config Strategy Decision

### ENTSCHEIDUNG: Erweitere bestehende `config.toml` unter `[risk.*]`

**Rationale:**
- Config-Loader (`PeakConfig`) unterstützt bereits nested sections
- Bestehende `[risk]` Section vorhanden
- Kein neues Config-File nötig → weniger Komplexität
- Builder-Pattern bereits etabliert: `build_risk_manager_from_config()`

### Config-Schema (Erweiterung)

```toml
# ==========================================
# config.toml - Risk Layer v1.0
# ==========================================

[risk]
# Risk Manager Type (siehe src/core/risk.py)
type = "portfolio_var_stress"  # oder "noop", "max_drawdown", "equity_floor"

# VaR/CVaR Parameter
alpha = 0.05           # Confidence Level (95% VaR)
window = 252           # Rolling Window (trading days)

# Risk Limits (optional)
[risk.limits]
max_gross_exposure = 1.5     # 150% of Equity
max_net_exposure = 1.0       # 100% of Equity
max_position_weight = 0.35   # 35% per Position
max_var = 0.08               # 8% of Equity (95% VaR)
max_cvar = 0.12              # 12% of Equity (95% CVaR)

# ==========================================
# NEU: Monte Carlo VaR (Agent A5)
# ==========================================
[risk.monte_carlo]
enabled = false              # Set to true to enable MC VaR
n_simulations = 10000        # Number of MC paths
method = "bootstrap"         # "bootstrap", "parametric", or "copula"
confidence_level = 0.95      # Same as 1-alpha
horizon_days = 1             # Risk horizon (typically 1 or 10)
seed = 42                    # Random seed for reproducibility

# Copula-specific settings (if method = "copula")
copula_type = "gaussian"     # "gaussian" or "t"
copula_df = 5                # Degrees of freedom for t-copula

# ==========================================
# NEU: VaR Backtesting (Agent A3)
# ==========================================
[risk.var_backtest]
# Kupiec POF Test ✅ EXISTIERT
kupiec_confidence = 0.95     # Test confidence level

# Christoffersen Tests (Agent A3)
christoffersen_enabled = true
independence_test = true     # Test for violation independence
conditional_coverage = true  # Test for conditional coverage

# Basel Traffic Light (Agent A3)
traffic_light_enabled = true
green_zone_threshold = 0.95  # No action required
yellow_zone_threshold = 0.80 # Increased monitoring
red_zone_threshold = 0.80    # Model adjustment required

# ==========================================
# NEU: Stress Testing Extensions (Agent A4)
# ==========================================
[risk.stress]
enabled = true
scenario_library_path = "config/scenarios/"  # Directory with .toml scenarios
auto_run_daily = true        # Run stress tests daily
alert_on_breach = true       # Alert if stress scenario breaches limits

# Pre-defined scenarios (can also be loaded from files)
[[risk.stress.scenarios]]
name = "2020_covid_crash"
asset_shocks = { "BTC-EUR" = -0.50, "ETH-EUR" = -0.60 }  # 50% / 60% drawdown

[[risk.stress.scenarios]]
name = "interest_rate_spike"
asset_shocks = { "BTC-EUR" = -0.15, "ETH-EUR" = -0.20 }

# ==========================================
# Integration mit bestehendem System
# ==========================================
# Die Risk Layer v1.0 wird automatisch genutzt wenn:
# 1. [risk] Section in config.toml existiert
# 2. BacktestEngine mit risk_manager=build_risk_manager_from_config(cfg) initialisiert
# 3. Live Trading nutzt RiskGate (src/risk_layer/risk_gate.py)
```

**Hinweis:**
- Bestehende `config/risk_layer_v1_example.toml` bleibt als Referenz
- Hauptkonfiguration erfolgt über `config/config.toml`
- Keine neuen Loader-Features nötig (PeakConfig unterstützt alles bereits)

---

## 3. Public API Definition

### 3.1 Core Risk Calculations (`src/risk/`)

```python
# ============================================================
# Portfolio VaR/CVaR (Historical & Parametric) ✅ EXISTIERT
# ============================================================
from src.risk import (
    historical_var,        # Historical VaR
    historical_cvar,       # Historical CVaR/ES
    parametric_var,        # Parametric VaR (Gaussian)
    parametric_cvar,       # Parametric CVaR (Gaussian)
)

# Usage:
var_95 = historical_var(returns, alpha=0.05)
cvar_95 = historical_cvar(returns, alpha=0.05)

# ============================================================
# Component VaR (Euler Allocation) ✅ EXISTIERT
# ============================================================
from src.risk import ComponentVaRCalculator, ComponentVaRResult

calc = ComponentVaRCalculator(returns_df, method="ledoit_wolf")
result: ComponentVaRResult = calc.calculate(
    weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    portfolio_value=100000.0,
    alpha=0.05,
    horizon_days=1
)

print(f"Total VaR: {result.total_var}")
print(f"Component VaR: {result.component_var}")  # Per-asset contributions

# ============================================================
# Monte Carlo VaR ⭐ NEU (Agent A5)
# ============================================================
from src.risk import MonteCarloVaRCalculator, MonteCarloVaRConfig, MonteCarloVaRResult

config = MonteCarloVaRConfig(
    n_simulations=10000,
    method="bootstrap",  # or "parametric", "copula"
    confidence_level=0.95,
    horizon_days=1,
    seed=42
)

mc_calc = MonteCarloVaRCalculator(returns_df, config)
mc_result: MonteCarloVaRResult = mc_calc.calculate(
    weights={"BTC-EUR": 0.6, "ETH-EUR": 0.4},
    portfolio_value=100000.0
)

print(f"MC VaR: {mc_result.var}")
print(f"MC CVaR: {mc_result.cvar}")
print(f"Simulated Paths: {mc_result.simulated_returns.shape}")

# ============================================================
# Stress Testing ✅ EXISTIERT
# ============================================================
from src.risk import StressScenario, run_stress_suite

scenario = StressScenario(
    name="2020_covid_crash",
    asset_shocks={"BTC-EUR": -0.50, "ETH-EUR": -0.60}
)

stress_results = run_stress_suite(
    scenarios=[scenario],
    returns=returns_df,
    positions=positions_snapshot
)
```

### 3.2 Risk Layer Execution (`src/risk_layer/`)

```python
# ============================================================
# Risk Gate (Orchestration) ✅ EXISTIERT
# ============================================================
from src.risk_layer import RiskGate, RiskDecision

gate = RiskGate(config_path="config/config.toml")
decision: RiskDecision = gate.check_order(order, portfolio_snapshot)

if not decision.allowed:
    print(f"Order blocked: {decision.reason}")

# ============================================================
# VaR Backtesting Suite
# ============================================================
from src.risk_layer.var_backtest import (
    VaRBacktestRunner,      # ✅ EXISTIERT
    kupiec_pof_test,        # ✅ EXISTIERT
    christoffersen_independence_test,  # ⭐ NEU (Agent A3)
    basel_traffic_light,    # ⭐ NEU (Agent A3)
)

runner = VaRBacktestRunner(
    returns=returns_df,
    var_estimates=var_series,
    alpha=0.05
)

result = runner.run_full_backtest()
print(f"Kupiec p-value: {result.kupiec.p_value}")
print(f"Basel Zone: {result.basel_zone}")  # GREEN, YELLOW, RED

# ============================================================
# Kill Switch ✅ EXISTIERT
# ============================================================
from src.risk_layer import KillSwitchLayer, KillSwitchStatus

kill_switch = KillSwitchLayer()
if kill_switch.status == KillSwitchStatus.ACTIVE:
    print("⚠️  Trading halted by kill switch!")
```

---

## 4. File Ownership & Agent Assignments

| Module | File | Agent | Status | Description |
|--------|------|-------|--------|-------------|
| **Core Risk** | | | | |
| `src/risk/` | `monte_carlo.py` | **A5** | ⭐ NEW | Monte Carlo VaR Calculator |
| | | | | |
| **Risk Layer - Backtest** | | | | |
| `src/risk_layer/var_backtest/` | `christoffersen_tests.py` | **A3** | ⭐ NEW | Christoffersen Independence/CC Tests |
| `src/risk_layer/var_backtest/` | `traffic_light.py` | **A3** | ⭐ NEW | Basel Traffic Light System |
| | | | | |
| **Config Extensions** | | | | |
| `config/config.toml` | `[risk.monte_carlo]` | **A5** | ⭐ NEW | MC VaR Config Section |
| `config/config.toml` | `[risk.var_backtest]` | **A3** | ⭐ NEW | Extended Backtest Config |
| `config/config.toml` | `[risk.stress]` | **A4** | ⭐ NEW | Stress Test Config |
| | | | | |
| **Tests** | | | | |
| `tests/risk/` | `test_monte_carlo.py` | **A5** | ⭐ NEW | MC VaR Tests |
| `tests/risk_layer/` | `test_christoffersen.py` | **A3** | ⭐ NEW | Christoffersen Tests |
| `tests/risk_layer/` | `test_traffic_light.py` | **A3** | ⭐ NEW | Basel Traffic Light Tests |

**Agent Mapping:**
- **A0 (Architect)**: Scaffold, Decision Memo, Exports ✅ CURRENT
- **A1 (VaR Core)**: Portfolio VaR/CVaR enhancements (if needed)
- **A2 (Component VaR)**: Component VaR extensions (if needed)
- **A3 (VaR Backtest)**: Christoffersen Tests + Basel Traffic Light
- **A4 (Stress Test)**: Stress Testing enhancements
- **A5 (Monte Carlo)**: Monte Carlo VaR Calculator
- **A6 (Integration)**: End-to-end integration tests + documentation

---

## 5. Implementation Principles

### 5.1 No Breaking Changes
- ✅ Alle bestehenden Imports bleiben gültig
- ✅ Bestehende Tests laufen unverändert
- ✅ Neue Features sind opt-in (via Config)

### 5.2 Builder Pattern
- Alle neuen Calculator-Klassen folgen dem Builder-Pattern:
  ```python
  config = MonteCarloVaRConfig(...)
  calculator = MonteCarloVaRCalculator(returns_df, config)
  result = calculator.calculate(weights, portfolio_value)
  ```

### 5.3 Config-Driven
- Alle Features sind über `config.toml` steuerbar
- Default-Werte sind konservativ
- Production muss explizit konfiguriert werden (keine impliziten Prod-Defaults)

### 5.4 Type Safety
- Alle Public APIs nutzen Dataclasses/Enums
- Keine `Any`-Types in Public APIs
- Strikte Type Hints (MyPy-kompatibel)

### 5.5 Logging & Observability
- Alle Risk-Decisions werden geloggt (via `AuditLogWriter`)
- Performance-Metrics für VaR-Berechnungen
- Alert-Integration über bestehende `risk_layer&#47;alerting&#47;`

---

## 6. Scaffold Implementation

### 6.1 Neue Module (Placeholder)

```python
# src/risk/monte_carlo.py - Agent A5
"""Monte Carlo VaR Calculator - PLACEHOLDER"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class MonteCarloVaRConfig:
    """Configuration for Monte Carlo VaR."""
    n_simulations: int = 10000
    method: str = "bootstrap"  # bootstrap, parametric, copula
    confidence_level: float = 0.95
    horizon_days: int = 1
    seed: int = 42

@dataclass
class MonteCarloVaRResult:
    """Result of Monte Carlo VaR calculation."""
    var: float
    cvar: float
    simulated_returns: np.ndarray
    percentile_index: int

class MonteCarloVaRCalculator:
    """Monte Carlo VaR Calculator - PLACEHOLDER for Agent A5."""
    def __init__(self, returns: pd.DataFrame, config: MonteCarloVaRConfig):
        raise NotImplementedError("Agent A5: Implement Monte Carlo VaR")

    def calculate(self, weights: dict, portfolio_value: float) -> MonteCarloVaRResult:
        raise NotImplementedError("Agent A5: Implement calculate()")
```

```python
# src/risk_layer/var_backtest/christoffersen_tests.py - Agent A3
"""Christoffersen Independence & Conditional Coverage Tests - PLACEHOLDER"""
from dataclasses import dataclass

@dataclass
class ChristoffersenResult:
    """Result of Christoffersen test."""
    lr_statistic: float
    p_value: float
    passed: bool
    critical_value: float

def christoffersen_independence_test(violations: list[bool], alpha: float = 0.05) -> ChristoffersenResult:
    """PLACEHOLDER: Agent A3 implementiert Christoffersen Independence Test."""
    raise NotImplementedError("Agent A3: Implement Christoffersen Independence Test")

def christoffersen_conditional_coverage_test(violations: list[bool], alpha: float = 0.05) -> ChristoffersenResult:
    """PLACEHOLDER: Agent A3 implementiert Christoffersen Conditional Coverage Test."""
    raise NotImplementedError("Agent A3: Implement Christoffersen CC Test")
```

```python
# src/risk_layer/var_backtest/traffic_light.py - Agent A3
"""Basel Traffic Light System - PLACEHOLDER"""
from enum import Enum
from dataclasses import dataclass

class BaselZone(Enum):
    """Basel Traffic Light Zones."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

@dataclass
class TrafficLightResult:
    """Result of Basel Traffic Light Assessment."""
    zone: BaselZone
    n_violations: int
    expected_violations: float
    ratio: float

def basel_traffic_light(n_violations: int, n_observations: int, alpha: float = 0.05) -> TrafficLightResult:
    """PLACEHOLDER: Agent A3 implementiert Basel Traffic Light."""
    raise NotImplementedError("Agent A3: Implement Basel Traffic Light")
```

### 6.2 Export Updates

```python
# src/risk/__init__.py - ERWEITERUNG
# (Bestehende Exports bleiben unverändert)

# Monte Carlo VaR (Agent A5)
from .monte_carlo import (
    MonteCarloVaRCalculator,
    MonteCarloVaRConfig,
    MonteCarloVaRResult,
)

__all__ = [
    # ... existing exports ...
    # Monte Carlo VaR
    "MonteCarloVaRCalculator",
    "MonteCarloVaRConfig",
    "MonteCarloVaRResult",
]
```

```python
# src/risk_layer/var_backtest/__init__.py - ERWEITERUNG
# (Bestehende Exports bleiben unverändert)

from src.risk_layer.var_backtest.christoffersen_tests import (
    ChristoffersenResult,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
)
from src.risk_layer.var_backtest.traffic_light import (
    BaselZone,
    TrafficLightResult,
    basel_traffic_light,
)

__all__ = [
    # ... existing exports ...
    # Christoffersen Tests
    "ChristoffersenResult",
    "christoffersen_independence_test",
    "christoffersen_conditional_coverage_test",
    # Basel Traffic Light
    "BaselZone",
    "TrafficLightResult",
    "basel_traffic_light",
]
```

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Jeder Agent implementiert Tests für seine Module
- Naming Convention: `tests&#47;risk&#47;test_<module>.py`
- Alle Tests müssen `python3 -m pytest` konform sein

### 7.2 Integration Tests
- Agent A6 implementiert End-to-End-Tests
- Testet Zusammenspiel von `src/risk/` und `src/risk_layer/`
- Nutzt `BacktestEngine` mit vollständiger Risk Layer

### 7.3 Regression Tests
- Alle bestehenden Tests müssen weiterhin passen
- CI/CD Pipeline wird nicht gebrochen

---

## 8. Rollout Plan

### Phase 1: Scaffold (Agent A0) ✅ AKTUELL
- [x] Decision Memo erstellen
- [x] Placeholder-Module anlegen
- [x] Export-Updates
- [ ] Commit: "feat(risk): scaffold Risk Layer v1.0 architecture"

### Phase 2: Implementation (Agents A1-A5)
- [ ] Agent A3: Christoffersen Tests + Basel Traffic Light
- [ ] Agent A5: Monte Carlo VaR Calculator
- [ ] Agent A4: Stress Testing Extensions (optional)

### Phase 3: Integration (Agent A6)
- [ ] End-to-End Tests
- [ ] Documentation Updates
- [ ] Example Notebooks
- [ ] Production Readiness Review

---

## 9. Success Criteria

✅ **No Breaking Changes:**
- Alle bestehenden Tests laufen unverändert
- Keine Änderungen an Public APIs (nur Extensions)

✅ **Clear Ownership:**
- Jeder Agent hat klare File-Ownership
- Keine Konflikte zwischen Agents

✅ **Config-Driven:**
- Alle neuen Features sind opt-in
- Production muss explizit konfiguriert werden

✅ **Type-Safe:**
- Alle Public APIs haben strikte Type Hints
- MyPy-kompatibel

✅ **Testable:**
- Unit Tests für alle neuen Module
- Integration Tests für End-to-End-Flow

---

## 10. Migration Guide (für bestehenden Code)

### Vor Risk Layer v1.0:
```python
# Legacy: Direkter Import aus risk_layer
from src.risk_layer import RiskGate

gate = RiskGate()
decision = gate.check_order(order)
```

### Nach Risk Layer v1.0:
```python
# Neu: Config-driven + erweiterte Features
from src.risk_layer import RiskGate
from src.risk import MonteCarloVaRCalculator  # Neu!

# Gate bleibt gleich (Backward Compatible)
gate = RiskGate(config_path="config/config.toml")
decision = gate.check_order(order)

# Optional: Nutze neue MC VaR Features
mc_calc = MonteCarloVaRCalculator(returns_df, config)
mc_result = mc_calc.calculate(weights, portfolio_value)
```

**Wichtig:** Bestehender Code funktioniert unverändert!

---

## 11. Appendix: File Tree (Full)

```
Peak_Trade/
├── config/
│   ├── config.toml                        # ✅ Erweitert um [risk.monte_carlo], [risk.var_backtest], [risk.stress]
│   ├── risk_layer_v1_example.toml         # ✅ Bleibt als Referenz
│   └── scenarios/                         # ⭐ NEU: Stress-Test-Szenarien
│       ├── 2020_covid_crash.toml
│       └── interest_rate_spike.toml
│
├── src/
│   ├── risk/                              # Core Risk Calculations
│   │   ├── __init__.py                    # ✅ Erweitert um MC VaR Exports
│   │   ├── types.py                       # ✅ EXISTIERT
│   │   ├── portfolio.py                   # ✅ EXISTIERT
│   │   ├── var.py                         # ✅ EXISTIERT
│   │   ├── parametric_var.py              # ✅ EXISTIERT
│   │   ├── component_var.py               # ✅ EXISTIERT
│   │   ├── covariance.py                  # ✅ EXISTIERT
│   │   ├── stress.py                      # ✅ EXISTIERT
│   │   ├── enforcement.py                 # ✅ EXISTIERT
│   │   ├── monte_carlo.py                 # ⭐ NEU (Agent A5)
│   │   └── limits.py                      # ✅ EXISTIERT
│   │
│   ├── risk_layer/                        # Execution & Enforcement
│   │   ├── __init__.py                    # ✅ EXISTIERT
│   │   ├── models.py                      # ✅ EXISTIERT
│   │   ├── risk_gate.py                   # ✅ EXISTIERT
│   │   ├── kill_switch.py                 # ✅ EXISTIERT
│   │   ├── audit_log.py                   # ✅ EXISTIERT
│   │   ├── var_gate.py                    # ✅ EXISTIERT
│   │   ├── liquidity_gate.py              # ✅ EXISTIERT
│   │   ├── stress_gate.py                 # ✅ EXISTIERT
│   │   ├── metrics.py                     # ✅ EXISTIERT
│   │   ├── alerting/                      # ✅ EXISTIERT (Phase 1)
│   │   │   ├── __init__.py
│   │   │   ├── alert_manager.py
│   │   │   └── channels/
│   │   │       ├── slack_channel.py
│   │   │       ├── email_channel.py
│   │   │       └── ...
│   │   └── var_backtest/                  # VaR Backtesting Suite
│   │       ├── __init__.py                # ✅ Erweitert um neue Exports
│   │       ├── kupiec_pof.py              # ✅ EXISTIERT
│   │       ├── violation_detector.py      # ✅ EXISTIERT
│   │       ├── var_backtest_runner.py     # ✅ EXISTIERT
│   │       ├── christoffersen_tests.py    # ⭐ NEU (Agent A3)
│   │       └── traffic_light.py           # ⭐ NEU (Agent A3)
│   │
│   └── core/
│       └── risk.py                        # ✅ EXISTIERT (BaseRiskManager, build_risk_manager_from_config)
│
├── tests/
│   ├── risk/
│   │   ├── test_monte_carlo.py            # ⭐ NEU (Agent A5)
│   │   └── ...
│   └── risk_layer/
│       ├── test_christoffersen.py         # ⭐ NEU (Agent A3)
│       ├── test_traffic_light.py          # ⭐ NEU (Agent A3)
│       └── ...
│
└── docs/
    └── risk/
        ├── RISK_LAYER_ALIGNMENT.md        # ✅ DIESES DOKUMENT
        ├── MONTE_CARLO_VAR.md             # ⭐ NEU (Agent A5)
        ├── VAR_BACKTESTING.md             # ⭐ NEU (Agent A3)
        └── STRESS_TESTING.md              # ⭐ NEU (Agent A4)
```

---

## 12. Contact & Ownership

**Architect:** Agent A0  
**Review:** @peak_trade_team  
**Status:** READY FOR IMPLEMENTATION

**Next Steps:**
1. ✅ Commit Scaffold (Agent A0)
2. → Agents A3, A5 beginnen Implementation
3. → Agent A6 Integration & Documentation

---

**End of Decision Memo**
