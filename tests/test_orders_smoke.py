#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_orders_smoke.py
"""
Peak_Trade: Smoke-Tests fuer Order-Layer (src/orders)
=====================================================

Testet:
- OrderRequest/OrderFill/OrderExecutionResult Dataclasses
- PaperOrderExecutor (filled/rejected)
- Mapping-Helpers (from_live_order_request, from_orders_csv_row)
- Integration: Orders -> Executor -> Results
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =============================================================================
# 1. Dataclass Tests
# =============================================================================

class TestOrderRequest:
    """Tests fuer OrderRequest Dataclass."""

    def test_basic_instantiation(self):
        """OrderRequest kann mit Pflichtfeldern instanziiert werden."""
        from src.orders import OrderRequest

        req = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
        )
        assert req.symbol == "BTC/EUR"
        assert req.side == "buy"
        assert req.quantity == 0.1
        assert req.order_type == "market"
        assert req.limit_price is None
        assert req.client_id is None
        assert req.metadata == {}

    def test_with_all_fields(self):
        """OrderRequest kann mit allen Feldern instanziiert werden."""
        from src.orders import OrderRequest

        req = OrderRequest(
            symbol="ETH/EUR",
            side="sell",
            quantity=1.5,
            order_type="limit",
            limit_price=3000.0,
            client_id="test-123",
            metadata={"strategy_key": "ma_crossover"},
        )
        assert req.symbol == "ETH/EUR"
        assert req.side == "sell"
        assert req.quantity == 1.5
        assert req.order_type == "limit"
        assert req.limit_price == 3000.0
        assert req.client_id == "test-123"
        assert req.metadata["strategy_key"] == "ma_crossover"

    def test_validation_quantity_positive(self):
        """OrderRequest validiert positive quantity."""
        from src.orders import OrderRequest

        with pytest.raises(ValueError, match="quantity muss > 0"):
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0)

        with pytest.raises(ValueError, match="quantity muss > 0"):
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=-1)

    def test_validation_limit_price_required(self):
        """OrderRequest validiert dass limit_price bei limit-Orders vorhanden ist."""
        from src.orders import OrderRequest

        with pytest.raises(ValueError, match="limit_price ist erforderlich"):
            OrderRequest(
                symbol="BTC/EUR",
                side="buy",
                quantity=0.1,
                order_type="limit",
            )

    def test_validation_limit_price_positive(self):
        """OrderRequest validiert positive limit_price."""
        from src.orders import OrderRequest

        with pytest.raises(ValueError, match="limit_price muss > 0"):
            OrderRequest(
                symbol="BTC/EUR",
                side="buy",
                quantity=0.1,
                order_type="limit",
                limit_price=0,
            )


class TestOrderFill:
    """Tests fuer OrderFill Dataclass."""

    def test_basic_instantiation(self):
        """OrderFill kann instanziiert werden."""
        from src.orders import OrderFill

        now = datetime.now(timezone.utc)
        fill = OrderFill(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            price=50000.0,
            timestamp=now,
        )
        assert fill.symbol == "BTC/EUR"
        assert fill.side == "buy"
        assert fill.quantity == 0.1
        assert fill.price == 50000.0
        assert fill.timestamp == now
        assert fill.fee is None
        assert fill.fee_currency is None

    def test_with_fee(self):
        """OrderFill kann mit Fee instanziiert werden."""
        from src.orders import OrderFill

        now = datetime.now(timezone.utc)
        fill = OrderFill(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            price=50000.0,
            timestamp=now,
            fee=5.0,
            fee_currency="EUR",
        )
        assert fill.fee == 5.0
        assert fill.fee_currency == "EUR"


class TestOrderExecutionResult:
    """Tests fuer OrderExecutionResult Dataclass."""

    def test_filled_result(self):
        """OrderExecutionResult fuer erfolgreiche Order."""
        from src.orders import OrderRequest, OrderFill, OrderExecutionResult

        now = datetime.now(timezone.utc)
        req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        fill = OrderFill(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            price=50000.0,
            timestamp=now,
        )
        result = OrderExecutionResult(
            status="filled",
            request=req,
            fill=fill,
        )
        assert result.status == "filled"
        assert result.is_filled
        assert not result.is_rejected
        assert result.fill is not None
        assert result.reason is None

    def test_rejected_result(self):
        """OrderExecutionResult fuer abgelehnte Order."""
        from src.orders import OrderRequest, OrderExecutionResult

        req = OrderRequest(symbol="UNKNOWN/EUR", side="buy", quantity=0.1)
        result = OrderExecutionResult(
            status="rejected",
            request=req,
            fill=None,
            reason="no_price_for_symbol",
        )
        assert result.status == "rejected"
        assert result.is_rejected
        assert not result.is_filled
        assert result.fill is None
        assert result.reason == "no_price_for_symbol"


# =============================================================================
# 2. PaperOrderExecutor Tests
# =============================================================================

class TestPaperMarketContext:
    """Tests fuer PaperMarketContext."""

    def test_basic_instantiation(self):
        """PaperMarketContext kann instanziiert werden."""
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext()
        assert ctx.prices == {}
        assert ctx.fee_bps == 0.0
        assert ctx.slippage_bps == 0.0
        assert ctx.base_currency == "EUR"

    def test_with_prices(self):
        """PaperMarketContext kann mit Preisen instanziiert werden."""
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            fee_bps=10.0,
            slippage_bps=5.0,
        )
        assert ctx.get_price("BTC/EUR") == 50000.0
        assert ctx.get_price("ETH/EUR") == 3000.0
        assert ctx.get_price("UNKNOWN") is None

    def test_set_price(self):
        """PaperMarketContext.set_price funktioniert."""
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext()
        ctx.set_price("BTC/EUR", 50000.0)
        assert ctx.get_price("BTC/EUR") == 50000.0

    def test_set_price_validation(self):
        """PaperMarketContext.set_price validiert positive Preise."""
        from src.orders import PaperMarketContext

        ctx = PaperMarketContext()
        with pytest.raises(ValueError, match="Preis muss > 0"):
            ctx.set_price("BTC/EUR", 0)


class TestPaperOrderExecutor:
    """Tests fuer PaperOrderExecutor."""

    def test_market_order_filled(self):
        """Market-Order wird gefillt wenn Preis vorhanden."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0})
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        result = executor.execute_order(req)

        assert result.is_filled
        assert result.fill is not None
        assert result.fill.symbol == "BTC/EUR"
        assert result.fill.quantity == 0.1
        assert result.fill.price == 50000.0

    def test_market_order_rejected_no_price(self):
        """Market-Order wird rejected wenn kein Preis vorhanden."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={})  # Kein Preis fuer BTC/EUR
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        result = executor.execute_order(req)

        assert result.is_rejected
        assert result.fill is None
        assert "no_price_for_symbol" in result.reason

    def test_slippage_buy(self):
        """Slippage erhoeht den Preis bei Kauf."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            slippage_bps=10.0,  # 0.1%
        )
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        result = executor.execute_order(req)

        assert result.is_filled
        expected_price = 50000.0 * (1 + 10.0 / 10000.0)  # 50005.0
        assert result.fill.price == pytest.approx(expected_price, rel=1e-6)

    def test_slippage_sell(self):
        """Slippage reduziert den Preis bei Verkauf."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            slippage_bps=10.0,  # 0.1%
        )
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(symbol="BTC/EUR", side="sell", quantity=0.1)
        result = executor.execute_order(req)

        assert result.is_filled
        expected_price = 50000.0 * (1 - 10.0 / 10000.0)  # 49995.0
        assert result.fill.price == pytest.approx(expected_price, rel=1e-6)

    def test_fee_calculation(self):
        """Fees werden korrekt berechnet."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0},
            fee_bps=10.0,  # 0.1%
        )
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1)
        result = executor.execute_order(req)

        assert result.is_filled
        # Notional = 0.1 * 50000 = 5000
        # Fee = 5000 * 10/10000 = 5
        assert result.fill.fee == pytest.approx(5.0, rel=1e-6)

    def test_limit_order_filled_buy(self):
        """Limit-Buy-Order wird gefillt wenn Marktpreis <= Limit."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={"BTC/EUR": 49000.0})
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="limit",
            limit_price=50000.0,  # Limit hoeher als Markt
        )
        result = executor.execute_order(req)

        assert result.is_filled
        assert result.fill.price == 49000.0  # Zum besseren Preis

    def test_limit_order_rejected_buy(self):
        """Limit-Buy-Order wird rejected wenn Marktpreis > Limit."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={"BTC/EUR": 51000.0})
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="limit",
            limit_price=50000.0,  # Limit niedriger als Markt
        )
        result = executor.execute_order(req)

        assert result.is_rejected
        assert "limit_not_met" in result.reason

    def test_limit_order_filled_sell(self):
        """Limit-Sell-Order wird gefillt wenn Marktpreis >= Limit."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={"BTC/EUR": 51000.0})
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.1,
            order_type="limit",
            limit_price=50000.0,  # Limit niedriger als Markt
        )
        result = executor.execute_order(req)

        assert result.is_filled
        assert result.fill.price == 51000.0  # Zum besseren Preis

    def test_limit_order_rejected_sell(self):
        """Limit-Sell-Order wird rejected wenn Marktpreis < Limit."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(prices={"BTC/EUR": 49000.0})
        executor = PaperOrderExecutor(ctx)

        req = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.1,
            order_type="limit",
            limit_price=50000.0,  # Limit hoeher als Markt
        )
        result = executor.execute_order(req)

        assert result.is_rejected
        assert "limit_not_met" in result.reason

    def test_execute_orders_batch(self):
        """execute_orders verarbeitet mehrere Orders."""
        from src.orders import PaperMarketContext, PaperOrderExecutor, OrderRequest

        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0}
        )
        executor = PaperOrderExecutor(ctx)

        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1),
            OrderRequest(symbol="ETH/EUR", side="sell", quantity=1.0),
            OrderRequest(symbol="UNKNOWN", side="buy", quantity=1.0),
        ]
        results = executor.execute_orders(orders)

        assert len(results) == 3
        assert results[0].is_filled
        assert results[1].is_filled
        assert results[2].is_rejected


