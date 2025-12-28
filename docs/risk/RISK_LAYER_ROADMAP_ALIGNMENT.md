# Peak_Trade Risk Layer Roadmap – Alignment & Inventar

**Version:** 1.0  
**Datum:** 2025-12-28  
**Status:** ✅ ALIGNMENT ABGESCHLOSSEN  
**Autor:** AI Lead Orchestrator (Agent A)

---

## 🎯 Executive Summary

Diese Analyse dokumentiert den **IST-Zustand** der Peak_Trade Risk Layer Implementierung und definiert klare Architektur-Entscheidungen für die weitere Entwicklung.

**Haupterkenntnisse:**
- ✅ **Emergency Kill Switch** ist zu **97-100% implementiert** (Phase 5)
- ✅ **VaR Backtesting** (Kupiec POF, Christoffersen) ist **vollständig implementiert**
- ✅ **VaR Core** existiert in mehreren Varianten (`src/risk/` und `src/risk_layer/`)
- ⚠️ **Zwei parallele Risk-Systeme** erfordern Konsolidierung
- 🔄 **Stress Testing** teilweise implementiert, erfordert Erweiterung
- 🆕 **Attribution Analytics** fehlt noch

**Empfehlung:** Keine große Roadmap-Neuimplementierung nötig. Stattdessen:
1. Konsolidierung der beiden Risk-Systeme
2. Lücken füllen (Attribution, erweiterte Stress-Tests)
3. Integration testen

---

## 📦 Repo-Inventar

### 1. Bestehende Risk-Module

#### `src/risk/` – Risk Layer v1.0 (Agent A6 Implementation)

```
src/risk/
├── __init__.py                    # Public API
├── types.py                       # PositionSnapshot, PortfolioSnapshot, RiskBreach
├── portfolio.py                   # Exposure/Weight/Correlation
├── var.py                         # Historical & Parametric VaR/CVaR
├── parametric_var.py              # Parametric VaR (Gaussian, Cornish-Fisher, EWMA)
├── portfolio_var.py               # Portfolio-Level VaR
├── component_var.py               # Marginal, Incremental, Diversification VaR
├── monte_carlo.py                 # Monte Carlo VaR (Bootstrap, Normal, Student-t)
├── covariance.py                  # Covariance Matrix Estimation
├── stress_tester.py               # Stress Testing (Historical Scenarios)
├── stress.py                      # Stress Testing Engine
├── enforcement.py                 # RiskEnforcer + RiskLimitsV2
├── limits.py                      # Legacy Limits
├── position_sizer.py              # Position Sizing
└── risk_layer_manager.py          # Central Orchestrator
```

**Status:** ✅ Funktionsfähig, gut getestet, in Produktion  
**Verwendung:** `RiskLayerManager` als zentrale Schnittstelle  
**Config:** `[risk_layer_v1]` in `config/config.toml`

#### `src/risk_layer/` – Defense-in-Depth Risk Layer (Neuere Architektur)

```
src/risk_layer/
├── __init__.py                    # Public API
├── models.py                      # RiskDecision, RiskResult, Violation
├── audit_log.py                   # Audit Logging
├── risk_gate.py                   # Order Validation Gateway
├── var_gate.py                    # VaR-based Gate
├── liquidity_gate.py              # Liquidity Gate
├── stress_gate.py                 # Stress Test Gate
├── metrics.py                     # Risk Metrics
├── micro_metrics.py               # Micro-Level Metrics
├── kill_switch/                   # ✅ PHASE 5 (97-100% FERTIG)
│   ├── core.py                    # KillSwitch State Machine
│   ├── state.py                   # State Enum & Events
│   ├── config.py                  # Config Schema
│   ├── triggers/                  # Trigger-Mechanismen
│   │   ├── base.py                # Abstract Trigger
│   │   ├── threshold.py           # Drawdown, Daily Loss, Vol
│   │   ├── manual.py              # Manual CLI/API Trigger
│   │   ├── watchdog.py            # System Health Watchdog
│   │   └── external.py            # Exchange/Network Triggers
│   ├── recovery.py                # Recovery Manager
│   ├── health_check.py            # Pre-Recovery Health Checks
│   ├── persistence.py             # State Persistence (Atomic Writes)
│   ├── audit.py                   # Audit Trail (JSONL)
│   ├── execution_gate.py          # Execution Gate für Live Trading
│   ├── cli.py                     # CLI Interface
│   └── adapter.py                 # Adapter für Integration
├── var_backtest/                  # ✅ VAR VALIDATION (100% FERTIG)
│   ├── kupiec_pof.py              # Kupiec POF Test (pure Python, no scipy!)
│   ├── christoffersen_tests.py   # Independence Tests
│   ├── traffic_light.py           # Basel Traffic Light Approach
│   ├── var_backtest_runner.py    # Orchestrator
│   └── violation_detector.py     # Violation Detection
└── alerting/                      # ✅ ALERTING SYSTEM (100% FERTIG)
    ├── alert_manager.py           # Central Alert Manager
    ├── alert_types.py             # Alert Severity, Types
    ├── alert_event.py             # Alert Event Model
    ├── alert_config.py            # Config Loading
    ├── alert_dispatcher.py        # Multi-Channel Dispatch
    └── channels/                  # Notification Channels
        ├── base_channel.py        # Abstract Channel
        ├── console_channel.py     # Console Output
        ├── file_channel.py        # File Logging
        ├── email_channel.py       # Email (SMTP)
        ├── slack_channel.py       # Slack Webhook
        ├── telegram_channel.py    # Telegram Bot
        └── webhook_channel.py     # Generic Webhook
```

