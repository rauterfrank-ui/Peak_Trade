"""
Test für Portfolio-Manager
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from src.portfolio import PortfolioManager
from src.strategies.ma_crossover import generate_signals as ma_signals
from src.strategies.momentum import generate_signals as momentum_signals


def create_test_data(n_bars=200):
    """Erstellt Test-Daten."""
    dates = pd.date_range("2024-01-01", periods=n_bars, freq="1h")

    prices = 50000 + np.cumsum(np.random.randn(n_bars) * 100)

    return pd.DataFrame(
        {
            "open": prices * 0.999,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "close": prices,
            "volume": 100,
        },
        index=dates,
    )


def test_portfolio_manager_basic():
    """Test: Portfolio-Manager kann Strategien hinzufügen."""
    pm = PortfolioManager()

    params_ma = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
    params_mom = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }

    pm.add_strategy("ma_test", ma_signals, params_ma)
    pm.add_strategy("mom_test", momentum_signals, params_mom)

    assert len(pm.strategies) == 2


def test_portfolio_backtest():
    """Test: Portfolio-Backtest läuft durch."""
    pm = PortfolioManager()
    pm.total_capital = 10000

    params_ma = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
    pm.add_strategy("ma_test", ma_signals, params_ma)

    df = create_test_data(n_bars=200)

    result = pm.run_backtest(df, allocation_method="equal")

    assert result.portfolio_equity is not None
    assert len(result.strategy_results) == 1
    assert "total_return" in result.stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
