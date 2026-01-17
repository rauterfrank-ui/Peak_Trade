# Risk Layer v1.0 - Files Ready for Implementation

**Agent A0 Status:** ✅ COMPLETE  
**Datum:** 2025-12-28

---

## Files Created by Agent A0 (Scaffold)

### 📦 Core Risk Modules

| File | Lines | Status | Owner |
|------|-------|--------|-------|
| `src/risk/monte_carlo.py` | ~280 | ⭐ PLACEHOLDER | Agent A5 |

**Enthält:**
- `MonteCarloVaRConfig` dataclass
- `MonteCarloVaRResult` dataclass
- `MonteCarloVaRCalculator` class (stub)
- `MonteCarloMethod` enum (BOOTSTRAP, PARAMETRIC, COPULA)
- `CopulaType` enum (GAUSSIAN, T)
- `build_monte_carlo_var_from_config()` factory
- Detaillierte Implementation-Hints in docstrings

---

### 🛡️ Risk Layer Modules

| File | Lines | Status | Owner |
|------|-------|--------|-------|
| `src/risk_layer/var_backtest/christoffersen_tests.py` | ~240 | ⭐ PLACEHOLDER | Agent A3 |
| `src/risk_layer/var_backtest/traffic_light.py` | ~240 | ⭐ PLACEHOLDER | Agent A3 |

**christoffersen_tests.py enthält:**
- `ChristoffersenResult` dataclass
- `christoffersen_independence_test()` function (stub)
- `christoffersen_conditional_coverage_test()` function (stub)
- `run_full_var_backtest()` convenience wrapper (stub)
- Helper functions: `_compute_transition_matrix()`, `_likelihood_ratio_statistic()`
- Referenzen: Christoffersen (1998)

**traffic_light.py enthält:**
- `BaselZone` enum (GREEN, YELLOW, RED)
- `TrafficLightResult` dataclass
- `basel_traffic_light()` function (stub)
- `compute_zone_thresholds()` helper (stub)
- `traffic_light_recommendation()` helper
- `TrafficLightMonitor` class (stub, optional für live monitoring)
- Referenzen: Basel Committee (1996)

---

### 📤 Updated Exports

| File | Status | Changes |
|------|--------|---------|
| `src/risk/__init__.py` | ✅ UPDATED | Added MC VaR exports (6 new items) |
| `src/risk_layer/var_backtest/__init__.py` | ✅ UPDATED | Added Christoffersen + Traffic Light exports (10 new items) |

**Neue Exports (src/risk/):**
```python
from src.risk import (
    MonteCarloVaRCalculator,
    MonteCarloVaRConfig,
    MonteCarloVaRResult,
    MonteCarloMethod,
    CopulaType,
    build_monte_carlo_var_from_config,
)
```

**Neue Exports (src/risk_layer/var_backtest/):**
```python
from src.risk_layer.var_backtest import (
    # Christoffersen Tests
    ChristoffersenResult,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
    run_full_var_backtest,
    # Basel Traffic Light
    BaselZone,
    TrafficLightResult,
    TrafficLightMonitor,
    basel_traffic_light,
    compute_zone_thresholds,
    traffic_light_recommendation,
)
```

---

### ⚙️ Configuration

| File | Status | Purpose |
|------|--------|---------|
| `config/risk_layer_v1_scaffold.toml` | ✅ CREATED | Template für neue Config-Sections |

**Neue Config-Sections:**
- `[risk.monte_carlo]` - MC VaR Settings (enabled, n_simulations, method, etc.)
- `[risk.var_backtest]` - Extended Backtest Settings (Christoffersen, Traffic Light)
- `[risk.stress]` - Stress Testing Settings (optional)

**Integration:**
- Agents müssen diese Sections in `config/config.toml` mergen
- Alle Features sind opt-in (via `enabled` flags)

---

### 📚 Documentation

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `docs/risk/RISK_LAYER_ALIGNMENT.md` | ~800 | ✅ CREATED | Architecture Decision Memo |
| `docs&#47;risk&#47;AGENT_HANDOFF.md` | ~500 | ✅ CREATED (historical) | Handoff Instructions für A1-A6 |
| `docs/risk/FILES_READY_FOR_AGENTS.md` | ~200 | ✅ CREATED | Diese Datei (File-Übersicht) |

---

## Import-Statements für Agents

### Agent A3 (VaR Backtesting)

```python
# In christoffersen_tests.py
import numpy as np
from scipy.stats import chi2
from dataclasses import dataclass
from typing import List, Tuple

# Bestehende Integration:
from src.risk_layer.var_backtest.kupiec_pof import quick_kupiec_check

# In traffic_light.py
import numpy as np
from scipy.stats import binom
from dataclasses import dataclass
from enum import Enum
from typing import Optional
```

### Agent A5 (Monte Carlo VaR)

```python
# In monte_carlo.py
import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal, multivariate_t  # Für Parametric/Copula
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
```

---

## Test Files (noch zu erstellen)

### Agent A3

```
tests/risk_layer/
├── test_christoffersen.py          # 🆕 Agent A3
└── test_traffic_light.py           # 🆕 Agent A3
```

**Mindest-Coverage:**
- Test Independence Test (independent violations → pass)
- Test Independence Test (clustered violations → fail)
- Test Conditional Coverage (correct model → pass)
- Test Conditional Coverage (incorrect model → fail)
- Test Traffic Light GREEN zone (0-4 violations @ 99% VaR, 250 days)
- Test Traffic Light YELLOW zone (5-9 violations)
- Test Traffic Light RED zone (≥10 violations)

