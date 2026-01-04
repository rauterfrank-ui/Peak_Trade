"""
Risk Layer (Phase 0+)

This package is the canonical entry point for risk-related primitives and layers.
It intentionally re-exports a minimal, side-effect-free surface:

- Adapters for Order <-> dict interop (introduced with the canonical Order contract work).
- Kill Switch primitives for emergency stop / trading halt semantics.

Keep this module import-safe (no runtime wiring, no environment access, no I/O).
"""

from __future__ import annotations

# Adapters (canonical Order contract)
from src.risk_layer.adapters import order_to_dict, to_order

# Kill Switch (phase 0 governance / safety)
from src.risk_layer.kill_switch import KillSwitchLayer, KillSwitchStatus

__all__ = [
    "order_to_dict",
    "to_order",
    "KillSwitchLayer",
    "KillSwitchStatus",
]
