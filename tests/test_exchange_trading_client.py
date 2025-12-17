# tests/test_exchange_trading_client.py
"""
Peak_Trade: Tests für TradingExchangeClient & DummyExchangeClient (Phase 38)
============================================================================

Diese Tests prüfen:
1. TradingExchangeClient Protocol-Konformität
2. DummyExchangeClient Funktionalität
3. Order-Lifecycle (place -> status -> cancel)
4. Edge-Cases und Fehlerbehandlung

WICHTIG: Alle Tests sind Offline-Tests ohne Netzwerkzugriff!
"""
from __future__ import annotations

import pytest

from src.exchange.base import (
    ExchangeOrderResult,
    ExchangeOrderStatus,
    TradingExchangeClient,
)
from src.exchange.dummy_client import DummyExchangeClient

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def dummy_client() -> DummyExchangeClient:
    """Erstellt einen DummyExchangeClient mit Standard-Preisen."""
    return DummyExchangeClient(
        simulated_prices={
            "BTC/EUR": 50000.0,
            "ETH/EUR": 3000.0,
            "BTC/USD": 55000.0,
        },
        fee_bps=10.0,
        slippage_bps=5.0,
    )


@pytest.fixture
def empty_client() -> DummyExchangeClient:
    """Erstellt einen DummyExchangeClient ohne Preise."""
    return DummyExchangeClient(
        simulated_prices={},
        fee_bps=10.0,
        slippage_bps=0.0,
    )


# =============================================================================
# Protocol Conformance Tests
# =============================================================================


