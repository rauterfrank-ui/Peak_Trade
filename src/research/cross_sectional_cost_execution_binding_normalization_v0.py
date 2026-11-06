"""Canonical cost-execution-binding normalization for single-slot backtest wiring v0.

Maps ratified fee_binding/slippage_binding aliases to fee_model_binding/slippage_model_binding
expected by run_single_slot_panel_backtest_v0. Research-only; no runtime or authority effect.
"""

from __future__ import annotations

from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_COST_EXECUTION_BINDING_NORMALIZATION_V0=true"
NORMALIZATION_VERSION = "cross_sectional_cost_execution_binding_normalization.v0"


def normalize_cost_execution_binding_for_backtest_v0(
    cost_execution_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Return backtest-ready cost binding without mutating ratified cost values."""
    if "fee_model_binding" in cost_execution_binding:
        return dict(cost_execution_binding)
    return {
        **dict(cost_execution_binding),
        "fee_model_binding": cost_execution_binding.get("fee_binding", {}),
        "slippage_model_binding": cost_execution_binding.get("slippage_binding", {}),
        "funding_model_binding": cost_execution_binding.get("funding_binding", {}),
    }


__all__ = [
    "NORMALIZATION_VERSION",
    "PACKAGE_MARKER",
    "normalize_cost_execution_binding_for_backtest_v0",
]
