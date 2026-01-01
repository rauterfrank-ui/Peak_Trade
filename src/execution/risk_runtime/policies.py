"""
Risk Policies (WP0B)

Pluggable risk evaluation policies.
"""

from typing import Protocol
from decimal import Decimal

from src.execution.risk_runtime.decisions import (
    RiskDirective,
    allow_directive,
    reject_directive,
)
from src.execution.risk_runtime.context import RiskContextSnapshot


# ============================================================================
# Risk Policy Protocol
# ============================================================================


class RiskPolicy(Protocol):
    """
    Protocol for risk policies.

    Design:
    - name: Human-readable policy name
    - evaluate(): Stateless evaluation (idempotent)
    - Returns RiskDirective (ALLOW/REJECT/MODIFY/HALT)
    - Policies are composable (runtime evaluates all)
    """

    name: str

    def evaluate(self, snapshot: RiskContextSnapshot) -> RiskDirective:
        """
        Evaluate snapshot against policy.

        Args:
            snapshot: Current system state

        Returns:
            RiskDirective with decision
        """
        ...


# ============================================================================
# Noop Policy
# ============================================================================


class NoopPolicy:
    """
    Noop policy (always allows).

    Use cases:
    - Testing
    - Development (bypass risk checks)
    - Default safe policy
    """

    name = "NoopPolicy"

    def evaluate(self, snapshot: RiskContextSnapshot) -> RiskDirective:
        """Always allow"""
        return allow_directive(
            reason="NoopPolicy: no checks",
            policy=self.name,
        )


# ============================================================================
# Max Open Orders Policy
# ============================================================================


class MaxOpenOrdersPolicy:
    """
    Limit maximum number of open orders.

    Design:
    - Reject if open_orders_count >= max_open_orders
    - Deterministic (same snapshot → same decision)
    - No state (idempotent)
    """

    name = "MaxOpenOrdersPolicy"

    def __init__(self, max_open_orders: int):
        """
        Initialize policy.

        Args:
            max_open_orders: Maximum allowed open orders
        """
        self.max_open_orders = max_open_orders

    def evaluate(self, snapshot: RiskContextSnapshot) -> RiskDirective:
        """
        Evaluate if open orders limit is exceeded.

        Args:
            snapshot: Current system state

        Returns:
            ALLOW if within limit, REJECT if exceeded
        """
        if snapshot.open_orders_count >= self.max_open_orders:
            return reject_directive(
                reason=f"Max open orders exceeded: {snapshot.open_orders_count} >= {self.max_open_orders}",
                policy=self.name,
                limit=str(self.max_open_orders),
                current=str(snapshot.open_orders_count),
            )

        return allow_directive(
            reason=f"Open orders within limit: {snapshot.open_orders_count} < {self.max_open_orders}",
            policy=self.name,
        )


# ============================================================================
# Max Position Size Policy
# ============================================================================


class MaxPositionSizePolicy:
    """
    Limit maximum position size per symbol.

    Design:
    - Reject if position size would exceed limit after order
    - Checks both current position + pending order
    - Deterministic
    """

    name = "MaxPositionSizePolicy"

    def __init__(self, max_position_size: Decimal):
        """
        Initialize policy.

        Args:
            max_position_size: Maximum allowed position size (absolute)
        """
        self.max_position_size = max_position_size

    def evaluate(self, snapshot: RiskContextSnapshot) -> RiskDirective:
        """
        Evaluate if position size limit would be exceeded.

        Args:
            snapshot: Current system state

        Returns:
            ALLOW if within limit, REJECT if exceeded
        """
        # Only check if we have an order
        if not snapshot.order:
            return allow_directive(reason="No order to evaluate", policy=self.name)

        order = snapshot.order
        symbol = order.symbol

        # Get current position
        current_position = snapshot.positions_summary.get(symbol, Decimal("0"))

        # Calculate new position after order
        from src.execution.contracts import OrderSide

        if order.side == OrderSide.BUY:
            new_position = current_position + order.quantity
        else:  # SELL
            new_position = current_position - order.quantity

        # Check if new position exceeds limit
        if abs(new_position) > self.max_position_size:
            return reject_directive(
                reason=f"Position size limit exceeded: {abs(new_position)} > {self.max_position_size}",
                policy=self.name,
                symbol=symbol,
                limit=str(self.max_position_size),
                current=str(abs(current_position)),
                new=str(abs(new_position)),
            )

        return allow_directive(
            reason=f"Position size within limit: {abs(new_position)} <= {self.max_position_size}",
            policy=self.name,
        )


# ============================================================================
# Min Cash Balance Policy
# ============================================================================


class MinCashBalancePolicy:
    """
    Ensure minimum cash balance is maintained.

    Design:
    - Reject if order would cause cash balance < min_cash_balance
    - Simple check (doesn't account for fees/slippage in Phase 0)
    - Deterministic
    """

    name = "MinCashBalancePolicy"

    def __init__(self, min_cash_balance: Decimal):
        """
        Initialize policy.

        Args:
            min_cash_balance: Minimum required cash balance
        """
        self.min_cash_balance = min_cash_balance

    def evaluate(self, snapshot: RiskContextSnapshot) -> RiskDirective:
        """
        Evaluate if min cash balance would be maintained.

        Args:
            snapshot: Current system state

        Returns:
            ALLOW if sufficient cash, REJECT otherwise
        """
        # Only check for BUY orders (SELL orders increase cash)
        if not snapshot.order:
            return allow_directive(reason="No order to evaluate", policy=self.name)

        from src.execution.contracts import OrderSide

        order = snapshot.order

        if order.side == OrderSide.SELL:
            # SELL orders increase cash, always OK
            return allow_directive(reason="SELL order increases cash", policy=self.name)

        # BUY order: estimate cost
        if order.price is not None:
            estimated_cost = order.price * order.quantity
        else:
            # MARKET order: can't estimate precisely, use conservative check
            # In production: use mark price or recent trade price
            return allow_directive(
                reason="MARKET order: cannot estimate cost in Phase 0",
                policy=self.name,
            )

        # Check if cash balance would fall below minimum
        estimated_new_balance = snapshot.cash_balance - estimated_cost

        if estimated_new_balance < self.min_cash_balance:
            return reject_directive(
                reason=f"Insufficient cash: {estimated_new_balance} < {self.min_cash_balance}",
                policy=self.name,
                limit=str(self.min_cash_balance),
                current=str(snapshot.cash_balance),
                estimated_new=str(estimated_new_balance),
            )

        return allow_directive(
            reason=f"Sufficient cash: {estimated_new_balance} >= {self.min_cash_balance}",
            policy=self.name,
        )