# =============================================================================
# 3. Mapper Tests
# =============================================================================

class TestFromLiveOrderRequest:
    """Tests fuer from_live_order_request Mapper."""

    def test_basic_mapping(self):
        """Einfaches Mapping von LiveOrderRequest."""
        from src.orders import from_live_order_request
        from src.live.orders import LiveOrderRequest

        live_req = LiveOrderRequest(
            client_order_id="test-123",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=0.1,
            notional=5000.0,
            strategy_key="ma_crossover",
            extra={"current_price": 50000.0},
        )

        order_req = from_live_order_request(live_req)

        assert order_req.symbol == "BTC/EUR"
        assert order_req.side == "buy"  # Normalized
        assert order_req.quantity == 0.1
        assert order_req.order_type == "market"  # Normalized
        assert order_req.client_id == "test-123"
        assert order_req.metadata["strategy_key"] == "ma_crossover"

    def test_quantity_from_notional(self):
        """Quantity wird aus Notional berechnet wenn nicht vorhanden."""
        from src.orders import from_live_order_request
        from src.live.orders import LiveOrderRequest

        live_req = LiveOrderRequest(
            client_order_id="test-123",
            symbol="BTC/EUR",
            side="BUY",
            quantity=None,
            notional=5000.0,
            extra={"current_price": 50000.0},
        )

        order_req = from_live_order_request(live_req)

        # quantity = 5000 / 50000 = 0.1
        assert order_req.quantity == pytest.approx(0.1, rel=1e-6)


