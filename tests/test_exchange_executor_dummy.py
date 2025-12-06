# tests/test_exchange_executor_dummy.py
"""
Peak_Trade: Tests für ExchangeOrderExecutor mit DummyExchangeClient (Phase 38)
==============================================================================

Tests für den erweiterten ExchangeOrderExecutor, der jetzt optional einen
TradingExchangeClient nutzen kann.

Diese Tests prüfen:
1. ExchangeOrderExecutor mit DummyExchangeClient
2. Order-Ausführung und Result-Mapping
3. Kompatibilität mit bestehendem Dry-Run-Modus
4. Factory-Methode from_config()
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.orders.base import OrderRequest, OrderExecutionResult
from src.orders.exchange import ExchangeOrderExecutor
from src.exchange.dummy_client import DummyExchangeClient
from src.exchange.base import ExchangeOrderStatus
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard


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
        },
        fee_bps=10.0,
        slippage_bps=5.0,
    )


@pytest.fixture
def testnet_env_config() -> EnvironmentConfig:
    """Erstellt eine Testnet-Environment-Config."""
    return EnvironmentConfig(
        environment=TradingEnvironment.TESTNET,
        enable_live_trading=False,
        testnet_dry_run=True,
    )


@pytest.fixture
def paper_env_config() -> EnvironmentConfig:
    """Erstellt eine Paper-Environment-Config."""
    return EnvironmentConfig(
        environment=TradingEnvironment.PAPER,
        enable_live_trading=False,
    )


@pytest.fixture
def safety_guard_testnet(testnet_env_config: EnvironmentConfig) -> SafetyGuard:
    """Erstellt einen SafetyGuard für Testnet."""
    return SafetyGuard(env_config=testnet_env_config)


@pytest.fixture
def safety_guard_paper(paper_env_config: EnvironmentConfig) -> SafetyGuard:
    """Erstellt einen SafetyGuard für Paper."""
    return SafetyGuard(env_config=paper_env_config)


@pytest.fixture
def executor_with_client(
    safety_guard_testnet: SafetyGuard,
    dummy_client: DummyExchangeClient,
) -> ExchangeOrderExecutor:
    """Erstellt einen ExchangeOrderExecutor mit DummyExchangeClient."""
    return ExchangeOrderExecutor(
        safety_guard=safety_guard_testnet,
        trading_client=dummy_client,
    )


@pytest.fixture
def executor_dry_run(safety_guard_testnet: SafetyGuard) -> ExchangeOrderExecutor:
    """Erstellt einen ExchangeOrderExecutor im Dry-Run-Modus."""
    return ExchangeOrderExecutor(
        safety_guard=safety_guard_testnet,
        simulated_prices={"BTC/EUR": 50000.0},
    )


@pytest.fixture
def sample_order() -> OrderRequest:
    """Erstellt eine Test-Order."""
    return OrderRequest(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.01,
        order_type="market",
        client_id="test_order_001",
    )


# =============================================================================
# Basic Tests
# =============================================================================


class TestExecutorBasics:
    """Basis-Tests für ExchangeOrderExecutor."""

    def test_executor_with_client_not_dry_run(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Executor mit Client ist nicht im Dry-Run-Modus."""
        assert executor_with_client.is_dry_run is False
        assert executor_with_client.trading_client is not None

    def test_executor_without_client_is_dry_run(
        self,
        executor_dry_run: ExchangeOrderExecutor,
    ) -> None:
        """Test: Executor ohne Client ist im Dry-Run-Modus."""
        assert executor_dry_run.is_dry_run is True
        assert executor_dry_run.trading_client is None

    def test_executor_initial_state(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Executor startet mit Execution-Count 0."""
        assert executor_with_client.get_execution_count() == 0


# =============================================================================
# Order Execution Tests (mit DummyClient)
# =============================================================================


class TestOrderExecutionWithClient:
    """Tests für Order-Ausführung mit DummyExchangeClient."""

    def test_execute_market_buy_order(
        self,
        executor_with_client: ExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Market-Buy-Order wird erfolgreich ausgeführt."""
        result = executor_with_client.execute_order(sample_order)

        assert isinstance(result, OrderExecutionResult)
        assert result.status == "filled"
        assert result.is_filled is True
        assert result.fill is not None
        assert result.fill.symbol == "BTC/EUR"
        assert result.fill.side == "buy"
        assert result.fill.quantity == 0.01
        assert result.fill.price > 0

    def test_execute_market_sell_order(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Market-Sell-Order wird erfolgreich ausgeführt."""
        order = OrderRequest(
            symbol="ETH/EUR",
            side="sell",
            quantity=1.0,
            order_type="market",
        )

        result = executor_with_client.execute_order(order)

        assert result.status == "filled"
        assert result.fill is not None
        assert result.fill.symbol == "ETH/EUR"
        assert result.fill.side == "sell"
        assert result.fill.quantity == 1.0

    def test_execute_order_increments_count(
        self,
        executor_with_client: ExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Execution-Count wird erhöht."""
        assert executor_with_client.get_execution_count() == 0

        executor_with_client.execute_order(sample_order)
        assert executor_with_client.get_execution_count() == 1

        executor_with_client.execute_order(sample_order)
        assert executor_with_client.get_execution_count() == 2

    def test_execute_order_metadata_contains_client_info(
        self,
        executor_with_client: ExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Metadata enthält Client-Informationen."""
        result = executor_with_client.execute_order(sample_order)

        assert "client_name" in result.metadata
        assert result.metadata["client_name"] == "dummy"
        assert "exchange_order_id" in result.metadata
        assert "mode" in result.metadata
        assert "trading_client_dummy" in result.metadata["mode"]

    def test_execute_order_with_fee(
        self,
        executor_with_client: ExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Fee wird korrekt in Fill übernommen."""
        result = executor_with_client.execute_order(sample_order)

        assert result.fill is not None
        assert result.fill.fee is not None
        assert result.fill.fee > 0
        assert result.fill.fee_currency == "EUR"


# =============================================================================
# Multiple Orders Tests
# =============================================================================


class TestMultipleOrders:
    """Tests für mehrere Orders."""

    def test_execute_multiple_orders(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Mehrere Orders werden alle ausgeführt."""
        orders = [
            OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01, order_type="market"),
            OrderRequest(symbol="ETH/EUR", side="sell", quantity=0.5, order_type="market"),
        ]

        results = executor_with_client.execute_orders(orders)

        assert len(results) == 2
        assert all(r.status == "filled" for r in results)
        assert executor_with_client.get_execution_count() == 2


# =============================================================================
# Dry-Run Backward Compatibility Tests
# =============================================================================


class TestDryRunBackwardCompatibility:
    """Tests für Rückwärtskompatibilität mit Dry-Run-Modus."""

    def test_dry_run_still_works(
        self,
        executor_dry_run: ExchangeOrderExecutor,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Dry-Run-Modus funktioniert weiterhin."""
        result = executor_dry_run.execute_order(sample_order)

        assert result.status == "filled"
        assert result.is_filled is True
        # Dry-Run-spezifische Metadata
        assert result.metadata.get("dry_run") is True
        assert result.metadata.get("mode") == "testnet_dry_run"

    def test_dry_run_uses_simulated_prices(
        self,
        safety_guard_testnet: SafetyGuard,
    ) -> None:
        """Test: Dry-Run nutzt simulierte Preise."""
        executor = ExchangeOrderExecutor(
            safety_guard=safety_guard_testnet,
            simulated_prices={"BTC/EUR": 60000.0},  # Anderer Preis
        )

        order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.1, order_type="market")
        result = executor.execute_order(order)

        assert result.fill is not None
        # Preis sollte nahe am simulierten Preis sein (+ Slippage)
        assert result.fill.price > 60000.0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests für Fehlerbehandlung."""

    def test_order_rejected_for_unknown_symbol(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Order für unbekanntes Symbol wird rejected."""
        order = OrderRequest(
            symbol="UNKNOWN/PAIR",
            side="buy",
            quantity=1.0,
            order_type="market",
        )

        result = executor_with_client.execute_order(order)

        # DummyClient rejected Orders ohne Preis
        assert result.status == "rejected"
        assert result.is_rejected is True


# =============================================================================
# Factory Method Tests
# =============================================================================


class TestFactoryMethod:
    """Tests für from_config() Factory-Methode."""

    def test_from_config_creates_executor_with_client(self) -> None:
        """Test: from_config() erstellt Executor mit TradingExchangeClient."""
        from src.core.peak_config import load_config

        cfg = load_config("config/config.toml")
        executor = ExchangeOrderExecutor.from_config(cfg)

        assert executor.is_dry_run is False
        assert executor.trading_client is not None
        assert executor.trading_client.get_name() == "dummy"

    def test_from_config_executor_can_execute_orders(self) -> None:
        """Test: Via from_config() erstellter Executor kann Orders ausführen."""
        from src.core.peak_config import load_config

        cfg = load_config("config/config.toml")
        executor = ExchangeOrderExecutor.from_config(cfg)

        order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.01,
            order_type="market",
        )

        result = executor.execute_order(order)

        assert result.status == "filled"
        assert result.fill is not None


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration-Tests."""

    def test_full_trading_flow(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Vollständiger Trading-Flow."""
        # 1. Buy BTC
        buy_order = OrderRequest(
            symbol="BTC/EUR",
            side="buy",
            quantity=0.1,
            order_type="market",
        )
        buy_result = executor_with_client.execute_order(buy_order)

        assert buy_result.status == "filled"
        assert buy_result.fill is not None
        buy_price = buy_result.fill.price

        # 2. Sell BTC
        sell_order = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.1,
            order_type="market",
        )
        sell_result = executor_with_client.execute_order(sell_order)

        assert sell_result.status == "filled"
        assert sell_result.fill is not None

        # 3. Execution-Count prüfen
        assert executor_with_client.get_execution_count() == 2

    def test_mixed_symbols(
        self,
        executor_with_client: ExchangeOrderExecutor,
    ) -> None:
        """Test: Orders auf verschiedenen Symbolen."""
        btc_order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01, order_type="market")
        eth_order = OrderRequest(symbol="ETH/EUR", side="sell", quantity=0.5, order_type="market")

        btc_result = executor_with_client.execute_order(btc_order)
        eth_result = executor_with_client.execute_order(eth_order)

        assert btc_result.status == "filled"
        assert eth_result.status == "filled"

        # Preise sollten unterschiedlich sein
        assert btc_result.fill.price > eth_result.fill.price  # BTC teurer als ETH




