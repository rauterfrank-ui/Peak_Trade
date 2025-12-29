"""
Risk Hook Interface (WP0E - Phase 0 Foundation)

This module defines the interface between execution and risk layer.
NO cyclic imports - execution depends on contracts, risk depends on contracts.

Design Goals:
- Risk is called via stable interface (Protocol)
- Execution never imports from src/risk_layer directly
- Risk implementation is injectable (testing, mocking)
- No side effects (pure evaluation)
"""

from typing import Protocol, Optional, Dict, Any
from decimal import Decimal

from src.execution.contracts import Order, RiskResult, RiskDecision


# ============================================================================
# Risk Hook Protocol (Interface)
# ============================================================================


class RiskHook(Protocol):
    """
    Protocol for risk evaluation.

    Execution calls this interface to check if an order is allowed.
    Risk layer implements this protocol.

    Design:
    - Protocol (not ABC) for maximum flexibility
    - Stateless evaluation (idempotent)
    - No side effects (pure function)
    """

    def evaluate_order(self, order: Order, context: Optional[Dict[str, Any]] = None) -> RiskResult:
        """
        Evaluate if an order should be allowed.

        Args:
            order: Order to evaluate
            context: Optional context (portfolio state, market conditions, etc.)

        Returns:
            RiskResult with decision (ALLOW/BLOCK/PAUSE) and reason
        """
        ...

    def check_kill_switch(self) -> RiskResult:
        """
        Check if kill switch is active.

        Returns:
            RiskResult with decision (ALLOW if inactive, PAUSE if active)
        """
        ...

    def evaluate_position_change(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """
        Evaluate if a position change is allowed (pre-fill check).

        Args:
            symbol: Symbol (e.g., "BTC-EUR")
            quantity: Position size change
            side: "BUY" or "SELL"
            context: Optional context

        Returns:
            RiskResult with decision
        """
        ...


# ============================================================================
# Null Risk Hook (Default/Testing)
# ============================================================================


class NullRiskHook:
    """
    Null implementation of RiskHook (always allows).

    Used for:
    - Testing (no risk checks)
    - Development (bypass risk)
    - Safe default (explicit opt-in to risk checks)
    """

    def evaluate_order(self, order: Order, context: Optional[Dict[str, Any]] = None) -> RiskResult:
        """Always allow (null implementation)"""
        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="NullRiskHook: no checks",
            metadata={"hook_type": "null"},
        )

    def check_kill_switch(self) -> RiskResult:
        """Always inactive (null implementation)"""
        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="NullRiskHook: kill switch inactive",
            metadata={"hook_type": "null"},
        )

    def evaluate_position_change(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """Always allow (null implementation)"""
        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="NullRiskHook: no position checks",
            metadata={"hook_type": "null", "symbol": symbol},
        )


# ============================================================================
# Blocking Risk Hook (Testing)
# ============================================================================


class BlockingRiskHook:
    """
    Blocking implementation of RiskHook (always blocks).

    Used for:
    - Testing (verify block behavior)
    - Emergency override (block all orders)
    """

    def __init__(self, reason: str = "BlockingRiskHook: blocked"):
        self.reason = reason

    def evaluate_order(self, order: Order, context: Optional[Dict[str, Any]] = None) -> RiskResult:
        """Always block"""
        return RiskResult(
            decision=RiskDecision.BLOCK,
            reason=self.reason,
            metadata={"hook_type": "blocking"},
        )

    def check_kill_switch(self) -> RiskResult:
        """Always active (block)"""
        return RiskResult(
            decision=RiskDecision.PAUSE,
            reason=self.reason,
            metadata={"hook_type": "blocking"},
        )

    def evaluate_position_change(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """Always block"""
        return RiskResult(
            decision=RiskDecision.BLOCK,
            reason=self.reason,
            metadata={"hook_type": "blocking", "symbol": symbol},
        )


# ============================================================================
# Conditional Risk Hook (Testing)
# ============================================================================


class ConditionalRiskHook:
    """
    Conditional implementation of RiskHook (allows/blocks based on conditions).

    Used for:
    - Testing (simulate specific risk scenarios)
    - Development (prototype risk logic)
    """

    def __init__(
        self,
        allow_symbols: Optional[set] = None,
        max_quantity: Optional[Decimal] = None,
        kill_switch_active: bool = False,
    ):
        self.allow_symbols = allow_symbols or set()
        self.max_quantity = max_quantity
        self.kill_switch_active = kill_switch_active

    def evaluate_order(self, order: Order, context: Optional[Dict[str, Any]] = None) -> RiskResult:
        """Conditional evaluation"""
        # Check kill switch first
        if self.kill_switch_active:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason="Kill switch is active",
                metadata={"hook_type": "conditional"},
            )

        # Check symbol whitelist
        if self.allow_symbols and order.symbol not in self.allow_symbols:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason=f"Symbol {order.symbol} not in whitelist",
                metadata={"hook_type": "conditional", "allow_symbols": list(self.allow_symbols)},
            )

        # Check quantity limit
        if self.max_quantity is not None and order.quantity > self.max_quantity:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason=f"Quantity {order.quantity} exceeds max {self.max_quantity}",
                metadata={"hook_type": "conditional", "max_quantity": str(self.max_quantity)},
            )

        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="All conditional checks passed",
            metadata={"hook_type": "conditional"},
        )

    def check_kill_switch(self) -> RiskResult:
        """Check kill switch status"""
        if self.kill_switch_active:
            return RiskResult(
                decision=RiskDecision.PAUSE,
                reason="Kill switch is active",
                metadata={"hook_type": "conditional"},
            )
        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="Kill switch inactive",
            metadata={"hook_type": "conditional"},
        )

    def evaluate_position_change(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskResult:
        """Conditional position evaluation"""
        if self.kill_switch_active:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason="Kill switch is active",
                metadata={"hook_type": "conditional"},
            )

        if self.allow_symbols and symbol not in self.allow_symbols:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason=f"Symbol {symbol} not in whitelist",
                metadata={"hook_type": "conditional"},
            )

        if self.max_quantity is not None and quantity > self.max_quantity:
            return RiskResult(
                decision=RiskDecision.BLOCK,
                reason=f"Quantity {quantity} exceeds max {self.max_quantity}",
                metadata={"hook_type": "conditional"},
            )

        return RiskResult(
            decision=RiskDecision.ALLOW,
            reason="All conditional checks passed",
            metadata={"hook_type": "conditional"},
        )


# ============================================================================
# Helper Functions
# ============================================================================


def create_null_hook() -> NullRiskHook:
    """Factory for null risk hook"""
    return NullRiskHook()


def create_blocking_hook(reason: str = "Blocked by policy") -> BlockingRiskHook:
    """Factory for blocking risk hook"""
    return BlockingRiskHook(reason=reason)


def create_conditional_hook(
    allow_symbols: Optional[set] = None,
    max_quantity: Optional[Decimal] = None,
    kill_switch_active: bool = False,
) -> ConditionalRiskHook:
    """Factory for conditional risk hook"""
    return ConditionalRiskHook(
        allow_symbols=allow_symbols,
        max_quantity=max_quantity,
        kill_switch_active=kill_switch_active,
    )