**Status:** ✅ Kill Switch & VaR Backtest vollständig, Alerting vollständig  
**Verwendung:** `RiskGate` als zentrale Validierungs-Schnittstelle  
**Config:** `config/risk/kill_switch.toml`, Alerting-Config integriert

#### `src/core/risk.py` – Integration Layer

```python
# Manager-Schicht für Backtest-Integration
class BaseRiskManager(ABC)
class PortfolioVaRStressRiskManager
def build_risk_manager_from_config(cfg, section="risk") -> BaseRiskManager
```

**Status:** ✅ Produktiv, gut integriert mit BacktestEngine  
**Config:** `[risk]` in `config/config.toml`

---

## 🏗️ Architektur-Entscheidungen

### Entscheidung 1: Kanonischer Package-Pfad

**Entscheidung:** `src/risk_layer` ist der **primäre** Package-Pfad für neue Entwicklungen.

**Begründung:**
- Neuere Defense-in-Depth Architektur mit klaren Layern
- Kill Switch & VaR Backtest bereits dort implementiert
- Bessere Trennung von Concerns (Gates, Alerting, Audit)

**Migration-Strategie:**
```python
# src/risk/__init__.py - Compatibility Exports
from src.risk_layer.var_gate import VaRGate  # Re-export
from src.risk_layer.kill_switch import KillSwitch  # Re-export

# Legacy Code kann weiterhin arbeiten:
from src.risk import KillSwitch  # ✅ Funktioniert
```

**Neue Features:**  
→ In `src/risk_layer/` implementieren  
→ Backward-Kompatibilität via Exports in `src/risk/__init__.py`

---

### Entscheidung 2: Config-Location & Struktur

**Primäre Config:** `config/config.toml`

**Struktur:**
```toml
# Haupt-Config (config/config.toml)
[risk_layer_v1]
enabled = true

[risk_layer_v1.var]
methods = ["historical", "parametric", "ewma"]
confidence_level = 0.95
window = 252

[risk_layer_v1.component_var]
enabled = true

[risk_layer_v1.monte_carlo]
enabled = true
n_simulations = 10000

[risk_layer_v1.stress_test]
enabled = true
scenarios_dir = "config/scenarios"

[risk_layer_v1.backtest]
enabled = false  # Requires historical data

# Für Backtest-Integration
[risk]
type = "portfolio_var_stress"  # oder "noop", "max_drawdown"
alpha = 0.05
window = 252

[risk.limits]
max_gross_exposure = 1.5
max_position_weight = 0.35
max_var = 0.08
max_cvar = 0.12
```

**Zusätzliche Configs:**
- `config/risk/kill_switch.toml` – Kill Switch Trigger & Recovery Settings
- `config/scenarios/` – Stress-Test-Szenarien (TOML)
- `config/risk/*.toml` – Weitere modulspezifische Configs

**Config-Zugriff:**
```python
from src.core.peak_config import load_config

cfg = load_config()  # Lädt config/config.toml
value = cfg.get("risk_layer_v1.var.window", 252)  # Dot-notation
```

---

### Entscheidung 3: Kupiec p-value Ansatz

**Entscheidung:** Pure-Python Chi-Square Implementierung (bereits implementiert!)

**Implementierung:** `src/risk_layer/var_backtest/kupiec_pof.py`

**Details:**
- ✅ Keine scipy-Abhängigkeit
- ✅ Verwendet `math.erf` + Binary Search für Chi-Square CDF/SF/PPF
- ✅ Numerisch stabil für Edge Cases (N=0, N=T)
- ✅ Vollständig getestet

