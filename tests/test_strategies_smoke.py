"""
Peak_Trade Strategies Smoke Tests
=================================
Tests für Strategy Registry und OOP-Strategien.
"""

import numpy as np
import pandas as pd
import pytest

from src.core.peak_config import load_config
from src.strategies.base import BaseStrategy
from src.strategies.registry import (
    create_strategy_from_config,
    get_available_strategy_keys,
)


def create_dummy_ohlcv(n_bars: int = 100) -> pd.DataFrame:
    """Erzeugt synthetische OHLCV-Daten für Tests."""
    np.random.seed(123)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    close = 50000 + np.cumsum(np.random.randn(n_bars) * 100)

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df[["open", "close"]].max(axis=1) * 1.001
    df["low"] = df[["open", "close"]].min(axis=1) * 0.999
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def test_get_available_strategy_keys():
    """Test: Liste der verfügbaren Strategien."""
    keys = get_available_strategy_keys()

    assert isinstance(keys, list)
    assert len(keys) >= 3  # Mindestens 3 OOP-Strategien

    # Bekannte Strategien
    assert "ma_crossover" in keys
    assert "rsi_reversion" in keys
    assert "breakout_donchian" in keys


def test_create_strategy_from_config_ma_crossover():
    """Test: MA Crossover Strategie erstellen."""
    cfg = load_config()

    strategy = create_strategy_from_config("ma_crossover", cfg)

    assert strategy is not None
    assert isinstance(strategy, BaseStrategy)
    assert hasattr(strategy, "KEY")
    assert strategy.KEY == "ma_crossover"


def test_create_strategy_from_config_rsi():
    """Test: RSI Reversion Strategie erstellen."""
    cfg = load_config()

    strategy = create_strategy_from_config("rsi_reversion", cfg)

    assert strategy is not None
    assert isinstance(strategy, BaseStrategy)
    assert strategy.KEY == "rsi_reversion"


def test_create_strategy_from_config_donchian():
    """Test: Donchian Breakout Strategie erstellen."""
    cfg = load_config()

    strategy = create_strategy_from_config("breakout_donchian", cfg)

    assert strategy is not None
    assert isinstance(strategy, BaseStrategy)
    assert strategy.KEY == "breakout_donchian"


def test_strategy_generate_signals():
    """Test: Strategie generiert Signale."""
    cfg = load_config()
    df = create_dummy_ohlcv(100)

    strategy = create_strategy_from_config("ma_crossover", cfg)
    signals = strategy.generate_signals(df)

    assert signals is not None
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)

    # Signale sollten nur -1, 0, 1 enthalten
    unique_values = signals.unique()
    for val in unique_values:
        assert val in [-1, 0, 1]


# R&D-Strategien, die übersprungen werden (Platzhalter oder Meta-Layer)
R_AND_D_SKIP_STRATEGIES = {
    "armstrong_cycle",
    "bouchaud_microstructure",
    "ehlers_cycle_filter",
    "el_karoui_vol_model",
    "vol_regime_overlay",
    "meta_labeling",
}


def _get_testable_strategy_keys():
    """Gibt nur testbare Strategien zurück (ohne R&D-Platzhalter)."""
    return [k for k in get_available_strategy_keys() if k not in R_AND_D_SKIP_STRATEGIES]


@pytest.mark.parametrize("strategy_key", _get_testable_strategy_keys())
def test_all_strategies_generate_signals(strategy_key):
    """Test: Alle registrierten Strategien generieren Signale."""
    cfg = load_config()
    df = create_dummy_ohlcv(150)

    strategy = create_strategy_from_config(strategy_key, cfg)
    signals = strategy.generate_signals(df)

    assert signals is not None
    assert len(signals) == len(df)


def test_strategy_invalid_key():
    """Test: Ungültiger Strategie-Key wirft Fehler."""
    cfg = load_config()

    with pytest.raises(KeyError):
        create_strategy_from_config("invalid_strategy_key_xyz", cfg)


