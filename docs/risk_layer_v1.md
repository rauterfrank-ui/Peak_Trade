# Risk Layer v1 - Implementation Guide

## Überblick

Der **Risk Layer v1** erweitert Peak_Trade um Portfolio-Level Risk Management mit:

- **Portfolio-Exposure**: Gross/Net Exposure Limits
- **Position Weights**: Max-Weight pro Position
- **VaR/CVaR**: Historical & Parametric Value at Risk
- **Stress Testing**: Szenario-basierte Risk-Analyse
- **Risk-Limit Enforcement**: Circuit-Breaker-Semantik bei Hard Breaches

## Architektur

```
src/risk/
├── types.py          # PositionSnapshot, PortfolioSnapshot, RiskBreach, RiskDecision
├── portfolio.py      # Exposure/Weight/Correlation-Berechnungen
├── var.py            # VaR/CVaR (Historical + Parametric)
├── stress.py         # Stress-Testing-Engine
├── enforcement.py    # RiskEnforcer + RiskLimitsV2
└── __init__.py       # Public API

src/core/risk.py      # PortfolioVaRStressRiskManager (Integration)
```

## Verwendung

### 1. Config-basiert (empfohlen)

**config/config.toml:**
```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05      # 95% VaR/CVaR
window = 252      # Rolling-Window (1 Jahr)

[risk.limits]
max_gross_exposure = 1.5    # 150% of Equity
max_position_weight = 0.35  # 35% max per Position
max_var = 0.08              # 8% VaR-Limit
max_cvar = 0.12             # 12% CVaR-Limit
```

**Python:**
```python
from src.core.peak_config import load_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine

cfg = load_config()
risk_manager = build_risk_manager_from_config(cfg)

engine = BacktestEngine(risk_manager=risk_manager)
result = engine.run_realistic(df, strategy_fn, params)

print(f"Sharpe: {result.stats['sharpe']:.2f}")
```

### 2. Programmatisch

```python
from src.core.risk import PortfolioVaRStressRiskManager
from src.backtest.engine import BacktestEngine

risk_manager = PortfolioVaRStressRiskManager(
    alpha=0.05,
    window=252,
    max_gross_exposure=1.5,
    max_position_weight=0.35,
    max_var=0.08,
    max_cvar=0.12,
)

engine = BacktestEngine(risk_manager=risk_manager)
result = engine.run_realistic(df, strategy_fn, params)
```

## Module-Details

### types.py

**PositionSnapshot**: Einzelne Position
```python
from src.risk import PositionSnapshot

pos = PositionSnapshot(
    symbol="BTC/EUR",
    units=0.5,
    price=50000,
    timestamp=pd.Timestamp.now()
)
print(pos.notional)  # 25000.0
```

**PortfolioSnapshot**: Vollständiges Portfolio
```python
from src.risk import PortfolioSnapshot, PositionSnapshot

snapshot = PortfolioSnapshot(
    equity=100000,
    positions=[
        PositionSnapshot("BTC/EUR", 0.5, 50000),
        PositionSnapshot("ETH/EUR", 10, 3000),
    ]
)

print(snapshot.get_gross_exposure())  # 55000.0
print(snapshot.get_net_exposure())    # 55000.0 (beide long)
```

**RiskBreach & RiskDecision**: Enforcement-Results
```python
from src.risk import RiskBreach, RiskDecision, BreachSeverity

breach = RiskBreach(
    code="MAX_VAR",
    message="VaR exceeds limit",
    severity=BreachSeverity.HARD,
    metrics={"var": 0.10, "limit": 0.08}
)

decision = RiskDecision(
    allowed=False,
    action="HALT",
    breaches=[breach]
)

print(decision.has_hard_breach())  # True
```

### portfolio.py

Portfolio-Analytics:
```python
from src.risk import compute_gross_exposure, compute_weights
from src.risk import PositionSnapshot

positions = [
    PositionSnapshot("BTC/EUR", 0.5, 50000),
    PositionSnapshot("ETH/EUR", 10, 3000),
]

gross = compute_gross_exposure(positions)  # 55000.0
weights = compute_weights(positions, equity=100000)
# {'BTC/EUR': 0.25, 'ETH/EUR': 0.30}
```

### var.py

VaR/CVaR-Berechnung:
```python
import pandas as pd
from src.risk import historical_var, historical_cvar

returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])

var_95 = historical_var(returns, alpha=0.05)
cvar_95 = historical_cvar(returns, alpha=0.05)

print(f"VaR(95%): {var_95:.2%}")
print(f"CVaR(95%): {cvar_95:.2%}")
```

### stress.py

