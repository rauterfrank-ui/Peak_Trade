# tests/test_live_portfolio_monitor.py
"""
Tests für Live Portfolio Monitoring (Phase 48)
===============================================

Tests für:
- LivePositionSnapshot
- LivePortfolioSnapshot
- LivePortfolioMonitor
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.live.broker_base import BaseBrokerClient, PaperBroker
from src.live.portfolio_monitor import (
    LivePortfolioMonitor,
    LivePortfolioSnapshot,
    LivePositionSnapshot,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_position_1() -> LivePositionSnapshot:
    """Erstellt Sample-Position 1."""
    return LivePositionSnapshot(
        symbol="BTC/EUR",
        side="long",
        size=0.5,
        entry_price=28000.0,
        mark_price=29500.0,
        unrealized_pnl=750.0,
        realized_pnl=120.0,
    )


@pytest.fixture
def sample_position_2() -> LivePositionSnapshot:
    """Erstellt Sample-Position 2."""
    return LivePositionSnapshot(
        symbol="ETH/EUR",
        side="short",
        size=2.0,
        entry_price=1800.0,
        mark_price=1750.0,
        unrealized_pnl=100.0,
        realized_pnl=0.0,
    )


@pytest.fixture
def fake_exchange_client() -> Mock:
    """Erstellt einen Fake-Exchange-Client."""
    client = Mock(spec=BaseBrokerClient)
    client.fetch_positions.return_value = []
    return client


# =============================================================================
# DATACLASS TESTS
# =============================================================================


def test_live_position_snapshot_creation(sample_position_1: LivePositionSnapshot):
    """Testet Erstellung einer LivePositionSnapshot."""
    assert sample_position_1.symbol == "BTC/EUR"
    assert sample_position_1.side == "long"
    assert sample_position_1.size == 0.5
    assert sample_position_1.entry_price == 28000.0
    assert sample_position_1.mark_price == 29500.0
    assert sample_position_1.notional == pytest.approx(0.5 * 29500.0, abs=0.01)


def test_live_position_snapshot_notional_calculation():
    """Testet automatische Notional-Berechnung."""
    pos = LivePositionSnapshot(
        symbol="BTC/EUR",
        side="long",
        size=0.5,
        mark_price=30000.0,
    )
    assert pos.notional == pytest.approx(0.5 * 30000.0, abs=0.01)


def test_live_portfolio_snapshot_aggregation(
    sample_position_1: LivePositionSnapshot,
    sample_position_2: LivePositionSnapshot,
):
    """Testet Aggregation von Positionen in Portfolio-Snapshot."""
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[sample_position_1, sample_position_2],
    )

    # Prüfe Aggregat-Werte
    assert snapshot.num_open_positions == 2
    assert snapshot.total_notional == pytest.approx(
        sample_position_1.notional + sample_position_2.notional, abs=0.01
    )
    assert snapshot.total_unrealized_pnl == pytest.approx(850.0, abs=0.01)  # 750 + 100
    assert snapshot.total_realized_pnl == pytest.approx(120.0, abs=0.01)

    # Prüfe Symbol-Notional
    assert "BTC/EUR" in snapshot.symbol_notional
    assert "ETH/EUR" in snapshot.symbol_notional
    assert snapshot.symbol_notional["BTC/EUR"] == pytest.approx(sample_position_1.notional, abs=0.01)
    assert snapshot.symbol_notional["ETH/EUR"] == pytest.approx(sample_position_2.notional, abs=0.01)


def test_live_portfolio_snapshot_empty():
    """Testet leeres Portfolio."""
    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[],
    )

    assert snapshot.num_open_positions == 0
    assert snapshot.total_notional == 0.0
    assert snapshot.total_unrealized_pnl == 0.0
    assert snapshot.total_realized_pnl == 0.0
    assert len(snapshot.symbol_notional) == 0


def test_live_portfolio_snapshot_flat_positions_ignored():
    """Testet dass flache Positionen ignoriert werden."""
    flat_pos = LivePositionSnapshot(
        symbol="LTC/EUR",
        side="flat",
        size=0.0,
        mark_price=100.0,
    )

    snapshot = LivePortfolioSnapshot(
        as_of=datetime.utcnow(),
        positions=[flat_pos],
    )

    assert snapshot.num_open_positions == 0
    assert snapshot.total_notional == 0.0


# =============================================================================
# MONITOR TESTS
# =============================================================================


def test_live_portfolio_monitor_with_fake_client(fake_exchange_client: Mock):
    """Testet LivePortfolioMonitor mit Fake-Client."""
    monitor = LivePortfolioMonitor(fake_exchange_client)

    snapshot = monitor.snapshot()

    assert isinstance(snapshot, LivePortfolioSnapshot)
    assert snapshot.num_open_positions == 0
    assert len(snapshot.positions) == 0


def test_live_portfolio_monitor_with_paper_broker():
    """Testet LivePortfolioMonitor mit PaperBroker."""
    broker = PaperBroker(starting_cash=10000.0, base_currency="EUR", log_to_console=False)

    # Füge einige Positionen hinzu (simuliert durch direkte Manipulation)
    broker.positions["BTC/EUR"] = {
        "qty": 0.5,
        "avg_price": 28000.0,
        "realized_pnl": 120.0,
        "last_price": 29500.0,
    }
    broker.positions["ETH/EUR"] = {
        "qty": -2.0,  # Short
        "avg_price": 1800.0,
        "realized_pnl": 0.0,
        "last_price": 1750.0,
    }

    monitor = LivePortfolioMonitor(broker)
    snapshot = monitor.snapshot()

    assert snapshot.num_open_positions == 2
    assert len(snapshot.positions) == 2

    # Prüfe erste Position
    btc_pos = next((p for p in snapshot.positions if p.symbol == "BTC/EUR"), None)
    assert btc_pos is not None
    assert btc_pos.side == "long"
    assert btc_pos.size == pytest.approx(0.5, abs=0.001)
    assert btc_pos.entry_price == pytest.approx(28000.0, abs=0.01)
    assert btc_pos.mark_price == pytest.approx(29500.0, abs=0.01)
    assert btc_pos.notional == pytest.approx(0.5 * 29500.0, abs=0.01)

    # Prüfe zweite Position
    eth_pos = next((p for p in snapshot.positions if p.symbol == "ETH/EUR"), None)
    assert eth_pos is not None
    assert eth_pos.side == "short"
    assert eth_pos.size == pytest.approx(2.0, abs=0.001)

    # Prüfe Cash
    assert snapshot.cash == pytest.approx(10000.0, abs=0.01)


def test_live_portfolio_monitor_with_dataframe_positions(fake_exchange_client: Mock):
    """Testet LivePortfolioMonitor mit DataFrame-Positionen."""
    import pandas as pd

    df = pd.DataFrame([
        {
            "symbol": "BTC/EUR",
            "side": "long",
            "size": 0.5,
            "entry_price": 28000.0,
            "mark_price": 29500.0,
            "unrealized_pnl": 750.0,
        },
        {
            "symbol": "ETH/EUR",
            "side": "short",
            "size": 2.0,
            "entry_price": 1800.0,
            "mark_price": 1750.0,
            "unrealized_pnl": 100.0,
        },
    ])

    fake_exchange_client.fetch_positions.return_value = df

    monitor = LivePortfolioMonitor(fake_exchange_client)
    snapshot = monitor.snapshot()

    assert snapshot.num_open_positions == 2
    assert len(snapshot.positions) == 2


def test_live_portfolio_monitor_parse_position_variants():
    """Testet Parsing verschiedener Position-Formate."""
    monitor = LivePortfolioMonitor(Mock(spec=BaseBrokerClient))

    # Variante 1: Standard-Format
    pos1 = monitor._parse_position({
        "symbol": "BTC/EUR",
        "side": "long",
        "size": 0.5,
        "entry_price": 28000.0,
        "mark_price": 29500.0,
    })
    assert pos1 is not None
    assert pos1.symbol == "BTC/EUR"
    assert pos1.side == "long"

    # Variante 2: PaperBroker-Format (qty statt size)
    pos2 = monitor._parse_position({
        "symbol": "ETH/EUR",
        "qty": 2.0,
        "avg_price": 1800.0,
        "last_price": 1750.0,
    })
    assert pos2 is not None
    assert pos2.symbol == "ETH/EUR"
    assert pos2.size == pytest.approx(2.0, abs=0.001)

    # Variante 3: Side aus size ableiten
    pos3 = monitor._parse_position({
        "symbol": "LTC/EUR",
        "size": -1.0,  # Negative size = short
    })
    assert pos3 is not None
    assert pos3.side == "short"

    # Variante 4: Ungültige Position (kein Symbol)
    pos4 = monitor._parse_position({})
    assert pos4 is None