class TestFromOrdersCsvRow:
    """Tests fuer from_orders_csv_row Mapper."""

    def test_basic_mapping(self):
        """Einfaches Mapping von CSV-Row."""
        from src.orders import from_orders_csv_row
        import json

        row = {
            "client_order_id": "test-456",
            "symbol": "ETH/EUR",
            "side": "SELL",
            "order_type": "MARKET",
            "quantity": 1.5,
            "notional": 4500.0,
            "strategy_key": "rsi_reversion",
            "extra_json": json.dumps({"current_price": 3000.0}),
        }

        order_req = from_orders_csv_row(row)

        assert order_req.symbol == "ETH/EUR"
        assert order_req.side == "sell"  # Normalized
        assert order_req.quantity == 1.5
        assert order_req.client_id == "test-456"

    def test_quantity_from_notional_csv(self):
        """Quantity wird aus Notional berechnet wenn nicht vorhanden (CSV)."""
        from src.orders import from_orders_csv_row
        import json
        import math

        row = {
            "client_order_id": "test-789",
            "symbol": "BTC/EUR",
            "side": "BUY",
            "order_type": "MARKET",
            "quantity": float("nan"),  # NaN wie in pandas
            "notional": 5000.0,
            "extra_json": json.dumps({"current_price": 50000.0}),
        }

        order_req = from_orders_csv_row(row)

        assert order_req.quantity == pytest.approx(0.1, rel=1e-6)


