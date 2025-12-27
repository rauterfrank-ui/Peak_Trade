# Risk Management Documentation

## Overview

Diese Dokumentation beschreibt das Risk-Management-System von Peak_Trade, einschließlich implementierter Features, Roadmaps und Operator-Guides.

---

## Documentation Index

### Implementation Guides

- **[Risk Layer v1 - Operator Guide](RISK_LAYER_V1_OPERATOR_GUIDE.md)**  
  Vollständiger Guide für Operators: Config, Usage, Troubleshooting, Best-Practices

- **[Risk Layer v1 - Technical Implementation](../risk_layer_v1.md)**  
  Technical Deep-Dive: Architecture, Module-Details, Code-Examples

- **[Risk Layer v1 - Change Justification](RISK_LAYER_V1_CHANGE_JUSTIFICATION.md)**  
  Begründung für Design-Entscheidungen und Architektur-Choices

### Roadmaps

- **[Portfolio VaR Roadmap](roadmaps/PORTFOLIO_VAR_ROADMAP.md)**  
  5-Phasen-Roadmap für Portfolio-Level VaR: Multi-Asset, Advanced Models, Paper-Trading, Adaptive Limits, Live-Trading

---

## Quick Links

### Current Implementation (Risk Layer v1)

**Status:** ✅ Production-Ready (Backtests)

**Features:**
- Portfolio-Level Risk Management (Exposures, Weights)
- VaR/CVaR (Historical + Parametric)
- Stress-Testing (5 Scenario-Types)
- Risk-Limit Enforcement (Circuit-Breaker)

**Tests:** 96/96 passed (100%)

**Config Example:**
```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05
window = 252

[risk.limits]
max_gross_exposure = 1.5
max_position_weight = 0.35
max_var = 0.08
max_cvar = 0.12
```

**Usage:**
```python
from src.core.peak_config import load_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine

cfg = load_config()
risk_manager = build_risk_manager_from_config(cfg)
engine = BacktestEngine(risk_manager=risk_manager)
result = engine.run_realistic(df, strategy_fn, params)
```

---

## Future Development

### Next Steps (2026)

1. **Q1 2026:** Multi-Asset Portfolio VaR
   - Covariance-based VaR
   - Correlation-Matrix-Checks
   - Multi-Asset-Portfolio-Returns

2. **Q1-Q2 2026:** Advanced Distribution Models
   - Student-t VaR (Fat Tails)
   - GARCH VaR (Time-varying Volatility)
   - Extreme Value Theory

3. **Q2 2026:** Paper-Trading Validation
   - Real-Time VaR Calculation
   - Backtesting Framework (Kupiec/Christoffersen)
   - Alert System

4. **Q2-Q3 2026:** Adaptive & ML-based Limits
   - Regime-dependent Limits
   - Volatility-scaled Limits
   - ML-based Limit-Prediction

5. **Q3-Q4 2026:** Live-Trading Integration
   - Pre-Trade VaR-Check
   - Real-Time Monitoring
   - Staged Rollout (Testnet → Paper → Micro → Full)

**Details:** See [Portfolio VaR Roadmap](roadmaps/PORTFOLIO_VAR_ROADMAP.md)

---

## Testing

### Run All Risk-Layer Tests

```bash
uv run pytest tests/risk/ -v
```

### Generate Stress-Report

```bash
python scripts/run_risk_stress_report.py --symbol BTC/EUR --output reports/stress.csv
```

---

## Support

**Questions?**
1. Check Operator-Guide: `RISK_LAYER_V1_OPERATOR_GUIDE.md`
2. Check Tests: `tests/risk/` (Usage-Examples)
3. Run Tests: `pytest tests/risk/ -v`

**Issues?**
- Check Troubleshooting-Section in Operator-Guide
- Review Test-Failures for similar cases
- Check Linter: `read_lints` tool

---

## Changelog

### 2025-12-25: Portfolio VaR Roadmap
- Added 5-Phase Roadmap for Portfolio-VaR Evolution
- Safety-First approach with staged rollout
- Timeline: Q1 2026 - Q4 2026

### 2025-12-23: Risk Layer v1 Production-Ready
- 96 Tests (100% Pass)
- Comprehensive Documentation
- Stress-Testing Script
- Status: ✅ Production-Ready for Backtests

### 2025-12-23: Risk Layer v1 Implementation
- Portfolio-Level Risk Management
- VaR/CVaR (Historical + Parametric)
- Stress-Testing Engine
- Risk-Limit Enforcement
- 1.268 Lines Production-Code
- Backward-compatible

---

**Last Updated:** 2025-12-25

