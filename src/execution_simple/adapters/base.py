# src/execution_simple/adapters/base.py
"""
Base Broker Adapter Interface.

Defines contract for broker integrations.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import ExecutionContext, Fill, Order


class BaseBrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.

    Adapters handle actual order submission and fill reporting.
    """

    @abstractmethod
    def execute_order(self, order: Order, context: ExecutionContext) -> Fill:
        """
        Execute order and return fill.

        Args:
            order: Validated order to execute
            context: Execution context

        Returns:
            Fill result

        Raises:
            Exception: If order execution fails
        """
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Adapter name for logging."""
        raise NotImplementedError
