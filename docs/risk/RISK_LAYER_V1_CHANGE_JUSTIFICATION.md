# Risk Layer V1 – Change Justification (for review)

## Scope
This PR introduces Risk Layer V1 (new modules under `src/risk/` + tests).

## Risk limit values
- Any `max_drawdown` values in this PR are **examples** or **defaults** intended for controlled test/backtest environments.
- Production deployment requires explicit operator configuration and governance approval.

## Why this change is safe
- Comprehensive tests under `tests/risk/*` (96 tests, 100% pass)
- No live execution switching / no auto-deploy behavior introduced by this PR alone
- Operator guide documents required steps + constraints

## Test plan
- `pytest -q tests&#47;risk` (96 tests)
- Full CI (tests, lint, strategy-smoke)
- Review by governance/risk owners

## Modules introduced
- `src/risk/types.py` - Risk layer type definitions (PortfolioState, RiskMetrics, etc.)
- `src/risk/var.py` - VaR/CVaR calculations (historical + parametric methods)
- `src/risk/stress.py` - Stress testing engine
- `src/risk/portfolio.py` - Portfolio risk analytics
- `src/risk/enforcement.py` - Risk limit enforcement

## Documentation
- `docs/risk_layer_v1.md` - Module overview
- `docs/risk/RISK_LAYER_V1_OPERATOR_GUIDE.md` - Operator guide
- `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md` - Implementation details
- `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md` - Production readiness checklist

## Integration points
- `src/core/risk.py` - Extended with Risk Layer V1 integration
- `src/backtest/engine.py` - Risk metrics tracking during backtests
- `config/risk_layer_v1_example.toml` - Example configuration (for reference only)

## No impact on existing systems
- All new modules are opt-in
- Existing position sizing and risk checks unchanged
- No breaking changes to existing APIs