**Code:**
```python
from src.risk_layer.var_backtest.kupiec_pof import kupiec_pof_test

result = kupiec_pof_test(
    violations=[False] * 245 + [True] * 5,  # 5 Violations in 250 Tagen
    confidence_level=0.99,
    significance_level=0.05,
)

print(f"Modell valide: {result.is_valid}")  # True/False
print(f"p-Wert: {result.p_value:.4f}")
print(f"LR-Statistik: {result.lr_statistic:.4f}")
```

**Keine Änderungen nötig!** Die Implementierung ist produktionsreif.

---

### Entscheidung 4: Test-Strategie

**Test-Framework:** pytest  
**Config:** `pytest.ini` im Repo-Root

**Struktur:**
```
tests/
├── risk/                          # Tests für src/risk/
│   ├── test_var.py
│   ├── test_component_var.py
│   ├── test_monte_carlo.py
│   ├── test_stress_tester.py
│   └── test_risk_layer_manager.py
├── risk_layer/                    # Tests für src/risk_layer/
│   ├── kill_switch/
│   │   ├── test_state_machine.py
│   │   ├── test_triggers.py
│   │   ├── test_recovery.py
│   │   ├── test_persistence.py
│   │   ├── test_integration.py
│   │   └── test_chaos.py
│   ├── var_backtest/
│   │   ├── test_kupiec_pof.py
│   │   ├── test_christoffersen.py
│   │   └── test_traffic_light.py
│   └── alerting/
│       ├── test_alert_manager.py
│       └── test_channels.py
└── integration/
    └── test_risk_layer_integration.py
```

**Coverage-Ziel:** > 90% für alle Risk-Module

**CI-Gates:**
```bash
# Alle Tests müssen passen
pytest tests/ --maxfail=1

# Coverage-Check
pytest tests/ --cov=src/risk --cov=src/risk_layer --cov-report=html
```

---

## 📋 Lückenanalyse

### ✅ Vollständig Implementiert

| Feature | Modul | Status |
|---------|-------|--------|
| Historical VaR/CVaR | `src/risk/var.py` | ✅ 100% |
| Parametric VaR | `src/risk/parametric_var.py` | ✅ 100% |
| Component VaR | `src/risk/component_var.py` | ✅ 100% |
| Monte Carlo VaR | `src/risk/monte_carlo.py` | ✅ 100% |
| Kupiec POF Test | `src/risk_layer/var_backtest/kupiec_pof.py` | ✅ 100% |
| Christoffersen Tests | `src/risk_layer/var_backtest/christoffersen_tests.py` | ✅ 100% |
| Traffic Light | `src/risk_layer/var_backtest/traffic_light.py` | ✅ 100% |
| Kill Switch | `src/risk_layer/kill_switch/` | ✅ 97% |
| Alerting System | `src/risk_layer/alerting/` | ✅ 100% |

### 🔄 Teilweise Implementiert

| Feature | Modul | Status | Fehlend |
|---------|-------|--------|---------|
| Stress Testing | `src/risk/stress_tester.py` | 🔄 70% | Reverse Stress, Forward Scenarios |
| Risk Gate | `src/risk_layer/risk_gate.py` | 🔄 80% | Vollständige Multi-Layer Integration |

### 🆕 Noch Nicht Implementiert

| Feature | Empfohlenes Modul | Priorität |
|---------|-------------------|-----------|
| **Attribution Analytics** | `src/risk_layer/attribution/` | 🔴 HOCH |
| **VaR Decomposition** | `src/risk_layer/attribution/var_decomposition.py` | 🔴 HOCH |
| **P&L Attribution** | `src/risk_layer/attribution/pnl_attribution.py` | 🟡 MITTEL |
| **Risk Factor Analysis** | `src/risk_layer/attribution/factor_analysis.py` | 🟡 MITTEL |
| **Advanced Stress Testing** | `src/risk_layer/stress/` | 🟡 MITTEL |
| **Reverse Stress Testing** | `src/risk_layer/stress/reverse_stress.py` | 🟡 MITTEL |
| **Forward Stress Scenarios** | `src/risk_layer/stress/forward_scenarios.py` | 🟢 NIEDRIG |

---

## 🎯 Roadmap-Anpassung

### Original User-Request
> GOAL: Implement the roadmap in small, reviewable PRs
> Phases: VaR → Validation → Attribution → Stress → Emergency

### Angepasste Roadmap (basierend auf IST-Zustand)

