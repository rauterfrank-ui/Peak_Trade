"""
Tests für neue Strategien
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np

from src.strategies.bollinger import generate_signals as bb_signals
from src.strategies.macd import generate_signals as macd_signals
from src.strategies.ecm import generate_signals as ecm_signals, calculate_ecm_phase
from src.core import get_strategy_cfg
from datetime import datetime


def create_test_data(n=200):
    """Erstellt Test-Daten."""
    dates = pd.date_range('2024-01-01', periods=n, freq='1h')
    prices = 50000 + np.cumsum(np.random.randn(n) * 100)
    
    return pd.DataFrame({
        'open': prices * 0.999,
        'high': prices * 1.002,
        'low': prices * 0.998,
        'close': prices,
        'volume': 100
    }, index=dates)


def test_bollinger_config():
    """Test: Bollinger-Config laden."""
    params = get_strategy_cfg('bollinger_bands')
    assert 'bb_period' in params
    assert 'bb_std' in params


def test_macd_config():
    """Test: MACD-Config laden."""
    params = get_strategy_cfg('macd')
    assert 'fast_ema' in params
    assert 'slow_ema' in params


def test_ecm_config():
    """Test: ECM-Config laden."""
    params = get_strategy_cfg('ecm_cycle')
    assert 'ecm_cycle_days' in params
    assert 'ecm_confidence_threshold' in params


def test_ecm_phase_calculation():
    """Test: ECM-Phase wird korrekt berechnet."""
    ref = datetime(2020, 1, 18)
    current = datetime(2021, 1, 18)  # 1 Jahr später
    
    phase_info = calculate_ecm_phase(current, ref)
    
    assert 'phase' in phase_info
    assert 'confidence' in phase_info
    assert 0 <= phase_info['phase'] <= 1
    assert 0 <= phase_info['confidence'] <= 1


def test_bollinger_signals():
    """Test: Bollinger-Signale werden generiert."""
    df = create_test_data(200)
    params = {'bb_period': 20, 'bb_std': 2.0, 
              'entry_threshold': 0.95, 'exit_threshold': 0.5, 'stop_pct': 0.03}
    
    signals = bb_signals(df, params)
    assert len(signals) == len(df)


def test_macd_signals():
    """Test: MACD-Signale werden generiert."""
    df = create_test_data(200)
    params = {'fast_ema': 12, 'slow_ema': 26, 
              'signal_ema': 9, 'stop_pct': 0.025}
    
    signals = macd_signals(df, params)
    assert len(signals) == len(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