# ============================================================================
# TESTS FÜR MIGRIERTE LEGACY-STRATEGIEN
# ============================================================================


def test_momentum_strategy_from_config():
    """Test: Momentum-Strategie erstellen und Signale generieren."""
    cfg = load_config()
    df = create_dummy_ohlcv(150)

    strategy = create_strategy_from_config("momentum_1h", cfg)

    # KEY prüfen
    assert strategy.KEY == "momentum_1h"

    # Signale generieren
    signals = strategy.generate_signals(df)
    assert signals is not None
    assert len(signals) == len(df)

    # Signale sollten nur -1, 0, 1 enthalten
    for val in signals.unique():
        assert val in [-1, 0, 1]


def test_momentum_strategy_parameters():
    """Test: Momentum-Strategie liest Config-Parameter korrekt."""
    cfg = load_config()

    strategy = create_strategy_from_config("momentum_1h", cfg)

    # Parameter aus config.toml prüfen (oder Defaults)
    assert hasattr(strategy, "lookback_period")
    assert hasattr(strategy, "entry_threshold")
    assert hasattr(strategy, "exit_threshold")
    assert strategy.lookback_period > 0
    assert strategy.entry_threshold > strategy.exit_threshold


def test_bollinger_bands_strategy_from_config():
    """Test: Bollinger Bands-Strategie erstellen und Signale generieren."""
    cfg = load_config()
    df = create_dummy_ohlcv(150)

    strategy = create_strategy_from_config("bollinger_bands", cfg)

    # KEY prüfen
    assert strategy.KEY == "bollinger_bands"

    # Signale generieren
    signals = strategy.generate_signals(df)
    assert signals is not None
    assert len(signals) == len(df)

    # Signale sollten nur -1, 0, 1 enthalten
    for val in signals.unique():
        assert val in [-1, 0, 1]


def test_bollinger_bands_strategy_parameters():
    """Test: Bollinger Bands-Strategie liest Config-Parameter korrekt."""
    cfg = load_config()

    strategy = create_strategy_from_config("bollinger_bands", cfg)

    # Parameter aus config.toml prüfen
    assert hasattr(strategy, "bb_period")
    assert hasattr(strategy, "bb_std")
    assert hasattr(strategy, "entry_threshold")
    assert strategy.bb_period > 0
    assert strategy.bb_std > 0
    assert 0 < strategy.entry_threshold <= 1


def test_macd_strategy_from_config():
    """Test: MACD-Strategie erstellen und Signale generieren."""
    cfg = load_config()
    df = create_dummy_ohlcv(150)

    strategy = create_strategy_from_config("macd", cfg)

    # KEY prüfen
    assert strategy.KEY == "macd"

    # Signale generieren
    signals = strategy.generate_signals(df)
    assert signals is not None
    assert len(signals) == len(df)

    # Signale sollten nur -1, 0, 1 enthalten
    for val in signals.unique():
        assert val in [-1, 0, 1]


def test_macd_strategy_parameters():
    """Test: MACD-Strategie liest Config-Parameter korrekt."""
    cfg = load_config()

    strategy = create_strategy_from_config("macd", cfg)

    # Parameter aus config.toml prüfen
    assert hasattr(strategy, "fast_ema")
    assert hasattr(strategy, "slow_ema")
    assert hasattr(strategy, "signal_ema")
    assert strategy.fast_ema > 0
    assert strategy.slow_ema > 0
    assert strategy.signal_ema > 0
    assert strategy.fast_ema < strategy.slow_ema


def test_migrated_strategies_all_registered():
    """Test: Alle migrierten Legacy-Strategien sind in der Registry."""
    keys = get_available_strategy_keys()

    # Ursprünglich vorhandene OOP-Strategien
    assert "ma_crossover" in keys
    assert "rsi_reversion" in keys
    assert "breakout_donchian" in keys

    # Neu migrierte Legacy-Strategien
    assert "momentum_1h" in keys
    assert "bollinger_bands" in keys
    assert "macd" in keys

    # Mindestens 6 Strategien
    assert len(keys) >= 6