| Phase | Name | Status | Arbeit Verbleibend |
|-------|------|--------|--------------------|
| **0** | ~~Foundation~~ | ✅ FERTIG | - |
| **1** | ~~VaR Core~~ | ✅ FERTIG | - |
| **2** | ~~VaR Validation~~ | ✅ FERTIG | - |
| **3** | **Attribution** | 🆕 NEU | 5-7 Tage |
| **4** | **Stress Testing (Erweitert)** | 🔄 AUSBAU | 3-4 Tage |
| **5** | ~~Emergency Kill Switch~~ | ✅ FERTIG (97%) | Kill Switch CLI-Polish (1 Tag) |
| **6** | **Integration & Testing** | 🔄 TEILWEISE | 3-4 Tage |

**Geschätzte Restarbeit:** 12-16 Tage (2.5-3 Wochen)

---

## 📝 PR0: Alignment & Stub Setup (Optional)

**Ziel:** Minimaler PR mit Types/Stubs für neue Module, falls gewünscht.

### Option A: Kein PR0 nötig
→ Direkt mit Phase 3 (Attribution) starten  
→ Bestehende Strukturen nutzen

### Option B: PR0 für saubere Vorbereitung

**Deliverables:**
```
src/risk_layer/attribution/
├── __init__.py                    # Public API Exports
├── types.py                       # AttributionResult, FactorContribution
└── README.md                      # Modul-Dokumentation

docs/risk/
└── RISK_LAYER_ROADMAP_ALIGNMENT.md  # Dieses Dokument
```

**Test-Stubs:**
```
tests/risk_layer/attribution/
├── __init__.py
└── conftest.py                    # Shared Fixtures
```

**Aufwand:** 2-3 Stunden  
**Wert:** Klare Struktur, reviewbare Baseline

---

## 🔧 Technische Empfehlungen

### 1. Package-Dependencies

**Aktuell (aus pyproject.toml):**
```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    # ... andere
]

[project.optional-dependencies]
risk = [
    "scipy>=1.10.0",  # Für erweiterte Stats (optional!)
]
```

**Empfehlung:**
- VaR Backtest: **Keine scipy-Abhängigkeit** (pure Python ist OK!)
- Attribution: scipy optional für Factor Analysis
- Stress Testing: Keine zusätzlichen Deps nötig

### 2. Logging-Konvention

```python
import logging

logger = logging.getLogger(__name__)  # ✅ Standard

# In Risk-kritischen Modulen:
logger.critical("🚨 Kill Switch triggered")  # Emergency
logger.error("Risk limit breached")           # Violations
logger.warning("VaR threshold approaching")  # Early Warning
logger.info("Risk check passed")             # Normal Flow
logger.debug(f"VaR={var:.4f}")               # Details
```

### 3. Config-Loading Best Practice

```python
from src.core.peak_config import load_config

def load_module_config(cfg, section: str, defaults: dict) -> dict:
    """
    Lädt Modul-Config mit Fallback zu Defaults.

    Args:
        cfg: PeakConfig Instance
        section: Config-Section (z.B. "risk_layer_v1.var")
        defaults: Default-Werte

    Returns:
        Merged Config Dict
    """
    config = {**defaults}  # Start mit Defaults

    # Override mit Config-Werten
    for key in defaults.keys():
        value = cfg.get(f"{section}.{key}")
        if value is not None:
            config[key] = value

    return config
```

### 4. Test-Fixtures

```python
# tests/risk_layer/conftest.py
import pytest
from src.core.peak_config import PeakConfig

@pytest.fixture
def mock_config():
    """Mock Config für Risk Layer Tests."""
    return PeakConfig(raw={
        "risk_layer_v1": {
            "var": {
                "methods": ["historical"],
                "confidence_level": 0.95,
                "window": 252,
            },
            "backtest": {
                "enabled": True,
            },
        },
    })

@pytest.fixture
def sample_returns():
    """Sample Returns für VaR-Tests."""
    import pandas as pd
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=500, freq="D")
    returns = pd.DataFrame({
        "BTC-EUR": np.random.normal(0.001, 0.02, 500),
        "ETH-EUR": np.random.normal(0.001, 0.025, 500),
    }, index=dates)

    return returns
```

---

## 🚀 Next Steps

### Empfohlene Reihenfolge

#### 1. **Sofort: Kill Switch CLI Polish** (1 Tag, Agent F)
- CLI Error Messages verbessern
- Hilfe-Texte für Operator Runbook
- Health Check Output formatieren

**PR:** `feat(risk): polish kill-switch CLI and operator UX`

#### 2. **Phase 3: Attribution Analytics** (5-7 Tage, Agent D)
- VaR Decomposition (Marginal/Component)
- P&L Attribution
- Factor Analysis (optional scipy)

