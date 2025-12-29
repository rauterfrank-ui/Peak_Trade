"""
Tests for WP1B - Paper Execution Engine

Tests:
- End-to-end order flow
- Ledger updates after fills
- Risk integration (BLOCK/PAUSE prevents execution)
- Journal tracking
"""

from decimal import Decimal

import pytest

from src.execution.contracts import OrderSide, OrderState, OrderType
from src.execution.paper.broker import FillSimulationConfig
from src.execution.paper.engine import ExecutionConfig, PaperExecutionEngine
from src.execution.risk_runtime.decisions import RiskDecision
from src.execution.risk_runtime.policies import MaxOpenOrdersPolicy, NoopPolicy
from src.execution.risk_runtime.runtime import RiskRuntime


class TestPaperExecutionEngineBasic:
    """Test basic execution engine functionality."""

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            initial_cash=Decimal("100000"),
        )
        engine = PaperExecutionEngine(config)

        assert engine.config.session_id == "test_session"
        assert engine.position_ledger.get_cash_balance() == Decimal("100000")

    def test_submit_market_order_full_flow(self):
        """Test full market order flow."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config)

        # Set market price
        engine.update_market_price("BTC/USD", Decimal("50000"))

        # Submit order
        order, fills = engine.submit_order(
            symbol="BTC/USD",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            order_type=OrderType.MARKET,
        )

        # Check order
        assert order.state == OrderState.FILLED
        assert order.symbol == "BTC/USD"
        assert order.quantity == Decimal("1.0")

        # Check fills
        assert len(fills) == 1
        assert fills[0].quantity == Decimal("1.0")

        # Check journal
        journal = engine.get_journal()
        assert len(journal.entries) == 1

    def test_ledger_updates_after_fill(self):
        """Test ledgers are updated correctly after fill."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            initial_cash=Decimal("100000"),
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        # Initial state
        initial_cash = engine.position_ledger.get_cash_balance()
        assert initial_cash == Decimal("100000")

        # Buy 1 BTC
        order, fills = engine.submit_order(
            symbol="BTC/USD",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            order_type=OrderType.MARKET,
        )

        # Check position created
        positions = engine.get_positions()
        assert len(positions) > 0

        btc_position = positions[0]
        assert btc_position.symbol == "BTC/USD"
        assert btc_position.quantity == Decimal("1.0")

        # Check cash reduced (cost + fee)
        current_cash = engine.position_ledger.get_cash_balance()
        assert current_cash < initial_cash

    def test_multiple_orders_tracked(self):
        """Test multiple orders are tracked correctly."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config)

        engine.update_market_price("BTC/USD", Decimal("50000"))
        engine.update_market_price("ETH/USD", Decimal("3000"))

        # Submit 3 orders
        engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("0.5")
        )
        engine.submit_order(
            symbol="ETH/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )
        engine.submit_order(
            symbol="BTC/USD", side=OrderSide.SELL, quantity=Decimal("0.2")
        )

        # Check order count
        stats = engine.get_stats()
        assert stats["total_orders"] == 3
        assert stats["total_fills"] == 3


class TestRiskIntegration:
    """Test risk runtime integration."""

    def test_risk_allows_order(self):
        """Test order proceeds when risk allows."""
        # Risk runtime with NoopPolicy (always allows)
        policies = [NoopPolicy()]
        risk_runtime = RiskRuntime(policies=policies)

        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config, risk_runtime=risk_runtime)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        order, fills = engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # Should proceed
        assert order.state == OrderState.FILLED
        assert len(fills) == 1

    def test_risk_blocks_order(self):
        """Test order is blocked when risk rejects."""
        # Risk runtime with MaxOpenOrdersPolicy (limit = 0, blocks all)
        policies = [MaxOpenOrdersPolicy(max_open_orders=0)]
        risk_runtime = RiskRuntime(policies=policies)

        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config, risk_runtime=risk_runtime)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        order, fills = engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # Should be rejected
        assert order.state == OrderState.REJECTED
        assert len(fills) == 0

        # Check audit log
        audit_entries = engine.audit_log.get_entries_by_event_type("RISK_ORDER_REJECTED")
        assert len(audit_entries) > 0

    def test_risk_block_prevents_ledger_update(self):
        """Test blocked order does not update ledgers."""
        policies = [MaxOpenOrdersPolicy(max_open_orders=0)]
        risk_runtime = RiskRuntime(policies=policies)

        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            initial_cash=Decimal("100000"),
        )
        engine = PaperExecutionEngine(config, risk_runtime=risk_runtime)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        initial_cash = engine.position_ledger.get_cash_balance()
        initial_positions = len(engine.get_positions())

        # Submit order (will be blocked)
        engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # Cash should not change
        assert engine.position_ledger.get_cash_balance() == initial_cash

        # Positions should not change
        assert len(engine.get_positions()) == initial_positions


class TestJournalTracking:
    """Test trade journal tracking."""

    def test_journal_entry_created_on_fill(self):
        """Test journal entry is created when order fills."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        order, fills = engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # Check journal
        journal = engine.get_journal()
        assert len(journal.entries) == 1

        entry = journal.entries[0]
        assert entry.client_order_id == order.client_order_id
        assert entry.symbol == "BTC/USD"
        assert entry.side == OrderSide.BUY
        assert entry.quantity == Decimal("1.0")

    def test_journal_not_created_when_blocked(self):
        """Test journal entry NOT created when order is blocked."""
        policies = [MaxOpenOrdersPolicy(max_open_orders=0)]
        risk_runtime = RiskRuntime(policies=policies)

        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
        )
        engine = PaperExecutionEngine(config, risk_runtime=risk_runtime)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        order, fills = engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # No journal entry (order was blocked)
        journal = engine.get_journal()
        assert len(journal.entries) == 0


class TestEngineStats:
    """Test engine statistics."""

    def test_stats_summary(self):
        """Test engine stats provide correct summary."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
            fill_simulation=FillSimulationConfig(random_seed=42),
        )
        engine = PaperExecutionEngine(config)

        engine.update_market_price("BTC/USD", Decimal("50000"))

        # Submit orders
        engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )
        engine.submit_order(
            symbol="BTC/USD", side=OrderSide.SELL, quantity=Decimal("0.5")
        )

        stats = engine.get_stats()

        assert stats["session_id"] == "test_session"
        assert stats["strategy_id"] == "test_strategy"
        assert stats["total_orders"] == 2
        assert stats["total_fills"] == 2
        assert stats["positions"] >= 1

    def test_no_market_price_fails(self):
        """Test order fails when no market price available."""
        config = ExecutionConfig(
            session_id="test_session",
            strategy_id="test_strategy",
        )
        engine = PaperExecutionEngine(config)

        # No market price set
        order, fills = engine.submit_order(
            symbol="BTC/USD", side=OrderSide.BUY, quantity=Decimal("1.0")
        )

        # Should fail
        assert order.state == OrderState.FAILED
        assert len(fills) == 0
