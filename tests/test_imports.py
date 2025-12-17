"""
Peak_Trade Import Tests
=======================
Stellt sicher, dass alle Hauptmodule importierbar sind.
"""



def test_can_import_src():
    """Test: src-Paket ist importierbar."""
    import src
    assert hasattr(src, "__version__")


def test_can_import_core():
    """Test: Core-Module sind importierbar."""


def test_can_import_strategies():
    """Test: Strategies-Module sind importierbar."""


def test_can_import_backtest():
    """Test: Backtest-Module sind importierbar."""


def test_can_import_live():
    """Test: Live-Module sind importierbar."""


def test_strategy_registry_available():
    """Test: Strategy Registry funktioniert."""
    from src.strategies.registry import get_available_strategy_keys

    keys = get_available_strategy_keys()
    assert isinstance(keys, list)
    assert len(keys) > 0
    assert "ma_crossover" in keys
