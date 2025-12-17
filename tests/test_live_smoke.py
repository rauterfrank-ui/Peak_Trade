"""
Peak_Trade Live/Paper Smoke Tests
=================================
Tests für Live-Risk-Limits und Workflows.
"""

import pytest

from src.core.peak_config import load_config
from src.live.orders import LiveOrderRequest, side_from_direction
from src.live.risk_limits import LiveRiskCheckResult, LiveRiskConfig, LiveRiskLimits
from src.live.workflows import RiskCheckContext, validate_risk_flags


def test_live_order_request_creation():
    """Test: LiveOrderRequest kann erstellt werden."""
    order = LiveOrderRequest(
        client_order_id="test_001",
        symbol="BTC/EUR",
        side="BUY",
        order_type="MARKET",
        quantity=0.001,
        notional=50.0,
    )

    assert order.symbol == "BTC/EUR"
    assert order.side == "BUY"
    assert order.quantity == 0.001
    assert order.notional == 50.0


def test_side_from_direction():
    """Test: Direction-zu-Side Konvertierung."""
    assert side_from_direction(1) == "BUY"
    assert side_from_direction(-1) == "SELL"
    assert side_from_direction(0) is None


def test_live_risk_config_dataclass():
    """Test: LiveRiskConfig Dataclass."""
    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_daily_loss_abs=500.0,
        max_daily_loss_pct=5.0,
        max_total_exposure_notional=5000.0,
        max_symbol_exposure_notional=2000.0,
        max_open_positions=5,
        max_order_notional=1000.0,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    assert config.enabled is True
    assert config.max_daily_loss_abs == 500.0


def test_live_risk_limits_from_config():
    """Test: LiveRiskLimits aus Config erstellen."""
    cfg = load_config()

    limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

    assert limits is not None
    assert limits.config is not None


def test_live_risk_check_orders_empty():
    """Test: Risk-Check mit leerer Order-Liste."""
    cfg = load_config()
    limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

    result = limits.check_orders([])

    assert isinstance(result, LiveRiskCheckResult)
    assert result.allowed is True
    assert result.metrics["n_orders"] == 0


def test_live_risk_check_orders_valid():
    """Test: Risk-Check mit gültigen Orders."""
    cfg = load_config()
    limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

    orders = [
        LiveOrderRequest(
            client_order_id="test_001",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=0.001,
            notional=100.0,
            extra={"current_price": 50000.0},
        )
    ]

    result = limits.check_orders(orders)

    assert isinstance(result, LiveRiskCheckResult)
    assert "n_orders" in result.metrics
    assert "total_notional" in result.metrics


def test_validate_risk_flags_both_set():
    """Test: Konflikt-Check für Risk-Flags."""
    with pytest.raises(ValueError):
        validate_risk_flags(enforce=True, skip=True)


def test_validate_risk_flags_valid():
    """Test: Gültige Risk-Flag-Kombinationen."""
    # Keine Exception erwartet
    validate_risk_flags(enforce=True, skip=False)
    validate_risk_flags(enforce=False, skip=True)
    validate_risk_flags(enforce=False, skip=False)


def test_risk_check_context_creation():
    """Test: RiskCheckContext erstellen."""
    cfg = load_config()

    ctx = RiskCheckContext(
        config=cfg,
        starting_cash=10000.0,
        enforce=False,
        skip=False,
        tag="test",
        runner_name="test_smoke",
    )

    assert ctx.config == cfg
    assert ctx.starting_cash == 10000.0
