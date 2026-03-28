"""
Risk Layer (Phase 0+)

This package is the canonical entry point for risk-related primitives and layers.
It intentionally re-exports a minimal, side-effect-free surface:

- Adapters for Order <-> dict interop (introduced with the canonical Order contract work).

Kill Switch state machine: import ``KillSwitch`` from ``src.risk_layer.kill_switch`` (not re-exported here).

Keep this module import-safe (no runtime wiring, no environment access, no I/O).
"""

from __future__ import annotations

# Adapters (canonical Order contract)
from src.risk_layer.adapters import order_to_dict, to_order

__all__ = [
    "order_to_dict",
    "to_order",
]
