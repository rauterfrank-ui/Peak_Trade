# src/execution_simple/pipeline.py
"""
Execution Pipeline - Core Orchestrator.

Orchestrates order generation, gate validation, and execution.
"""

from __future__ import annotations

from typing import Optional

from .adapters.base import BaseBrokerAdapter
from .gates import Gate
from .types import (
    ExecutionContext,
    ExecutionMode,
    ExecutionResult,
    Order,
    OrderIntent,
    OrderSide,
    OrderType,
)


class ExecutionPipeline:
    """
    Orchestrates order execution pipeline.

    Flow:
    1. Compute desired position change (delta)
    2. Create OrderIntent
    3. Validate through gates (in order)
    4. Create validated Order
    5. Execute via adapter (if configured)
    6. Return ExecutionResult

    Gates are applied in order:
    - PriceSanity: Validate price is valid
    - ResearchOnly: Block research code in LIVE
    - LotSize: Round quantity to lot size
    - MinNotional: Check minimum order size
    """

    def __init__(
        self,
        gates: list[Gate],
        adapter: Optional[BaseBrokerAdapter] = None,
    ):
        """
        Initialize pipeline.

        Args:
            gates: List of gates to apply (in order)
            adapter: Optional broker adapter for execution
        """
        self.gates = gates
        self.adapter = adapter

    def execute(
        self,
        target_position: float,
        current_position: float,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute position change.

        Args:
            target_position: Desired position in units
            current_position: Current position in units
            context: Execution context (mode, price, tags, etc.)

        Returns:
            ExecutionResult with orders, fills, and gate decisions
        """
        # 1. Compute desired delta
        desired_delta = target_position - current_position

        # Initialize result
        result = ExecutionResult(
            context=context,
            desired_delta=desired_delta,
        )

        # 2. If no change needed, return early
        if desired_delta == 0:
            return result

        # 3. Determine side and quantity
        if desired_delta > 0:
            side = OrderSide.BUY
            quantity = abs(desired_delta)
        else:
            side = OrderSide.SELL
            quantity = abs(desired_delta)

        # 4. Create initial intent
        intent = OrderIntent(
            symbol=context.symbol,
            side=side,
            quantity=quantity,
            price=context.price,
            order_type=OrderType.MARKET,
        )

        # 5. Apply gates in order
        for gate in self.gates:
            decision = gate.check(intent, context)
            result.gate_decisions.append(decision)

            # If gate blocks, stop pipeline
            if not decision.passed:
                result.blocked = True
                result.block_reason = f"{gate.name}: {decision.reason}"
                return result

            # If gate modifies quantity, update intent
            if decision.modified_qty is not None:
                intent.quantity = decision.modified_qty

        # 6. All gates passed - create validated order
        order = Order(
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            price=intent.price,
            order_type=intent.order_type,
        )
        result.orders.append(order)

        # 7. Execute via adapter (if configured and mode allows)
        if self.adapter and context.mode in (ExecutionMode.PAPER, ExecutionMode.BACKTEST):
            try:
                fill = self.adapter.execute_order(order, context)
                result.fills.append(fill)
            except Exception as e:
                result.blocked = True
                result.block_reason = f"Execution failed: {e}"

        return result
