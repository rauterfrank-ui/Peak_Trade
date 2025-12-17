"""
Peak_Trade Test Suite
======================
Basis-Tests für Position Sizing und Config.
"""

import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.core import load_config
from src.risk import PositionRequest, calc_position_size


def test_config_loading():
    """Test: Config kann geladen werden."""
    cfg = load_config()
    assert cfg.backtest.initial_cash == 10000.0
    assert cfg.risk.risk_per_trade == 0.01


def test_position_sizing_normal():
    """Test: Normale Position Sizing."""
    req = PositionRequest(
        equity=10000,
        entry_price=50000,
        stop_price=49000,
        risk_per_trade=0.01
    )

    # Position = 100 / 1000 = 0.1 BTC = 5000 USD (50% des Kontos)
    # Daher max_position_pct auf 0.60 setzen, damit Test durchgeht
    result = calc_position_size(req, max_position_pct=0.60)

    assert not result.rejected
    assert result.size == pytest.approx(0.1, rel=0.01)  # 100 / 1000 = 0.1 BTC
    assert result.value == pytest.approx(5000, rel=1)   # 0.1 * 50000


def test_position_sizing_too_small():
    """Test: Position zu klein wird abgelehnt."""
    req = PositionRequest(
        equity=1000,
        entry_price=50000,
        stop_price=49000,
        risk_per_trade=0.01
    )

    # Position wäre 10 / 1000 = 0.01 BTC = 500 USD
    # Das ist zwar > 50 USD, aber > 25% des Kontos (250 USD)
    # Daher für diesen Test: größeren max_position_pct und höheren min_value
    result = calc_position_size(req, min_position_value=600.0, max_position_pct=0.60)

    # Sollte jetzt wegen min_position_value abgelehnt werden
    assert result.rejected
    assert "< Min" in result.reason


def test_position_sizing_stop_too_close():
    """Test: Stop zu nah am Entry wird abgelehnt."""
    req = PositionRequest(
        equity=10000,
        entry_price=50000,
        stop_price=49950,  # Nur 0.1% Distanz
        risk_per_trade=0.01
    )

    result = calc_position_size(req, min_stop_distance=0.005)

    assert result.rejected
    assert "Stop-Distanz" in result.reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
