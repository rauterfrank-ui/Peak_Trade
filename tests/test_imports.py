"""
Peak_Trade Import Tests
=======================
Stellt sicher, dass alle Hauptmodule importierbar sind.
"""

import pytest


def test_can_import_src():
    """Test: src-Paket ist importierbar."""
    import src
    assert hasattr(src, "__version__")


def test_can_import_core():
    """Test: Core-Module sind importierbar."""
    from src.core import peak_config
    from src.core import position_sizing
    from src.core import risk
    from src.core import experiments


def test_can_import_strategies():
    """Test: Strategies-Module sind importierbar."""
    from src.strategies import base
    from src.strategies import registry
    from src.strategies import ma_crossover


def test_can_import_backtest():
    """Test: Backtest-Module sind importierbar."""
    from src.backtest import engine
    from src.backtest import stats


def test_can_import_live():
    """Test: Live-Module sind importierbar."""
    from src.live import orders
    from src.live import broker_base
    from src.live import risk_limits
    from src.live import workflows


def test_strategy_registry_available():
    """Test: Strategy Registry funktioniert."""
    from src.strategies.registry import get_available_strategy_keys

    keys = get_available_strategy_keys()
    assert isinstance(keys, list)
    assert len(keys) > 0
    assert "ma_crossover" in keys
