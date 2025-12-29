"""
Paper Execution Engine - WP1B (Phase 1 Shadow Trading)

Orchestrates the full paper trading flow:
Strategy Signals → Risk Check → Orders → Paper Fills → Ledgers → Journal
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from src.execution.audit_log import AuditLog
from src.execution.contracts import Fill, LedgerEntry, Order, OrderSide, OrderState, OrderType
from src.execution.order_ledger import OrderLedger
from src.execution.paper.broker import FillSimulationConfig, PaperBroker
from src.execution.paper.journal import JournalEntry, TradeJournal
from src.execution.position_ledger import PositionLedger
from src.execution.risk_runtime.decisions import RiskDecision
from src.execution.risk_runtime.runtime import RiskRuntime
from src.observability.logging import get_logger, set_context

logger = get_logger(__name__)


@dataclass
class ExecutionConfig:
    """
    Configuration for paper execution engine.

    Attributes:
        session_id: Unique session identifier
        strategy_id: Strategy identifier
        initial_cash: Initial cash balance
        fill_simulation: Fill simulation configuration
    """

    session_id: str
    strategy_id: str
    initial_cash: Decimal = Decimal("100000")  # $100k default
    fill_simulation: Optional[FillSimulationConfig] = None

    def __post_init__(self):
        if self.fill_simulation is None:
            self.fill_simulation = FillSimulationConfig()


class PaperExecutionEngine:
    """
    Paper execution engine with risk integration.

    Orchestrates:
    - Signal → Order creation
    - Risk checks (pre-submit gate via RiskRuntime)
    - Order submission to PaperBroker
    - Fill processing → Ledger updates
    - Trade journal

    Usage:
        >>> config = ExecutionConfig(session_id="shadow_1", strategy_id="ma_cross")
        >>> engine = PaperExecutionEngine(config)
        >>> order = engine.submit_order(...)
        >>> journal = engine.get_journal()
    """

    def __init__(
        self,
        config: ExecutionConfig,
        risk_runtime: Optional[RiskRuntime] = None,
    ):
        """
        Initialize paper execution engine.

        Args:
            config: Execution configuration
            risk_runtime: Optional RiskRuntime for pre-submit checks
        """
        self.config = config

        # Set observability context
        set_context(
            session_id=config.session_id,
            strategy_id=config.strategy_id,
            env="shadow",
        )

        # Initialize components
        self.broker = PaperBroker(config.fill_simulation)
        self.order_ledger = OrderLedger()
        self.position_ledger = PositionLedger(initial_cash=config.initial_cash)
        self.audit_log = AuditLog()
        self.journal = TradeJournal()

        # Risk runtime (optional)
        self.risk_runtime = risk_runtime

        # Market data (for fill simulation)
        self._current_prices: Dict[str, Decimal] = {}

        logger.info(
            f"Paper execution engine initialized: "
            f"session={config.session_id} strategy={config.strategy_id} "
            f"cash={config.initial_cash}"
        )

    def update_market_price(self, symbol: str, price: Decimal) -> None:
        """
        Update current market price for a symbol.

        Args:
            symbol: Symbol to update
            price: Current price
        """
        self._current_prices[symbol] = price

    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        client_order_id: Optional[str] = None,
    ) -> tuple[Order, List[Fill]]:
        """
        Submit order with risk checks.

        Args:
            symbol: Symbol to trade
            side: Order side (BUY/SELL)
            quantity: Order quantity
            order_type: Order type (MARKET/LIMIT)
            price: Limit price (for LIMIT orders)
            client_order_id: Optional client order ID

        Returns:
            Tuple of (order, fills)
        """
        # Generate client order ID if not provided
        if client_order_id is None:
            import uuid

            client_order_id = f"paper_{uuid.uuid4().hex[:8]}"

        # Create order
        order = Order(
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            state=OrderState.CREATED,
            strategy_id=self.config.strategy_id,
            session_id=self.config.session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Add to ledger
        self.order_ledger.add_order(order)

        # Risk check (pre-submit gate)
        if self.risk_runtime:
            risk_result = self._check_risk(order)

            if risk_result.decision == RiskDecision.REJECT:
                # REJECT: Do not submit, mark as failed
                logger.warning(
                    f"Order {order.client_order_id} REJECTED by risk: {risk_result.reason}"
                )

                order.state = OrderState.REJECTED
                self.order_ledger.update_order(order, event="RISK_REJECTED")

                audit_entry = LedgerEntry(
                    entry_id=f"risk_{order.client_order_id}",
                    event_type="RISK_ORDER_REJECTED",
                    client_order_id=order.client_order_id,
                    details={
                        "reason": risk_result.reason,
                        "decision": risk_result.decision.value,
                    },
                )
                self.audit_log.append(audit_entry)

                return (order, [])

            elif risk_result.decision == RiskDecision.HALT:
                # HALT: Emergency stop
                logger.error(
                    f"Order {order.client_order_id} HALTED by risk: {risk_result.reason}"
                )

                order.state = OrderState.FAILED
                self.order_ledger.update_order(order, event="RISK_HALTED")

                audit_entry = LedgerEntry(
                    entry_id=f"risk_{order.client_order_id}",
                    event_type="RISK_ORDER_HALTED",
                    client_order_id=order.client_order_id,
                    details={
                        "reason": risk_result.reason,
                        "decision": risk_result.decision.value,
                    },
                )
                self.audit_log.append(audit_entry)

                return (order, [])

        # Submit to paper broker
        current_price = self._current_prices.get(symbol, Decimal("0"))
        if current_price == 0:
            logger.error(f"No market price for {symbol}")
            order.state = OrderState.FAILED
            self.order_ledger.update_order(order, event="NO_MARKET_DATA")
            return (order, [])

        new_state, fills = self.broker.submit_order(order, current_price)

        # Update order state
        order.state = new_state
        order.updated_at = datetime.utcnow()
        self.order_ledger.update_order(order, event="ORDER_SUBMITTED")

        # Process fills
        for fill in fills:
            self._process_fill(fill)

        # Journal entry
        if fills:
            self.journal.add_entry(
                JournalEntry(
                    timestamp=datetime.utcnow(),
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    side=order.side,
                    quantity=sum(f.quantity for f in fills),
                    avg_price=sum(f.price * f.quantity for f in fills)
                    / sum(f.quantity for f in fills),
                    total_fee=sum(f.fee for f in fills),
                    order_state=order.state,
                    metadata={
                        "strategy_id": self.config.strategy_id,
                        "session_id": self.config.session_id,
                    },
                )
            )

        logger.info(
            f"Order {order.client_order_id} submitted: "
            f"state={order.state.value} fills={len(fills)}"
        )

        return (order, fills)

    def _check_risk(self, order: Order) -> any:
        """
        Check order against risk runtime.

        Args:
            order: Order to check

        Returns:
            RiskDirective
        """
        # Evaluate via risk runtime
        result = self.risk_runtime.evaluate_pre_order(
            order=order,
            order_ledger=self.order_ledger,
            position_ledger=self.position_ledger,
        )

        return result

    def _process_fill(self, fill: Fill) -> None:
        """
        Process a fill and update ledgers.

        Args:
            fill: Fill to process
        """
        # Update position ledger
        self.position_ledger.apply_fill(fill)

        # Audit log
        audit_entry = LedgerEntry(
            entry_id=f"fill_{fill.fill_id}",
            event_type="FILL_PROCESSED",
            client_order_id=fill.client_order_id,
            details={
                "fill_id": fill.fill_id,
                "symbol": fill.symbol,
                "side": fill.side.value,
                "quantity": str(fill.quantity),
                "price": str(fill.price),
                "fee": str(fill.fee),
            },
        )
        self.audit_log.append(audit_entry)

    def get_positions(self) -> List:
        """Get current positions."""
        return self.position_ledger.get_all_positions()

    def get_pnl(self) -> Decimal:
        """Get total PnL."""
        return self.position_ledger.get_total_pnl(self._current_prices)

    def get_journal(self) -> TradeJournal:
        """Get trade journal."""
        return self.journal

    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "session_id": self.config.session_id,
            "strategy_id": self.config.strategy_id,
            "total_orders": self.order_ledger.get_order_count(),
            "total_fills": len(self.journal.entries),
            "positions": len(self.get_positions()),
            "total_pnl": str(self.get_pnl()),
            "broker_stats": self.broker.get_stats(),
        }
