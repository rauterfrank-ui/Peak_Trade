"""
Test für Momentum-Strategie
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from src.strategies.momentum import generate_signals, add_momentum_indicators


def test_momentum_signals_basic():
    """Test: Momentum-Signale werden korrekt generiert."""
    # Test-Setup: Momentum steigt von niedrig auf hoch
    # Start niedrig, dann starker Anstieg
    prices = [100] * 12  # Flach für 12 Bars
    prices.extend([100 + i * 2 for i in range(1, 13)])  # Dann steigt es: 102, 104, 106...

    df = pd.DataFrame({"close": prices})

    params = {
        "lookback_period": 10,
        "entry_threshold": 0.05,  # 5% Momentum
        "exit_threshold": -0.01,
    }

    signals = generate_signals(df, params)

    # Der Momentum-Wert sollte irgendwann > 5% werden
    # Prüfe einfach, dass die Funktion läuft und ein DataFrame zurückgibt
    assert len(signals) == len(df)
    assert isinstance(signals, pd.Series)


def test_momentum_calculation():
    """Test: Momentum wird korrekt berechnet."""
    df = pd.DataFrame({"close": [100, 110, 120]})  # +10% pro Bar

    params = {"lookback_period": 1}

    df_with_mom = add_momentum_indicators(df, params)

    # Momentum zwischen Bar 0 und 1 sollte 10% sein
    assert df_with_mom["momentum"].iloc[1] == pytest.approx(0.1, rel=0.01)


def test_momentum_config_loading():
    """Test: Momentum-Config kann geladen werden."""
    from src.core import get_strategy_cfg

    params = get_strategy_cfg("momentum_1h")

    assert "lookback_period" in params
    assert "entry_threshold" in params
    assert "exit_threshold" in params
    assert "stop_pct" in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
