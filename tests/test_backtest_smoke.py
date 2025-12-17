"""
Peak_Trade Backtest Smoke Tests
===============================
Minimaler Smoke-Test für die Backtest-Engine.
"""

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestEngine
from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config


def create_dummy_ohlcv(n_bars: int = 200) -> pd.DataFrame:
    """Erzeugt synthetische OHLCV-Daten für Tests."""
    np.random.seed(42)

    # Zeitindex (stündlich, UTC)
    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")

    # Random Walk für Close
    returns = np.random.normal(0, 0.01, n_bars)
    # Trend hinzufügen für Crossovers
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.005
    returns = returns + trend
    close_prices = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=idx)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)

    # High/Low
    high_bump = np.random.uniform(0, 0.003, n_bars)
    low_dip = np.random.uniform(0, 0.003, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def test_backtest_engine_init():
    """Test: BacktestEngine kann instanziiert werden."""
    cfg = load_config()

    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager,
    )

    assert engine is not None


def test_backtest_smoke_run():
    """Test: Minimaler Backtest-Durchlauf."""
    cfg = load_config()

    # Dummy-Daten
    df = create_dummy_ohlcv(200)

    # Engine mit Default-Konfig
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager,
    )

    # Einfache Signal-Funktion (immer Long)
    def simple_signal_fn(data, params):
        return pd.Series(1, index=data.index)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_signal_fn,
        strategy_params={},
    )

    # Prüfungen
    assert result is not None
    assert hasattr(result, "equity_curve")
    assert hasattr(result, "stats")
    assert len(result.equity_curve) > 0

    # Stats prüfen
    assert "total_return" in result.stats
    assert "sharpe" in result.stats
    assert "max_drawdown" in result.stats
    assert "total_trades" in result.stats


def test_backtest_with_ma_crossover():
    """Test: Backtest mit MA Crossover Strategie."""
    from src.strategies.registry import create_strategy_from_config

    cfg = load_config()
    df = create_dummy_ohlcv(300)

    # Strategie aus Registry
    strategy = create_strategy_from_config("ma_crossover", cfg)

    # Engine
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager,
    )

    # Signal-Wrapper
    def strategy_fn(data, params):
        return strategy.generate_signals(data)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_fn,
        strategy_params={},
    )

    assert result is not None
    assert "total_return" in result.stats
