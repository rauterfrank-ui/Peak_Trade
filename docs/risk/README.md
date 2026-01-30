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

- **Integration Guide** (planned) 🆕  
  How to use multiple Risk Layer components together - Workflows, Examples, Best Practices

- **[VaR Validation Operator Guide](VAR_VALIDATION_OPERATOR_GUIDE.md)** 🆕  
  Quick-start guide for operators: When to run, how to interpret results, troubleshooting

- **[VaR Backtest Suite Guide](VAR_BACKTEST_SUITE_GUIDE.md)** 🆕 *(Phase 9A/9B/10)*  
  Complete guide for VaR backtest suite: Duration diagnostics, rolling evaluation, snapshot runner  
  Operator-friendly workflows + API reference + troubleshooting

- **[Kupiec POF Theory](KUPIEC_POF_THEORY.md)** 🆕 Phase 8A  
  Theory and implementation details for Kupiec POF (Proportion of Failures) test

- **[Christoffersen Tests Guide](CHRISTOFFERSEN_TESTS_GUIDE.md)** 🆕 Phase 8B  
  Independence (LR-IND) & Conditional Coverage (LR-CC) VaR backtests - Theory, API, CLI, Best Practices

- **[VaR Backtest Suite Quick Start](VAR_BACKTEST_SUITE_QUICKSTART.md)** 🆕 Phase 8C  
  Suite Runner & Report Formatter: Run all VaR backtests (Kupiec, Basel, Christoffersen) in one command  
  Deterministic JSON + Markdown reports, regression-safe, operator-friendly

### Roadmaps

- **[Portfolio VaR Roadmap](roadmaps/PORTFOLIO_VAR_ROADMAP.md)**  
  5-Phasen-Roadmap für Portfolio-Level VaR: Multi-Asset, Advanced Models, Paper-Trading, Adaptive Limits, Live-Trading

---

## Quick Links

### Current Implementation (Risk Layer v1 + v1.1)

**Status:** ✅ Production-Ready (Backtests)

**Features:**
- Portfolio-Level Risk Management (Exposures, Weights)
- VaR/CVaR (Historical, Parametric, EWMA, Cornish-Fisher)
- **🆕 VaR Validation (Kupiec POF Test, Basel Traffic Light)** - Phase 2
- Component VaR (Risk Attribution & Decomposition)
- Monte Carlo VaR (Simulation-based risk estimation)
- Stress-Testing (5 Historical Crypto Scenarios)
- Risk-Limit Enforcement (Circuit-Breaker)

**Tests:** 177/177 passed (100%)  
_(96 core + 81 validation tests)_

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

### Phases 9A/9B/10: VaR Backtest Suite 🆕

**Status:** ✅ Live on main (merged 2025-12-29)

**Features:**
- **Phase 9A: Duration-Based Independence Diagnostic** - Detects temporal clustering in VaR violations
- **Phase 9B: Rolling-Window Evaluation** - Tests model stability over time
- **Phase 10: Operator Snapshot Runner** - Single-command CLI for backtest snapshots

**Key Components:**
- `duration_independence_diagnostic()` - Measures time between violations (stdlib-only)
- `rolling_evaluation()` - Runs UC/IND/CC tests over multiple windows
- `scripts&#47;risk&#47;run_var_backtest_suite_snapshot.py` - CLI tool with markdown reports

**Documentation:**
- [VaR Backtest Suite Guide](VAR_BACKTEST_SUITE_GUIDE.md) - Complete operator guide

**Usage:**
```bash
# Quick snapshot with all diagnostics
python3 scripts/risk/run_var_backtest_suite_snapshot.py \
  --returns-file data/returns.csv \
  --var-file data/var.csv \
  --confidence 0.99 \
  --enable-duration-diagnostic \
  --enable-rolling \
  --rolling-window-size 250
```

---

### Phase 2: VaR Validation 🆕

