"""
Test für Strategy Config-Funktionen
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.core import get_strategy_cfg, list_strategies


def test_get_strategy_cfg_success():
    """Test: Strategie-Config erfolgreich laden."""
    params = get_strategy_cfg("ma_crossover")
    
    assert 'fast_period' in params
    assert 'slow_period' in params
    assert 'stop_pct' in params
    
    assert params['fast_period'] == 10
    assert params['slow_period'] == 30
    assert params['stop_pct'] == 0.02


def test_get_strategy_cfg_not_found():
    """Test: Fehler bei nicht existierender Strategie."""
    
    with pytest.raises(KeyError) as exc_info:
        get_strategy_cfg("non_existent_strategy")
    
    error_msg = str(exc_info.value)
    assert "non_existent_strategy" in error_msg
    assert "nicht in config.toml definiert" in error_msg
    assert "Verfügbare Strategien" in error_msg


def test_list_strategies():
    """Test: Liste aller Strategien."""
    strategies = list_strategies()
    
    assert isinstance(strategies, list)
    assert "ma_crossover" in strategies
    assert strategies == sorted(strategies)  # Sollte sortiert sein


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