Stress-Testing:
```python
import pandas as pd
from src.risk import StressScenario, run_stress_suite

returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])

scenarios = [
    StressScenario("baseline", "shock", {"shock_pct": 0.0}),
    StressScenario("crash", "shock", {"shock_pct": -0.20}),
    StressScenario("vol_spike", "vol_spike", {"multiplier": 3.0}),
]

results = run_stress_suite(returns, scenarios, alpha=0.05)
print(results[['scenario', 'var', 'cvar', 'min', 'total_return']])
```

### enforcement.py

Risk-Limit-Enforcement:
```python
from src.risk import (
    RiskLimitsV2,
    RiskEnforcer,
    PortfolioSnapshot,
    PositionSnapshot,
)
import pandas as pd

limits = RiskLimitsV2(
    max_gross_exposure=1.5,
    max_position_weight=0.35,
    max_var=0.08,
    alpha=0.05,
)

snapshot = PortfolioSnapshot(
    equity=100000,
    positions=[PositionSnapshot("BTC/EUR", 0.5, 50000)]
)

returns = pd.Series([0.01, -0.02, 0.03, -0.01])

enforcer = RiskEnforcer()
decision = enforcer.evaluate_portfolio(snapshot, returns, limits)

if not decision.allowed:
    print(f"Trading HALTED: {decision.get_breach_summary()}")
```

## PortfolioVaRStressRiskManager

Der **PortfolioVaRStressRiskManager** integriert den v1-Layer in die Backtest-Engine:

**Features:**
- Automatisches Returns-Tracking (Rolling Window)
- Portfolio-Snapshot-Erstellung aus Backtest-State
- Circuit-Breaker bei HARD Breaches
- Backward-compatible (via **kwargs)

**Config:**
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

**API:**
```python
from src.core.risk import PortfolioVaRStressRiskManager

manager = PortfolioVaRStressRiskManager(
    alpha=0.05,
    window=252,
    max_gross_exposure=1.5,
    max_var=0.08,
)

# Im Backtest wird adjust_target_position() automatisch aufgerufen
# Bei Hard Breach: returns 0.0 -> Trading gestoppt
```

## Integration in BacktestEngine

Die BacktestEngine ruft `adjust_target_position()` des RiskManagers vor jedem Trade:

```python
# src/backtest/engine.py (vereinfacht)

if self.risk_manager is not None:
    risk_kwargs = {
        "symbol": symbol,
        "last_return": ...,
        "positions": [...],  # PositionSnapshots
    }

    target_units = self.risk_manager.adjust_target_position(
        target_units=target_units,
        price=entry_price,
        equity=equity,
        timestamp=trade_dt,
        **risk_kwargs,
    )

    if target_units == 0:
        # Trading HALTED by RiskManager
        ...
```

## Beispiel-Szenarien

### Szenario 1: Aggressive Strategy mit VaR-Limit

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05
window = 126  # 6 Monate

[risk.limits]
max_gross_exposure = 2.0
max_position_weight = 0.50
max_var = 0.15
```

→ Erlaubt 200% Gross Exposure, stoppt bei VaR > 15%

### Szenario 2: Conservative Strategy

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.01  # 99% VaR (extremer Tail)
window = 252

[risk.limits]
max_gross_exposure = 1.0
max_position_weight = 0.20
max_var = 0.05
max_cvar = 0.08
```

→ Kein Leverage, max 20% per Position, VaR-Limit bei 5%

## Testing

Unit-Tests für alle Module:
```bash
python3 -m pytest tests/test_risk_layer_v1.py -v
```

Integration-Tests mit BacktestEngine:
```bash
python3 -m pytest tests/test_backtest_risk_integration.py -v
```

## Roadmap / TODOs

- [ ] Multi-Asset-Support (Correlation-Checks)
- [ ] Parametric VaR ohne scipy-Dependency (vollständiger Fallback)
- [ ] Stress-Testing: Mehr Szenarien (Contagion, Liquidity Crisis, etc.)
- [ ] Real-Time Risk-Monitoring (Integration in Live-Trading)
- [ ] Risk-Report-Generation (PDF/HTML mit Visualisierungen)

## Design-Prinzipien

1. **Modular**: Jedes Modul hat klare Verantwortung
2. **Testbar**: Alle Funktionen deterministisch testbar
3. **Safe-by-default**: Bei Violations klarer deterministischer Pfad
4. **Backward-compatible**: Bestehende RiskManager laufen weiter
5. **Config-driven**: Alle Limits via Config steuerbar

## References

- **src/risk/**: Alle v1-Module
- **src/core/risk.py**: Integration in Backtest
- **config/risk_layer_v1_example.toml**: Config-Beispiele
- **tests/test_risk_layer_v1.py**: Unit-Tests (TODO)