### Agent A5

```
tests/risk/
└── test_monte_carlo.py             # 🆕 Agent A5
```

**Mindest-Coverage:**
- Test Bootstrap method (synthetic data)
- Test Parametric method (compare to analytical VaR)
- Test Copula method (Gaussian copula)
- Test horizon scaling (multi-day VaR)
- Test config builder (`build_monte_carlo_var_from_config()`)
- Test CVaR > VaR property
- Test weight validation (sum to 1.0)

### Agent A6

```
tests/integration/
└── test_risk_layer_e2e.py          # 🆕 Agent A6
```

**Coverage:**
- Full backtest with MC VaR + Christoffersen + Traffic Light
- RiskGate integration
- Config-driven workflow

---

## Dependencies Check

### ✅ Already Installed (requirements.txt)
- `numpy`
- `pandas`
- `scipy`
- `dataclasses` (Python 3.7+)
- `enum` (Python 3.4+)

### ⚠️ Optional (Agent A5 may add if needed)
- `copulas` (für advanced Copula-fitting)
  - Falls nötig: `pip install copulas`
  - Nicht zwingend erforderlich (scipy.stats hat basic Copulas)

---

## Linter & Type Checking Status

### ✅ All Scaffolds Pass Linter
```bash
# Checked by Agent A0:
# - No syntax errors
# - No import errors
# - MyPy-compatible type hints
```

**Commands für Agents:**
```bash
# Type Checking
mypy src/risk/monte_carlo.py
mypy src/risk_layer/var_backtest/christoffersen_tests.py
mypy src/risk_layer/var_backtest/traffic_light.py

# Linting
ruff check src/risk/monte_carlo.py
ruff check src/risk_layer/var_backtest/

# Run existing tests (ensure no regressions)
pytest tests/risk/ -v
pytest tests/risk_layer/ -v
```

---

## Git Workflow

### Agent A0 Commit (Scaffold)
```bash
git add docs/risk/ src/risk/monte_carlo.py src/risk_layer/var_backtest/ config/risk_layer_v1_scaffold.toml
git commit -m "feat(risk): scaffold Risk Layer v1.0 architecture (Agent A0)

- Add Decision Memo (RISK_LAYER_ALIGNMENT.md)
- Add Agent Handoff Instructions (AGENT_HANDOFF.md)
- Create Monte Carlo VaR placeholder (monte_carlo.py)
- Create Christoffersen tests placeholder (christoffersen_tests.py)
- Create Basel Traffic Light placeholder (traffic_light.py)
- Update exports in __init__.py files
- Add config template (risk_layer_v1_scaffold.toml)
- No breaking changes (all placeholders raise NotImplementedError)

Agents ready: A3 (VaR Backtest), A5 (Monte Carlo), A6 (Integration)"
```

### Agent A3 Commit (Example)
```bash
git add src/risk_layer/var_backtest/christoffersen_tests.py \
        src/risk_layer/var_backtest/traffic_light.py \
        tests/risk_layer/test_christoffersen.py \
        tests/risk_layer/test_traffic_light.py
git commit -m "feat(risk): implement Christoffersen tests + Basel Traffic Light (Agent A3)"
```

### Agent A5 Commit (Example)
```bash
git add src/risk/monte_carlo.py tests/risk/test_monte_carlo.py
git commit -m "feat(risk): implement Monte Carlo VaR Calculator (Agent A5)"
```

---

## Next Steps

### 1. Agent A3 (VaR Backtesting)
- [ ] Implementiere `christoffersen_independence_test()`
- [ ] Implementiere `christoffersen_conditional_coverage_test()`
- [ ] Implementiere `basel_traffic_light()`
- [ ] Schreibe Unit Tests
- [ ] Update Config Integration
- [ ] Commit

### 2. Agent A5 (Monte Carlo VaR)
- [ ] Implementiere `MonteCarloVaRCalculator._simulate_bootstrap()`
- [ ] Implementiere `MonteCarloVaRCalculator._simulate_parametric()`
- [ ] Implementiere `MonteCarloVaRCalculator._simulate_copula()`
- [ ] Implementiere `MonteCarloVaRCalculator.calculate()`
- [ ] Schreibe Unit Tests
- [ ] Update Config Integration
- [ ] Commit

### 3. Agent A6 (Integration)
- [ ] End-to-End Tests
- [ ] Documentation (User Guide)
- [ ] Example Notebooks
- [ ] Production Readiness Review

---

## Summary (Zahlen)

| Kategorie | Count | Status |
|-----------|-------|--------|
| **Neue Module** | 3 | ⭐ PLACEHOLDER |
| **Updated Exports** | 2 | ✅ COMPLETE |
| **Config Files** | 1 | ✅ TEMPLATE |
| **Documentation** | 3 | ✅ COMPLETE |
| **Tests (zu erstellen)** | 4 | 🆕 PENDING |
| **Linter Errors** | 0 | ✅ CLEAN |
| **Breaking Changes** | 0 | ✅ NONE |

---

## Contact & Support

**Agent A0 (Architect):** Verfügbar für Architektur-Fragen  
**Documentation:** `docs/risk/RISK_LAYER_ALIGNMENT.md` (vollständiges Decision Memo)  
**Handoff:** `docs&#47;risk&#47;AGENT_HANDOFF.md` (detaillierte Instructions, historical)

---

**Status:** ✅ READY FOR IMPLEMENTATION  
**Next Agent:** A3 oder A5 (parallel möglich)

🚀 Let's build Risk Layer v1.0! 🎯