**Status:** ✅ Live on main (PR #413 merged 2025-12-28)

**Features:**
- **Kupiec POF Test** - Statistical validation of VaR breach rate
- **Basel Traffic Light System** - Regulatory classification (Green/Yellow/Red zones)
- **Full Backtest Runner** - Automated VaR validation workflow
- **Breach Analysis** - Pattern detection (clustering, gaps, streaks)

**Pure Python Implementation:**
- ✅ No SciPy dependency
- ✅ Chi-square p-value via `math.erfc()`
- ✅ Deterministic & CI-safe

**Tests:** 81/81 passed (100%)

**Usage:**
```python
from src.risk.var import historical_var
from src.risk.validation import run_var_backtest

# Calculate VaR
var_value = historical_var(returns_train, alpha=0.05)

# Run backtest
var_series = pd.Series(var_value, index=returns_test.index)
result = run_var_backtest(
    returns=returns_test,
    var_series=var_series,
    confidence_level=0.95
)

print(f"Kupiec Test: {result.kupiec.result}")
print(f"Basel Traffic Light: {result.traffic_light.color}")
print(result.to_markdown())  # Generate report
```

**Documentation:**
- Phase 2 Implementation Report (archived)
- Phase 2 Test Hardening Report (archived)
- Integration Guide (planned) - Workflows & Examples

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
python3 -m pytest tests/risk/ -v
```

### Generate Stress-Report

```bash
python3 scripts/run_risk_stress_report.py --symbol BTC/EUR --output reports/stress.csv
```

---

## Support

**Questions?**
1. Check Operator-Guide: `RISK_LAYER_V1_OPERATOR_GUIDE.md`
2. Check Tests: `tests&#47;risk&#47;` (Usage-Examples)
3. Run Tests: `python3 -m pytest tests&#47;risk&#47; -v`

**Issues?**
- Check Troubleshooting-Section in Operator-Guide
- Review Test-Failures for similar cases
- Check Linter: `read_lints` tool

---

## Changelog

### 2026-01-04: Phase 8C - VaR Backtest Suite Runner & Report Formatter 🆕
- **Suite Runner:** Aggregates all VaR backtests (Kupiec POF, Basel, Christoffersen IND/CC) in one run
- **Report Formatter:** Deterministic JSON + Markdown output (stable keys, 6-decimal precision)
- **CLI Script:** `scripts&#47;risk&#47;run_var_backtest_suite.py` for operator convenience
- **3 Test Modules:** Unit tests (suite_runner, report_formatter) + Golden/Snapshot tests
- **Overall Result Logic:** PASS only if all tests green (else FAIL)
- **Stdlib-only:** No external dependencies beyond pandas
- **Operator Guide:** [VAR_BACKTEST_SUITE_QUICKSTART.md](VAR_BACKTEST_SUITE_QUICKSTART.md)
- **Status:** ✅ Production-Ready (regression-safe, deterministic)

### 2026-01-04: Phase 8B - Christoffersen VaR Backtests 🆕
- **47 new tests** for Christoffersen tests (100% pass)
- Independence Test (LR-IND) - Detects violation clustering
- Conditional Coverage Test (LR-CC) - Combined UC + IND
- CLI Integration: `--tests uc|ind|cc|all`
- Stdlib-only implementation (no scipy/numpy)
- Comprehensive guide: [CHRISTOFFERSEN_TESTS_GUIDE.md](CHRISTOFFERSEN_TESTS_GUIDE.md)
- PR #422 merged to main
- Merge Log: [docs/ops/merge-logs/2026-01-04_feat-var-backtest-christoffersen-cc_merge_log.md](../ops/merge-logs/2026-01-04_feat-var-backtest-christoffersen-cc_merge_log.md)

### 2025-12-28: Phase 2 - VaR Validation 🆕
- **81 new tests** for VaR validation (100% pass)
- Kupiec POF Test (pure Python, no SciPy)
- Basel Traffic Light System
- Full backtest runner with breach analysis
- JSON & Markdown report generation
- Integration Guide with workflows
- PR #413 merged to main

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

**Last Updated:** 2026-01-04
