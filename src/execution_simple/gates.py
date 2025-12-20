# src/execution_simple/gates.py
"""
Execution Gates - Policy & Safety Checks.

Gates validate orders before execution and can block or modify orders.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Optional

from .types import ExecutionContext, ExecutionMode, GateDecision, OrderIntent, OrderSide


class Gate(ABC):
    """
    Base Gate Interface.

    Gates check order intent and return a decision (pass/block/modify).
    """

    @abstractmethod
    def check(self, intent: OrderIntent, context: ExecutionContext) -> GateDecision:
        """
        Check order intent against gate policy.

        Args:
            intent: Order intent to validate
            context: Execution context

        Returns:
            GateDecision with pass/block/modify result
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Gate name for logging."""
        raise NotImplementedError


class PriceSanityGate(Gate):
    """
    Validates price is reasonable (not NaN, <= 0, or extreme).

    Blocks orders with invalid prices.
    """

    @property
    def name(self) -> str:
        return "PriceSanity"

    def check(self, intent: OrderIntent, context: ExecutionContext) -> GateDecision:
        """Check price sanity."""
        price = context.price

        # Check for invalid price
        if price <= 0 or math.isnan(price) or math.isinf(price):
            return GateDecision(
                gate_name=self.name,
                passed=False,
                reason=f"Invalid price: {price}",
            )

        return GateDecision(
            gate_name=self.name,
            passed=True,
            reason="Price valid",
        )


class ResearchOnlyGate(Gate):
    """
    Blocks LIVE execution for research-tagged strategies.

    Prevents accidental live deployment of research code.
    """

    def __init__(self, block_research_in_live: bool = True):
        """
        Initialize gate.

        Args:
            block_research_in_live: If True, block LIVE mode with research_only tag
        """
        self.block_research_in_live = block_research_in_live

    @property
    def name(self) -> str:
        return "ResearchOnly"

    def check(self, intent: OrderIntent, context: ExecutionContext) -> GateDecision:
        """Check if research code is attempting to run in LIVE mode."""
        # Only check in LIVE mode
        if context.mode != ExecutionMode.LIVE:
            return GateDecision(
                gate_name=self.name,
                passed=True,
                reason=f"Mode {context.mode.value} allows research code",
            )

        # Check for research_only tag
        if not self.block_research_in_live:
            return GateDecision(
                gate_name=self.name,
                passed=True,
                reason="Research blocking disabled",
            )

        if "research_only" in context.tags:
            return GateDecision(
                gate_name=self.name,
                passed=False,
                reason="Research code blocked in LIVE mode (safety)",
            )

        return GateDecision(
            gate_name=self.name,
            passed=True,
            reason="No research tags detected",
        )


class LotSizeGate(Gate):
    """
    Rounds quantity to exchange lot size constraints.

    Modifies quantity to meet exchange minimum lot size requirements.
    """

    def __init__(self, lot_size: float = 0.0001, min_qty: float = 0.0001):
        """
        Initialize gate.

        Args:
            lot_size: Minimum increment for quantity (e.g., 0.0001 for BTC)
            min_qty: Absolute minimum quantity allowed
        """
        self.lot_size = lot_size
        self.min_qty = min_qty

    @property
    def name(self) -> str:
        return "LotSize"

    def check(self, intent: OrderIntent, context: ExecutionContext) -> GateDecision:
        """Round quantity to lot size and check minimum."""
        original_qty = intent.quantity

        # Round down to lot_size (with floating-point fix)
        if self.lot_size > 0:
            # Add epsilon to avoid floating-point errors (0.6/0.1 = 5.999999...)
            num_lots = math.floor(original_qty / self.lot_size + 1e-9)
            rounded_qty = round(num_lots * self.lot_size, 8)  # Round to 8 decimals
        else:
            rounded_qty = original_qty

        # Check minimum quantity
        if rounded_qty > 0 and rounded_qty < self.min_qty:
            return GateDecision(
                gate_name=self.name,
                passed=False,
                reason=f"Quantity {rounded_qty:.6f} below min_qty {self.min_qty}",
                modified_qty=rounded_qty,
            )

        # If rounded to zero, block
        if rounded_qty == 0 and original_qty > 0:
            return GateDecision(
                gate_name=self.name,
                passed=False,
                reason=f"Quantity {original_qty:.6f} rounds to 0 with lot_size {self.lot_size}",
                modified_qty=0.0,
            )

        return GateDecision(
            gate_name=self.name,
            passed=True,
            reason=f"Rounded {original_qty:.6f} → {rounded_qty:.6f}",
            modified_qty=rounded_qty if rounded_qty != original_qty else None,
        )


class MinNotionalGate(Gate):
    """
    Validates order meets minimum notional value requirement.

    Blocks orders below minimum notional (e.g., $10 minimum order size).
    """

    def __init__(self, min_notional: float = 10.0):
        """
        Initialize gate.

        Args:
            min_notional: Minimum order notional value (quantity * price)
        """
        self.min_notional = min_notional

    @property
    def name(self) -> str:
        return "MinNotional"

    def check(self, intent: OrderIntent, context: ExecutionContext) -> GateDecision:
        """Check if order meets minimum notional value."""
        notional = abs(intent.quantity * context.price)

        if notional < self.min_notional:
            return GateDecision(
                gate_name=self.name,
                passed=False,
                reason=f"Notional ${notional:.2f} below min ${self.min_notional:.2f}",
            )

        return GateDecision(
            gate_name=self.name,
            passed=True,
            reason=f"Notional ${notional:.2f} >= min ${self.min_notional:.2f}",
        )
