"""Exclusive diagnostic classification for Bollinger/MR economic failure decomposition."""

from __future__ import annotations

from typing import Any, Mapping

from src.research.bollinger_mr_economic_failure_decomposition_development_v1.constants_v1 import (
    DIAGNOSTIC_CLASSES,
)


def _pf_lt_one(pf: float | None) -> bool:
    return pf is None or pf < 1.0


def classify_economic_failure(
    *,
    core: Mapping[str, Any],
    side: Mapping[str, Any],
    cost_stress: list[Mapping[str, Any]],
    concentration: Mapping[str, Any],
) -> dict[str, Any]:
    """Return exactly one diagnostic class with materiality flags (no recommendation)."""
    gross = float(core.get("gross_pnl") or 0.0)
    net = float(core.get("net_pnl") or 0.0)
    gpf = core.get("gross_profit_factor")
    npf = core.get("net_profit_factor")
    trade_count = int(core.get("trade_count") or 0)
    mean_capture = core.get("mean_realized_pnl_over_mfe_capture_ratio")
    mean_leakage = core.get("mean_mfe_to_exit_leakage")
    missing_exc = int(core.get("trades_missing_mfe_mae") or 0)

    long_net = float(side.get("long", {}).get("net_pnl") or 0.0)
    short_net = float(side.get("short", {}).get("net_pnl") or 0.0)
    long_n = int(side.get("long", {}).get("trade_count") or 0)
    short_n = int(side.get("short", {}).get("trade_count") or 0)

    stress_1x = next((r for r in cost_stress if float(r["cost_multiplier"]) == 1.0), None)
    stress_05 = next((r for r in cost_stress if float(r["cost_multiplier"]) == 0.5), None)

    entry_gross_edge_present = bool(gross > 0.0 and (gpf is None or float(gpf) >= 1.0))
    exit_leakage_material = bool(
        entry_gross_edge_present
        and missing_exc == 0
        and mean_capture is not None
        and float(mean_capture) < 0.35
        and mean_leakage is not None
        and float(mean_leakage) > 0.0
    )
    short_side_drag_material = bool(
        short_n > 0
        and short_net < 0.0
        and abs(short_net) >= max(abs(long_net), 1e-12)
        and short_n >= max(long_n, 1)
        and short_net < long_net
    )
    cost_drag_material = bool(
        gross > 0.0
        and net <= 0.0
        and stress_1x is not None
        and float(stress_1x["net_pnl"]) <= 0.0
        and stress_05 is not None
        and float(stress_05["net_pnl"]) <= float(stress_05["gross_pnl"]) * 0.25
    )
    instrument_concentration_material = bool(concentration.get("dominated_by_single") is True)

    flags = {
        "ENTRY_GROSS_EDGE_PRESENT": entry_gross_edge_present,
        "EXIT_LEAKAGE_MATERIAL": exit_leakage_material,
        "SHORT_SIDE_DRAG_MATERIAL": short_side_drag_material,
        "COST_DRAG_MATERIAL": cost_drag_material,
        "INSTRUMENT_CONCENTRATION_MATERIAL": instrument_concentration_material,
    }

    reason_parts: list[str] = []
    diagnostic_class: str

    if trade_count <= 0:
        diagnostic_class = "MIXED_OR_INCONCLUSIVE"
        reason_parts.append("zero_trade_ledger")
    elif instrument_concentration_material and entry_gross_edge_present is False:
        # Concentration alone only if the book is otherwise near-flat except one name.
        # Prefer gross-edge class when the whole book has no gross edge.
        diagnostic_class = "ENTRY_HAS_NO_GROSS_EDGE"
        reason_parts.append("gross_pnl_non_positive_or_gross_pf_below_one")
        if instrument_concentration_material:
            reason_parts.append("instrument_concentration_present_but_not_sole_class")
    elif not entry_gross_edge_present:
        diagnostic_class = "ENTRY_HAS_NO_GROSS_EDGE"
        reason_parts.append("gross_pnl_non_positive_or_gross_pf_below_one")
    elif cost_drag_material:
        diagnostic_class = "COSTS_DESTROY_MARGINAL_EDGE"
        reason_parts.append("positive_gross_destroyed_by_canonical_costs")
    elif short_side_drag_material and long_net >= 0.0:
        diagnostic_class = "SHORT_SIDE_STRUCTURAL_DRAG"
        reason_parts.append("short_book_dominates_net_loss_while_long_non_negative")
    elif exit_leakage_material:
        diagnostic_class = "ENTRY_EDGE_LOST_AT_EXIT"
        reason_parts.append("low_mfe_capture_ratio_with_material_exit_leakage")
    elif instrument_concentration_material:
        diagnostic_class = "INSTRUMENT_CONCENTRATION_ONLY"
        reason_parts.append("single_instrument_dominates_abs_net_pnl")
    else:
        diagnostic_class = "MIXED_OR_INCONCLUSIVE"
        reason_parts.append("no_single_dominant_failure_axis")

    if diagnostic_class not in DIAGNOSTIC_CLASSES:
        diagnostic_class = "MIXED_OR_INCONCLUSIVE"
        reason_parts.append("unknown_class_fallback")

    return {
        "diagnostic_class": diagnostic_class,
        "reason": ";".join(reason_parts),
        "flags": flags,
        "supporting_metrics": {
            "trade_count": trade_count,
            "gross_pnl": gross,
            "net_pnl": net,
            "gross_profit_factor": gpf,
            "net_profit_factor": npf,
            "long_net_pnl": long_net,
            "short_net_pnl": short_net,
            "long_trades": long_n,
            "short_trades": short_n,
            "mean_realized_pnl_over_mfe_capture_ratio": mean_capture,
            "mean_mfe_to_exit_leakage": mean_leakage,
            "worst1_abs_net_share": concentration.get("worst1_abs_net_share"),
            "pf_gross_lt_one": _pf_lt_one(float(gpf) if gpf is not None else None),
        },
        "action_recommendation": None,
        "new_hypothesis": None,
    }
