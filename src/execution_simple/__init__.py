# src/execution_simple/__init__.py
"""
Simplified Execution Pipeline (Learning & Demo Module).

This is a simplified, standalone execution pipeline for learning and demos.
It demonstrates core execution concepts without the complexity of the full
production execution module (src/execution/).

Use this for:
- Learning execution concepts
- Quick prototypes
- Demos and documentation

For production, use: src/execution.pipeline (Phase 16A V2 - Governance-aware)
"""

from .adapters import BaseBrokerAdapter, SimulatedBrokerAdapter
from .builder import build_execution_pipeline_from_config
from .gates import Gate, LotSizeGate, MinNotionalGate, PriceSanityGate, ResearchOnlyGate
from .pipeline import ExecutionPipeline
from .types import (
    ExecutionContext,
    ExecutionMode,
    ExecutionResult,
    Fill,
    GateDecision,
    Order,
    OrderIntent,
    OrderSide,
    OrderType,
)

__all__ = [
    # Types
    "ExecutionContext",
    "ExecutionMode",
    "ExecutionResult",
    "Fill",
    "GateDecision",
    "Order",
    "OrderIntent",
    "OrderSide",
    "OrderType",
    # Gates
    "Gate",
    "LotSizeGate",
    "MinNotionalGate",
    "PriceSanityGate",
    "ResearchOnlyGate",
    # Adapters
    "BaseBrokerAdapter",
    "SimulatedBrokerAdapter",
    # Pipeline
    "ExecutionPipeline",
    # Builder
    "build_execution_pipeline_from_config",
]