class TestToOrderRequests:
    """Tests fuer to_order_requests Helper."""

    def test_batch_conversion(self):
        """Batch-Konvertierung von LiveOrderRequests."""
        from src.orders import to_order_requests
        from src.live.orders import LiveOrderRequest

        live_orders = [
            LiveOrderRequest(
                client_order_id="order-1",
                symbol="BTC/EUR",
                side="BUY",
                quantity=0.1,
                extra={"current_price": 50000.0},
            ),
            LiveOrderRequest(
                client_order_id="order-2",
                symbol="ETH/EUR",
                side="SELL",
                quantity=1.0,
                extra={"current_price": 3000.0},
            ),
        ]

        order_requests = to_order_requests(live_orders)

        assert len(order_requests) == 2
        assert order_requests[0].symbol == "BTC/EUR"
        assert order_requests[1].symbol == "ETH/EUR"


# =============================================================================
# 4. Integration Tests
# =============================================================================

class TestIntegration:
    """Integration-Tests fuer den gesamten Order-Layer."""

    def test_live_order_to_execution(self):
        """Vollstaendiger Flow: LiveOrderRequest -> OrderRequest -> Execution."""
        from src.orders import (
            PaperMarketContext,
            PaperOrderExecutor,
            to_order_requests,
        )
        from src.live.orders import LiveOrderRequest

        # 1. LiveOrderRequests erstellen (wie von preview_live_orders.py)
        live_orders = [
            LiveOrderRequest(
                client_order_id="order-1",
                symbol="BTC/EUR",
                side="BUY",
                quantity=0.1,
                notional=5000.0,
                extra={"current_price": 50000.0},
            ),
            LiveOrderRequest(
                client_order_id="order-2",
                symbol="ETH/EUR",
                side="SELL",
                quantity=1.0,
                notional=3000.0,
                extra={"current_price": 3000.0},
            ),
        ]

        # 2. Zu OrderRequests konvertieren
        order_requests = to_order_requests(live_orders)

        # 3. Marktkontext mit Preisen erstellen
        ctx = PaperMarketContext(
            prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
            fee_bps=10.0,
        )

        # 4. Executor erstellen und Orders ausfuehren
        executor = PaperOrderExecutor(ctx)
        results = executor.execute_orders(order_requests)

        # 5. Ergebnisse pruefen
        assert len(results) == 2
        assert all(r.is_filled for r in results)

        # BTC-Order
        assert results[0].fill.symbol == "BTC/EUR"
        assert results[0].fill.quantity == 0.1
        assert results[0].fill.price == 50000.0
        assert results[0].fill.fee == pytest.approx(5.0, rel=1e-6)  # 5000 * 0.001

        # ETH-Order
        assert results[1].fill.symbol == "ETH/EUR"
        assert results[1].fill.quantity == 1.0
        assert results[1].fill.price == 3000.0
        assert results[1].fill.fee == pytest.approx(3.0, rel=1e-6)  # 3000 * 0.001

    def test_mixed_filled_rejected(self):
        """Flow mit gemischten Ergebnissen (filled + rejected)."""
        from src.orders import (
            PaperMarketContext,
            PaperOrderExecutor,
            OrderRequest,
        )

        # Marktkontext nur mit BTC-Preis
        ctx = PaperMarketContext(prices={"BTC/EUR": 50000.0})
        executor = PaperOrderExecutor(ctx)

        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1),
            OrderRequest(symbol="ETH/EUR", side="buy", quantity=1.0),  # Kein Preis
            OrderRequest(symbol="LTC/EUR", side="sell", quantity=5.0),  # Kein Preis
        ]

        results = executor.execute_orders(orders)

        # Zaehle filled/rejected
        filled = [r for r in results if r.is_filled]
        rejected = [r for r in results if r.is_rejected]

        assert len(filled) == 1
        assert len(rejected) == 2
        assert filled[0].fill.symbol == "BTC/EUR"


# =============================================================================
# 5. ExchangeOrderExecutor Stub Test
# =============================================================================

class TestExchangeOrderExecutorStub:
    """Test dass ExchangeOrderExecutor nicht implementiert ist."""

    def test_not_implemented(self):
        """ExchangeOrderExecutor wirft NotImplementedError."""
        from src.orders.paper import ExchangeOrderExecutor

        with pytest.raises(NotImplementedError):
            ExchangeOrderExecutor()


# =============================================================================
# CLI Sanity Check (wenn direkt ausgefuehrt)
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
