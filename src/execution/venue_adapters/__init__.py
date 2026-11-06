"""
Venue Adapters Package (WP0C - Phase 0 Foundation)

Provides venue execution adapters for different execution modes:
- SimulatedVenueAdapter: Deterministic paper/shadow execution
- AdapterRegistry: Factory for adapter selection based on ExecutionMode

IMPORTANT: NO live execution. All adapters are for paper/shadow/testnet only.
           Live execution remains blocked/gated in Phase 0.
"""

from src.execution.venue_adapters.base import OrderAdapter, VenueAdapterError
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter
from src.execution.venue_adapters.registry import AdapterRegistry
from src.execution.venue_adapters.fill_models import (
    FillModel,
    ImmediateFillModel,
    FeeModel,
    FixedFeeModel,
    SlippageModel,
    FixedSlippageModel,
)

__all__ = [
    # Base
    "OrderAdapter",
    "VenueAdapterError",
    # Adapters
    "SimulatedVenueAdapter",
    # Registry
    "AdapterRegistry",
    # Fill Models
    "FillModel",
    "ImmediateFillModel",
    "FeeModel",
    "FixedFeeModel",
    "SlippageModel",
    "FixedSlippageModel",
]
