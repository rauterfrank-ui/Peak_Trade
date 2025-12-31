"""
Adapter Registry (WP0C - Phase 0 Foundation)

Provides factory pattern for venue adapter selection based on ExecutionMode.

Design Goals:
- Mode-based routing (PAPER → SimulatedAdapter, etc.)
- Extensible (register new adapters easily)
- Fail-fast validation (all modes have adapters)
- No live enablement (LIVE_BLOCKED → reject)

IMPORTANT: NO live execution. Registry only provides paper/shadow/testnet adapters.
           Live execution remains blocked/gated in Phase 0.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from src.execution.orchestrator import ExecutionMode
from src.execution.venue_adapters.base import OrderAdapter, VenueAdapterError
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Registry and factory for venue adapters.

    Usage:
        registry = AdapterRegistry.create_default()
        adapter = registry.get_adapter(ExecutionMode.PAPER)
        event = adapter.execute_order(order, idempotency_key)

    Supported modes (Phase 0):
    - PAPER: SimulatedVenueAdapter (paper trading)
    - SHADOW: SimulatedVenueAdapter (shadow mode)
    - TESTNET: SimulatedVenueAdapter (testnet dry-run)
    - LIVE_BLOCKED: Raises VenueAdapterError (governance block)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._adapters: Dict[ExecutionMode, OrderAdapter] = {}
        logger.info("AdapterRegistry initialized (empty)")

    def register(self, mode: ExecutionMode, adapter: OrderAdapter) -> None:
        """
        Register adapter for execution mode.

        Args:
            mode: Execution mode (PAPER/SHADOW/TESTNET/LIVE_BLOCKED)
            adapter: Adapter instance

        Raises:
            ValueError: If mode already registered
        """
        if mode in self._adapters:
            raise ValueError(f"Adapter already registered for mode: {mode.value}")

        self._adapters[mode] = adapter
        logger.info(
            f"AdapterRegistry: Registered {adapter.__class__.__name__} for mode {mode.value}"
        )

    def get_adapter(self, mode: ExecutionMode) -> OrderAdapter:
        """
        Get adapter for execution mode.

        Args:
            mode: Execution mode

        Returns:
            OrderAdapter instance

        Raises:
            VenueAdapterError: If mode not registered or blocked
        """
        # LIVE_BLOCKED: explicit governance block
        if mode == ExecutionMode.LIVE_BLOCKED:
            raise VenueAdapterError(
                f"Live execution is governance-blocked (Phase 0). Mode={mode.value} is not allowed."
            )

        # Unknown mode: reject
        if mode not in self._adapters:
            raise VenueAdapterError(
                f"No adapter registered for mode: {mode.value}. "
                f"Available modes: {list(self._adapters.keys())}"
            )

        adapter = self._adapters[mode]
        logger.debug(
            f"AdapterRegistry: Retrieved {adapter.__class__.__name__} for mode {mode.value}"
        )
        return adapter

    def has_adapter(self, mode: ExecutionMode) -> bool:
        """
        Check if adapter is registered for mode.

        Args:
            mode: Execution mode

        Returns:
            True if adapter registered, False otherwise
        """
        return mode in self._adapters

    def list_modes(self) -> list[ExecutionMode]:
        """
        List all registered modes.

        Returns:
            List of ExecutionMode
        """
        return list(self._adapters.keys())

    @classmethod
    def create_default(cls) -> AdapterRegistry:
        """
        Create registry with default adapters for Phase 0.

        Default mappings:
        - PAPER → SimulatedVenueAdapter(enable_fills=True)
        - SHADOW → SimulatedVenueAdapter(enable_fills=True)
        - TESTNET → SimulatedVenueAdapter(enable_fills=True)
        - LIVE_BLOCKED → Not registered (explicit block)

        Returns:
            AdapterRegistry with default adapters
        """
        registry = cls()

        # PAPER mode: full simulation
        registry.register(
            ExecutionMode.PAPER,
            SimulatedVenueAdapter(enable_fills=True),
        )

        # SHADOW mode: same as PAPER
        registry.register(
            ExecutionMode.SHADOW,
            SimulatedVenueAdapter(enable_fills=True),
        )

        # TESTNET mode: same as PAPER (dry-run)
        registry.register(
            ExecutionMode.TESTNET,
            SimulatedVenueAdapter(enable_fills=True),
        )

        # LIVE_BLOCKED: NOT registered (governance block)
        # Calling get_adapter(LIVE_BLOCKED) will raise VenueAdapterError

        logger.info(
            f"AdapterRegistry: Created default registry with "
            f"{len(registry._adapters)} adapters (PAPER/SHADOW/TESTNET)"
        )

        return registry

    @classmethod
    def create_for_testing(
        cls,
        enable_fills: bool = True,
        market_prices: Optional[dict] = None,
    ) -> AdapterRegistry:
        """
        Create registry with testing-friendly adapters.

        Args:
            enable_fills: If False, orders are ACKed but not filled
            market_prices: Custom market prices (for fill simulation)

        Returns:
            AdapterRegistry for testing
        """
        registry = cls()

        # Create adapter with custom config
        adapter = SimulatedVenueAdapter(
            enable_fills=enable_fills,
            market_prices=market_prices,
        )

        # Register for all non-live modes
        registry.register(ExecutionMode.PAPER, adapter)
        registry.register(ExecutionMode.SHADOW, adapter)
        registry.register(ExecutionMode.TESTNET, adapter)

        logger.info(f"AdapterRegistry: Created testing registry (enable_fills={enable_fills})")

        return registry
