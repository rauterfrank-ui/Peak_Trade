# tests/test_live_risk_limits_portfolio_bridge.py
"""
Tests für Portfolio-Level Risk Bridge (Phase 48)
=================================================

Tests für:
- LiveRiskLimits.evaluate_portfolio()
- Portfolio-Level Risk-Checks
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.live.portfolio_monitor import (
    LivePortfolioSnapshot,
    LivePositionSnapshot,
)
from src.live.risk_limits import LiveRiskConfig, LiveRiskLimits

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_portfolio_snapshot() -> LivePortfolioSnapshot:
    """Erstellt Sample-Portfolio-Snapshot."""
    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=0.5,
            entry_price=28000.0,
            mark_price=29500.0,
            notional=14750.0,
            unrealized_pnl=750.0,
            realized_pnl=120.0,
        ),
        LivePositionSnapshot(
            symbol="ETH/EUR",
            side="short",
            size=2.0,
            entry_price=1800.0,
            mark_price=1750.0,
            notional=3500.0,
            unrealized_pnl=100.0,
            realized_pnl=0.0,
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
    )

    return snapshot


@pytest.fixture
def risk_config_low_limits() -> LiveRiskConfig:
    """Erstellt LiveRiskConfig mit niedrigen Limits (für Verletzungs-Tests)."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=10000.0,  # Niedrig (Snapshot hat 18250.0)
        max_symbol_exposure_notional=5000.0,  # OK für beide Symbole
        max_open_positions=5,  # OK
        max_order_notional=None,
        max_daily_loss_abs=500.0,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )


@pytest.fixture
def risk_config_ok_limits() -> LiveRiskConfig:
    """Erstellt LiveRiskConfig mit ausreichend hohen Limits (OK-Fall)."""
    return LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=50000.0,  # Hoch genug
        max_symbol_exposure_notional=20000.0,  # Hoch genug
        max_open_positions=10,  # Hoch genug
        max_order_notional=None,
        max_daily_loss_abs=1000.0,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )


# =============================================================================
# TESTS
# =============================================================================


def test_evaluate_portfolio_total_exposure_exceeded(
    sample_portfolio_snapshot: LivePortfolioSnapshot,
    risk_config_low_limits: LiveRiskConfig,
):
    """Testet Total Exposure-Limit-Verletzung."""
    risk_limits = LiveRiskLimits(risk_config_low_limits)

    result = risk_limits.evaluate_portfolio(sample_portfolio_snapshot)

    assert result.allowed is False
    assert any("max_total_exposure_exceeded" in reason for reason in result.reasons)
    assert result.metrics["portfolio_total_notional"] == pytest.approx(18250.0, abs=0.01)


def test_evaluate_portfolio_symbol_exposure_exceeded():
    """Testet Symbol Exposure-Limit-Verletzung."""
    # Portfolio mit hoher Symbol-Exposure
    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=1.0,
            mark_price=30000.0,
            notional=30000.0,  # Überschreitet Limit
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
    )

    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=50000.0,
        max_symbol_exposure_notional=20000.0,  # Niedrig (Position hat 30000.0)
        max_open_positions=10,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config)
    result = risk_limits.evaluate_portfolio(snapshot)

    assert result.allowed is False
    assert any("max_symbol_exposure_exceeded" in reason for reason in result.reasons)
    assert "BTC/EUR" in str(result.reasons)


def test_evaluate_portfolio_max_open_positions_exceeded():
    """Testet Max Open Positions-Limit-Verletzung."""
    # Portfolio mit vielen Positionen
    positions = [
        LivePositionSnapshot(
            symbol=f"SYM{i}/EUR",
            side="long",
            size=0.1,
            mark_price=100.0,
            notional=10.0,
        )
        for i in range(10)  # 10 Positionen
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
    )

    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=50000.0,
        max_symbol_exposure_notional=20000.0,
        max_open_positions=5,  # Niedrig (Portfolio hat 10)
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config)
    result = risk_limits.evaluate_portfolio(snapshot)

    assert result.allowed is False
    assert any("max_open_positions_exceeded" in reason for reason in result.reasons)


def test_evaluate_portfolio_ok_case(
    sample_portfolio_snapshot: LivePortfolioSnapshot,
    risk_config_ok_limits: LiveRiskConfig,
):
    """Testet OK-Fall: Portfolio innerhalb aller Limits."""
    risk_limits = LiveRiskLimits(risk_config_ok_limits)

    result = risk_limits.evaluate_portfolio(sample_portfolio_snapshot)

    assert result.allowed is True
    assert len(result.reasons) == 0 or all(
        "exceeded" not in r and "reached" not in r for r in result.reasons
    )

    # Prüfe Metrics
    assert result.metrics["portfolio_total_notional"] == pytest.approx(18250.0, abs=0.01)
    assert result.metrics["portfolio_num_open_positions"] == 2
    assert "BTC/EUR" in result.metrics["portfolio_symbol_notional"]
    assert "ETH/EUR" in result.metrics["portfolio_symbol_notional"]


def test_evaluate_portfolio_disabled():
    """Testet dass Risk-Checks übersprungen werden, wenn disabled."""
    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=1.0,
            mark_price=30000.0,
            notional=30000.0,
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
    )

    config = LiveRiskConfig(
        enabled=False,  # Deaktiviert
        base_currency="EUR",
        max_total_exposure_notional=1000.0,  # Würde verletzt werden
        max_symbol_exposure_notional=1000.0,
        max_open_positions=1,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config)
    result = risk_limits.evaluate_portfolio(snapshot)

    assert result.allowed is True
    assert result.metrics["live_risk_enabled"] is False


def test_evaluate_portfolio_metrics_includes_account_data():
    """Testet dass Account-Daten in Metrics enthalten sind (falls verfügbar)."""
    positions = [
        LivePositionSnapshot(
            symbol="BTC/EUR",
            side="long",
            size=0.5,
            mark_price=30000.0,
            notional=15000.0,
        ),
    ]

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=positions,
        equity=20000.0,
        cash=5000.0,
        margin_used=15000.0,
    )

    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=50000.0,
        max_symbol_exposure_notional=20000.0,
        max_open_positions=10,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config)
    result = risk_limits.evaluate_portfolio(snapshot)

    assert "portfolio_equity" in result.metrics
    assert result.metrics["portfolio_equity"] == pytest.approx(20000.0, abs=0.01)
    assert "portfolio_cash" in result.metrics
    assert result.metrics["portfolio_cash"] == pytest.approx(5000.0, abs=0.01)
    assert "portfolio_margin_used" in result.metrics
    assert result.metrics["portfolio_margin_used"] == pytest.approx(15000.0, abs=0.01)


def test_evaluate_portfolio_empty_portfolio():
    """Testet leeres Portfolio."""
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[],
    )

    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_total_exposure_notional=1000.0,
        max_symbol_exposure_notional=500.0,
        max_open_positions=1,
        max_order_notional=None,
        max_daily_loss_abs=None,
        max_daily_loss_pct=None,
        block_on_violation=True,
        use_experiments_for_daily_pnl=True,
    )

    risk_limits = LiveRiskLimits(config)
    result = risk_limits.evaluate_portfolio(snapshot)

    assert result.allowed is True
    assert result.metrics["portfolio_num_open_positions"] == 0
    assert result.metrics["portfolio_total_notional"] == 0.0
