"""Tests for live session evaluation metrics."""

from datetime import datetime, timezone

import pytest

from src.live_eval.live_session_eval import Fill, compute_metrics


def test_compute_metrics_empty():
    """Test metrics computation with empty fills list."""
    metrics = compute_metrics([])

    assert metrics["total_fills"] == 0
    assert metrics["symbols"] == []
    assert metrics["start_ts"] is None
    assert metrics["end_ts"] is None
    assert metrics["total_notional"] == 0.0
    assert metrics["total_qty"] == 0.0
    assert metrics["vwap_overall"] is None
    assert metrics["realized_pnl_total"] == 0.0


def test_compute_metrics_single_fill():
    """Test metrics with a single fill."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=0.1,
            fill_price=50000.0
        )
    ]

    metrics = compute_metrics(fills)

    assert metrics["total_fills"] == 1
    assert metrics["symbols"] == ["BTC/USD"]
    assert metrics["total_notional"] == 5000.0  # 0.1 * 50000
    assert metrics["total_qty"] == 0.1
    assert metrics["vwap_overall"] == 50000.0
    assert metrics["side_breakdown"]["buy"]["count"] == 1
    assert metrics["side_breakdown"]["sell"]["count"] == 0
    assert metrics["realized_pnl_total"] == 0.0  # No sells yet


def test_compute_metrics_fifo_pnl_simple():
    """Test FIFO PnL calculation with simple scenario."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=100.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=110.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 10, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="sell",
            qty=1.5,
            fill_price=120.0
        ),
    ]

    metrics = compute_metrics(fills)

    # Realized PnL calculation:
    # - First sell of 1.0 @ 120 matches first buy @ 100: (120-100)*1.0 = 20
    # - Remaining sell of 0.5 @ 120 matches second buy @ 110: (120-110)*0.5 = 5
    # Total: 20 + 5 = 25
    assert metrics["realized_pnl_total"] == 25.0
    assert metrics["realized_pnl_per_symbol"]["BTC/USD"] == 25.0


def test_compute_metrics_fifo_pnl_exact_match():
    """Test FIFO PnL with exact buy/sell match."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="ETH/USD",
            side="buy",
            qty=2.0,
            fill_price=3000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="ETH/USD",
            side="sell",
            qty=2.0,
            fill_price=3100.0
        ),
    ]

    metrics = compute_metrics(fills)

    # PnL: (3100-3000)*2.0 = 200
    assert metrics["realized_pnl_total"] == 200.0
    assert metrics["realized_pnl_per_symbol"]["ETH/USD"] == 200.0


def test_compute_metrics_fifo_pnl_multiple_symbols():
    """Test FIFO PnL with multiple symbols."""
    fills = [
        # BTC trades
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="sell",
            qty=1.0,
            fill_price=51000.0
        ),
        # ETH trades
        Fill(
            ts=datetime(2025, 1, 15, 10, 10, 0, tzinfo=timezone.utc),
            symbol="ETH/USD",
            side="buy",
            qty=2.0,
            fill_price=3000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 15, 0, tzinfo=timezone.utc),
            symbol="ETH/USD",
            side="sell",
            qty=2.0,
            fill_price=2900.0
        ),
    ]

    metrics = compute_metrics(fills)

    # BTC PnL: (51000-50000)*1 = 1000
    # ETH PnL: (2900-3000)*2 = -200
    # Total: 1000 - 200 = 800
    assert metrics["realized_pnl_per_symbol"]["BTC/USD"] == 1000.0
    assert metrics["realized_pnl_per_symbol"]["ETH/USD"] == -200.0
    assert metrics["realized_pnl_total"] == 800.0


def test_compute_metrics_fifo_pnl_loss():
    """Test FIFO PnL with a losing trade."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="sell",
            qty=1.0,
            fill_price=49000.0
        ),
    ]

    metrics = compute_metrics(fills)

    # PnL: (49000-50000)*1 = -1000
    assert metrics["realized_pnl_total"] == -1000.0


def test_compute_metrics_side_breakdown():
    """Test side breakdown statistics."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=0.5,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=0.3,
            fill_price=51000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 10, 0, tzinfo=timezone.utc),
            symbol="ETH/USD",
            side="sell",
            qty=2.0,
            fill_price=3000.0
        ),
    ]

    metrics = compute_metrics(fills)

    # Buy stats
    assert metrics["side_breakdown"]["buy"]["count"] == 2
    assert metrics["side_breakdown"]["buy"]["qty"] == 0.8  # 0.5 + 0.3
    assert metrics["side_breakdown"]["buy"]["notional"] == 40300.0  # 0.5*50000 + 0.3*51000

    # Sell stats
    assert metrics["side_breakdown"]["sell"]["count"] == 1
    assert metrics["side_breakdown"]["sell"]["qty"] == 2.0
    assert metrics["side_breakdown"]["sell"]["notional"] == 6000.0  # 2.0*3000


def test_compute_metrics_vwap():
    """Test VWAP calculation."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=2.0,
            fill_price=51000.0
        ),
    ]

    metrics = compute_metrics(fills)

    # VWAP: (1*50000 + 2*51000) / (1 + 2) = 152000 / 3 = 50666.67
    assert abs(metrics["vwap_overall"] - 50666.666667) < 0.01


def test_compute_metrics_excess_sell_strict_mode():
    """Test that excess sell quantity raises error in strict mode."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="sell",
            qty=2.0,  # Selling more than bought
            fill_price=51000.0
        ),
    ]

    with pytest.raises(ValueError, match="Sell quantity exceeds available lots"):
        compute_metrics(fills, strict=True)


def test_compute_metrics_excess_sell_best_effort():
    """Test that excess sell is handled gracefully in best-effort mode."""
    fills = [
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=50000.0
        ),
        Fill(
            ts=datetime(2025, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="sell",
            qty=2.0,  # Selling more than bought
            fill_price=51000.0
        ),
    ]

    # Should not raise in best-effort mode
    metrics = compute_metrics(fills, strict=False)

    # PnL from matched 1.0: (51000-50000)*1 = 1000
    # Excess 1.0 treated as short with PnL=0
    assert metrics["realized_pnl_total"] == 1000.0


def test_fill_validation():
    """Test Fill dataclass validation."""
    # Valid fill
    fill = Fill(
        ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        symbol="BTC/USD",
        side="buy",
        qty=1.0,
        fill_price=50000.0
    )
    assert fill.side == "buy"

    # Invalid side
    with pytest.raises(ValueError, match="Invalid side"):
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="invalid",
            qty=1.0,
            fill_price=50000.0
        )

    # Invalid quantity
    with pytest.raises(ValueError, match="Quantity must be positive"):
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=-1.0,
            fill_price=50000.0
        )

    # Invalid price
    with pytest.raises(ValueError, match="Fill price must be positive"):
        Fill(
            ts=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            symbol="BTC/USD",
            side="buy",
            qty=1.0,
            fill_price=-100.0
        )