class TestProtocolConformance:
    """Tests für TradingExchangeClient Protocol-Konformität."""

    def test_dummy_client_implements_protocol(self, dummy_client: DummyExchangeClient) -> None:
        """Test: DummyExchangeClient implementiert TradingExchangeClient Protocol."""
        assert isinstance(dummy_client, TradingExchangeClient)

    def test_protocol_has_required_methods(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Alle Protocol-Methoden sind vorhanden."""
        assert hasattr(dummy_client, "get_name")
        assert hasattr(dummy_client, "place_order")
        assert hasattr(dummy_client, "cancel_order")
        assert hasattr(dummy_client, "get_order_status")

        assert callable(dummy_client.get_name)
        assert callable(dummy_client.place_order)
        assert callable(dummy_client.cancel_order)
        assert callable(dummy_client.get_order_status)


# =============================================================================
# DummyExchangeClient Basic Tests
# =============================================================================


class TestDummyClientBasics:
    """Basis-Tests für DummyExchangeClient."""

    def test_get_name(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_name gibt 'dummy' zurück."""
        assert dummy_client.get_name() == "dummy"

    def test_repr(self, dummy_client: DummyExchangeClient) -> None:
        """Test: __repr__ gibt sinnvollen String zurück."""
        repr_str = repr(dummy_client)
        assert "DummyExchangeClient" in repr_str
        assert "prices=3" in repr_str
        assert "fee_bps=10.0" in repr_str

    def test_initial_state(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Client startet mit leerem Order-Buch."""
        assert dummy_client.get_order_count() == 0
        assert dummy_client.get_all_orders() == []
        assert dummy_client.get_open_orders() == []
        assert dummy_client.get_filled_orders() == []

    def test_get_all_prices(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_all_prices gibt alle konfigurierten Preise zurück."""
        prices = dummy_client.get_all_prices()
        assert prices["BTC/EUR"] == 50000.0
        assert prices["ETH/EUR"] == 3000.0
        assert prices["BTC/USD"] == 55000.0

    def test_set_price(self, dummy_client: DummyExchangeClient) -> None:
        """Test: set_price aktualisiert Preis korrekt."""
        dummy_client.set_price("BTC/EUR", 60000.0)
        assert dummy_client.get_price("BTC/EUR") == 60000.0

    def test_set_price_invalid(self, dummy_client: DummyExchangeClient) -> None:
        """Test: set_price wirft ValueError bei ungültigem Preis."""
        with pytest.raises(ValueError, match="muss > 0 sein"):
            dummy_client.set_price("BTC/EUR", 0)
        with pytest.raises(ValueError, match="muss > 0 sein"):
            dummy_client.set_price("BTC/EUR", -100)


# =============================================================================
# Order Placement Tests
# =============================================================================


class TestOrderPlacement:
    """Tests für Order-Platzierung."""

    def test_place_market_order_buy(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Market-Buy-Order wird sofort gefüllt."""
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="market",
        )

        assert order_id.startswith("DUMMY-")
        assert dummy_client.get_order_count() == 1

        # Status prüfen
        status = dummy_client.get_order_status(order_id)
        assert status.status == ExchangeOrderStatus.FILLED
        assert status.filled_qty == 0.1
        assert status.avg_price is not None
        assert status.avg_price > 50000.0  # Mit Slippage
        assert status.fee is not None
        assert status.fee > 0

    def test_place_market_order_sell(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Market-Sell-Order wird sofort gefüllt."""
        order_id = dummy_client.place_order(
            symbol="ETH/EUR",
            side="sell",
            quantity=1.0,
            order_type="market",
        )

        status = dummy_client.get_order_status(order_id)
        assert status.status == ExchangeOrderStatus.FILLED
        assert status.filled_qty == 1.0
        assert status.avg_price is not None
        assert status.avg_price < 3000.0  # Mit Slippage (Sell = niedrigerer Preis)

    def test_place_limit_order(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Limit-Order bleibt offen."""
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.5,
            order_type="limit",
            limit_price=48000.0,
        )

        status = dummy_client.get_order_status(order_id)
        assert status.status == ExchangeOrderStatus.OPEN
        assert status.filled_qty == 0.0
        assert status.avg_price is None

    def test_place_order_with_client_id(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Client-Order-ID wird korrekt gespeichert."""
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
            client_order_id="my-custom-id-123",
        )

        status = dummy_client.get_order_status(order_id)
        assert status.raw is not None
        assert status.raw.get("client_order_id") == "my-custom-id-123"

    def test_place_order_no_price_rejection(self, empty_client: DummyExchangeClient) -> None:
        """Test: Order ohne verfügbaren Preis wird rejected."""
        order_id = empty_client.place_order(
            symbol="UNKNOWN/PAIR",
            side="buy",
            quantity=1.0,
            order_type="market",
        )

        status = empty_client.get_order_status(order_id)
        assert status.status == ExchangeOrderStatus.REJECTED

    def test_place_order_invalid_quantity(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Ungültige Quantity wirft ValueError."""
        with pytest.raises(ValueError, match="quantity muss > 0"):
            dummy_client.place_order("BTC/EUR", "buy", 0, "market")
        with pytest.raises(ValueError, match="quantity muss > 0"):
            dummy_client.place_order("BTC/EUR", "buy", -1, "market")

    def test_place_limit_order_no_price(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Limit-Order ohne Preis wirft ValueError."""
        with pytest.raises(ValueError, match="limit_price erforderlich"):
            dummy_client.place_order("BTC/EUR", "buy", 0.1, "limit")

    def test_place_limit_order_invalid_price(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Limit-Order mit ungültigem Preis wirft ValueError."""
        with pytest.raises(ValueError, match="limit_price muss > 0"):
            dummy_client.place_order("BTC/EUR", "buy", 0.1, "limit", limit_price=0)
        with pytest.raises(ValueError, match="limit_price muss > 0"):
            dummy_client.place_order("BTC/EUR", "buy", 0.1, "limit", limit_price=-100)


# =============================================================================
# Order Cancellation Tests
# =============================================================================


class TestOrderCancellation:
    """Tests für Order-Stornierung."""

    def test_cancel_open_order(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Offene Limit-Order kann storniert werden."""
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="limit",
            limit_price=40000.0,
        )

        # Vorher: OPEN
        assert dummy_client.get_order_status(order_id).status == ExchangeOrderStatus.OPEN

        # Stornieren
        result = dummy_client.cancel_order(order_id)
        assert result is True

        # Nachher: CANCELLED
        assert dummy_client.get_order_status(order_id).status == ExchangeOrderStatus.CANCELLED

    def test_cancel_filled_order_fails(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Gefüllte Order kann nicht storniert werden."""
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="market",
        )

        # Vorher: FILLED
        assert dummy_client.get_order_status(order_id).status == ExchangeOrderStatus.FILLED

        # Stornieren sollte fehlschlagen
        result = dummy_client.cancel_order(order_id)
        assert result is False

        # Status unverändert
        assert dummy_client.get_order_status(order_id).status == ExchangeOrderStatus.FILLED

    def test_cancel_unknown_order(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Unbekannte Order-ID gibt False zurück."""
        result = dummy_client.cancel_order("UNKNOWN-ORDER-ID")
        assert result is False


# =============================================================================
# Order Status Tests
# =============================================================================


class TestOrderStatus:
    """Tests für Order-Status-Abfragen."""

    def test_get_order_status_returns_result(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_order_status gibt ExchangeOrderResult zurück."""
        order_id = dummy_client.place_order("BTC/EUR", "buy", 0.1, "market")

        status = dummy_client.get_order_status(order_id)

        assert isinstance(status, ExchangeOrderResult)
        assert status.exchange_order_id == order_id

    def test_get_order_status_unknown_raises(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Unbekannte Order-ID wirft ValueError."""
        with pytest.raises(ValueError, match="Order nicht gefunden"):
            dummy_client.get_order_status("UNKNOWN-ORDER-ID")

    def test_order_status_raw_data(self, dummy_client: DummyExchangeClient) -> None:
        """Test: raw-Feld enthält erweiterte Order-Informationen."""
        order_id = dummy_client.place_order(
            symbol="ETH/EUR",
            side="sell",
            quantity=2.0,
            order_type="market",
        )

        status = dummy_client.get_order_status(order_id)
        assert status.raw is not None
        assert status.raw["symbol"] == "ETH/EUR"
        assert status.raw["side"] == "sell"
        assert status.raw["quantity"] == 2.0
        assert status.raw["order_type"] == "market"
        assert "created_at" in status.raw
        assert "updated_at" in status.raw


# =============================================================================
# Slippage & Fee Tests
# =============================================================================


class TestSlippageAndFees:
    """Tests für Slippage- und Fee-Berechnung."""

    def test_buy_slippage_increases_price(self) -> None:
        """Test: Bei Buy-Orders erhöht Slippage den Fill-Preis."""
        client = DummyExchangeClient(
            simulated_prices={"BTC/EUR": 50000.0},
            fee_bps=0.0,
            slippage_bps=100.0,  # 1%
        )

        order_id = client.place_order("BTC/EUR", "buy", 0.1, "market")
        status = client.get_order_status(order_id)

        # 1% Slippage auf 50000 = 50500
        assert status.avg_price == pytest.approx(50500.0, rel=0.001)

    def test_sell_slippage_decreases_price(self) -> None:
        """Test: Bei Sell-Orders reduziert Slippage den Fill-Preis."""
        client = DummyExchangeClient(
            simulated_prices={"BTC/EUR": 50000.0},
            fee_bps=0.0,
            slippage_bps=100.0,  # 1%
        )

        order_id = client.place_order("BTC/EUR", "sell", 0.1, "market")
        status = client.get_order_status(order_id)

        # 1% Slippage auf 50000 = 49500
        assert status.avg_price == pytest.approx(49500.0, rel=0.001)

    def test_fee_calculation(self) -> None:
        """Test: Fee wird korrekt berechnet."""
        client = DummyExchangeClient(
            simulated_prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,  # 0.1%
            slippage_bps=0.0,
        )

        order_id = client.place_order("BTC/EUR", "buy", 0.1, "market")
        status = client.get_order_status(order_id)

        # Notional = 0.1 * 50000 = 5000, Fee = 5000 * 0.001 = 5.0
        assert status.fee == pytest.approx(5.0, rel=0.001)

    def test_zero_fee(self) -> None:
        """Test: Bei fee_bps=0 ist fee None."""
        client = DummyExchangeClient(
            simulated_prices={"BTC/EUR": 50000.0},
            fee_bps=0.0,
            slippage_bps=0.0,
        )

        order_id = client.place_order("BTC/EUR", "buy", 0.1, "market")
        status = client.get_order_status(order_id)

        assert status.fee is None


# =============================================================================
# Query Methods Tests
# =============================================================================


class TestQueryMethods:
    """Tests für Query-Methoden."""

    def test_get_open_orders(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_open_orders gibt nur offene Orders zurück."""
        # Market-Order (wird gefüllt)
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "market")

        # Limit-Orders (bleiben offen)
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "limit", limit_price=40000)
        dummy_client.place_order("ETH/EUR", "sell", 1.0, "limit", limit_price=4000)

        open_orders = dummy_client.get_open_orders()
        assert len(open_orders) == 2
        assert all(o.status == ExchangeOrderStatus.OPEN for o in open_orders)

    def test_get_filled_orders(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_filled_orders gibt nur gefüllte Orders zurück."""
        # Market-Orders (werden gefüllt)
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "market")
        dummy_client.place_order("ETH/EUR", "sell", 1.0, "market")

        # Limit-Order (bleibt offen)
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "limit", limit_price=40000)

        filled_orders = dummy_client.get_filled_orders()
        assert len(filled_orders) == 2
        assert all(o.status == ExchangeOrderStatus.FILLED for o in filled_orders)

    def test_get_all_orders(self, dummy_client: DummyExchangeClient) -> None:
        """Test: get_all_orders gibt alle Orders zurück."""
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "market")
        dummy_client.place_order("ETH/EUR", "sell", 1.0, "limit", limit_price=4000)

        all_orders = dummy_client.get_all_orders()
        assert len(all_orders) == 2


# =============================================================================
# Reset Tests
# =============================================================================


class TestReset:
    """Tests für Reset-Funktionalität."""

    def test_reset_clears_orders(self, dummy_client: DummyExchangeClient) -> None:
        """Test: reset() löscht alle Orders."""
        dummy_client.place_order("BTC/EUR", "buy", 0.1, "market")
        dummy_client.place_order("ETH/EUR", "sell", 1.0, "market")

        assert dummy_client.get_order_count() == 2

        dummy_client.reset()

        assert dummy_client.get_order_count() == 0
        assert dummy_client.get_all_orders() == []

    def test_reset_keeps_prices(self, dummy_client: DummyExchangeClient) -> None:
        """Test: reset() behält Preise bei."""
        dummy_client.reset()

        # Preise sollten noch da sein
        assert dummy_client.get_price("BTC/EUR") == 50000.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration-Tests für komplette Workflows."""

    def test_full_order_lifecycle(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Kompletter Order-Lifecycle (place -> check -> cancel)."""
        # 1. Order platzieren
        order_id = dummy_client.place_order(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.05,
            order_type="limit",
            limit_price=45000.0,
            client_order_id="lifecycle-test-001",
        )

        # 2. Status prüfen - OPEN
        status1 = dummy_client.get_order_status(order_id)
        assert status1.status == ExchangeOrderStatus.OPEN
        assert status1.filled_qty == 0.0

        # 3. Order stornieren
        cancelled = dummy_client.cancel_order(order_id)
        assert cancelled is True

        # 4. Status prüfen - CANCELLED
        status2 = dummy_client.get_order_status(order_id)
        assert status2.status == ExchangeOrderStatus.CANCELLED

    def test_multiple_orders_different_symbols(self, dummy_client: DummyExchangeClient) -> None:
        """Test: Mehrere Orders auf verschiedenen Symbolen."""
        orders = [
            ("BTC/EUR", "buy", 0.1),
            ("ETH/EUR", "sell", 2.0),
            ("BTC/USD", "buy", 0.05),
        ]

        order_ids = []
        for symbol, side, qty in orders:
            order_id = dummy_client.place_order(symbol, side, qty, "market")
            order_ids.append(order_id)

        # Alle sollten gefüllt sein
        for order_id in order_ids:
            status = dummy_client.get_order_status(order_id)
            assert status.status == ExchangeOrderStatus.FILLED

        assert dummy_client.get_order_count() == 3
        assert len(dummy_client.get_filled_orders()) == 3