**PR-Serie:**
- PR1: `feat(risk): add var decomposition and attribution core`
- PR2: `feat(risk): add pnl attribution analytics`
- PR3: `feat(risk): add factor analysis (optional scipy)`

#### 3. **Phase 4: Erweiterte Stress Tests** (3-4 Tage, Agent E)
- Reverse Stress Testing
- Forward Stress Scenarios
- Multi-Factor Stress

**PR:** `feat(risk): extend stress testing with reverse and forward scenarios`

#### 4. **Phase 6: Integration Testing** (3-4 Tage, Agent A + All)
- End-to-End Tests
- Performance Benchmarks
- Documentation Review

**PR:** `test(risk): add comprehensive integration tests for risk layer`

---

## 📚 Dokumentations-Roadmap

### Bestehende Docs (bereits vorhanden)
- ✅ `docs/risk/KILL_SWITCH_ARCHITECTURE.md`
- ✅ `docs/ops/KILL_SWITCH_RUNBOOK.md`
- ✅ `docs/ops/KILL_SWITCH_TROUBLESHOOTING.md`
- ✅ `docs/risk/roadmaps/ROADMAP_EMERGENCY_KILL_SWITCH.md`
- ✅ `docs/risk/RISK_LAYER_OVERVIEW.md`

### Fehlende Docs (zu erstellen)
- 🆕 `docs/risk/VAR_BACKTEST_GUIDE.md` – Kupiec, Christoffersen, Traffic Light
- 🆕 `docs/risk/ATTRIBUTION_GUIDE.md` – Attribution Analytics
- 🆕 `docs/risk/STRESS_TESTING_GUIDE.md` – Erweiterte Stress Tests
- 🆕 `docs/risk/RISK_LAYER_API.md` – API Reference für alle Module

---

## ⚠️ Wichtige Hinweise

### 1. Breaking Changes vermeiden
- `src/risk/` bleibt functional
- Neue Features in `src/risk_layer/`
- Backward-Kompatibilität via Exports

### 2. Config-Migration
- Bestehende Configs funktionieren weiter
- Neue Configs folgen `risk_layer_v1.*` Konvention
- Gradual Migration, kein Big Bang

### 3. Testing-Pflicht
- Jeder PR: 100% Tests passing
- Neue Features: >90% Coverage
- Integration Tests für Cross-Module Features

### 4. Review-Prozess
- PRs < 500 Lines bevorzugt
- Self-Review mit Checklist
- Docs + Tests im selben PR

---

## 📊 Metriken & Success Criteria

| Metrik | Ziel | Aktuell |
|--------|------|---------|
| Kill Switch Uptime | 99.9% | N/A (noch nicht live) |
| VaR Backtest Coverage | 100% | ✅ 100% |
| Risk Layer Test Coverage | >90% | ~85% (geschätzt) |
| Attribution Latency | <100ms | N/A (noch nicht impl.) |
| False Positive Rate (Kill Switch) | <5% | TBD (nach Live-Daten) |

---

## 🎓 Lessons Learned

### Was gut funktioniert hat
- ✅ Pure-Python Kupiec POF (keine scipy-Abhängigkeit!)
- ✅ Defense-in-Depth Architektur (`src/risk_layer/`)
- ✅ TOML-basierte Konfiguration mit `PeakConfig`
- ✅ Modulare Trigger-Architektur (Kill Switch)

### Verbesserungspotenzial
- ⚠️ Zwei parallele Risk-Systeme erzeugen Verwirrung
- ⚠️ Config-Struktur teilweise inkonsistent (`[risk]` vs. `[risk_layer_v1]`)
- ⚠️ Fehlende API-Dokumentation für Risk Layer

---

## 📞 Kontakt & Verantwortlichkeiten

| Agent | Rolle | Verantwortung |
|-------|-------|---------------|
| **Agent A** | Lead/Orchestrator | Alignment, Architecture, Integration |
| **Agent B** | VaR Core | (Bereits fertig) |
| **Agent C** | VaR Validation | (Bereits fertig) |
| **Agent D** | Attribution | Phase 3: Attribution Analytics |
| **Agent E** | Stress Testing | Phase 4: Erweiterte Stress Tests |
| **Agent F** | Emergency Controls | Phase 5: Kill Switch CLI Polish |

---

**Erstellt von:** Agent A (Lead Orchestrator)  
**Review:** TBD  
**Status:** ✅ BEREIT FÜR IMPLEMENTATION

---

**Changelog:**
- 2025-12-28: Initial Alignment Document (v1.0)
