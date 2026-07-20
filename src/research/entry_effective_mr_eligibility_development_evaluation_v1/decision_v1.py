"""Preregistered PASS/FAIL/INCONCLUSIVE decision for DEVELOPMENT evaluation.

Locked decision thresholds per
``config/research/entry_effective_mr_eligibility_preregistered_economic_hypothesis_measurement_contract_v1.json``.
"""

from __future__ import annotations

from typing import Any, Mapping

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_INCONCLUSIVE = "INCONCLUSIVE"

REASON_TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
REASON_INSUFFICIENT_CONTROL_TRADE_COUNT = "INSUFFICIENT_CONTROL_TRADE_COUNT"
REASON_NO_DIVERGENCE = "identical_arms_no_entry_eligibility_divergence"
REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT = "INSUFFICIENT_TREATMENT_TRADE_COUNT"
REASON_EXCESSIVE_TRADE_COUNT_REDUCTION = "EXCESSIVE_TRADE_COUNT_REDUCTION"
REASON_PROFIT_FACTOR_NOT_IMPROVED = "NET_PROFIT_FACTOR_NOT_IMPROVED"
REASON_MAX_DRAWDOWN_WORSE = "MAX_DRAWDOWN_WORSE"
REASON_NET_RETURN_NOT_IMPROVED = "NET_RETURN_NOT_IMPROVED"
REASON_COST_DRAG_NOT_FULLY_INCLUDED = "COST_DRAG_NOT_FULLY_INCLUDED"
REASON_ALL_PASS_REQUIRES_MET = "ALL_PASS_REQUIRES_MET"
REASON_PASS_REQUIRES_NOT_MET = "PASS_REQUIRES_NOT_MET"


def _as_float(mapping: Mapping[str, Any], key: str) -> float | None:
    value = mapping.get(key)
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _gt_fail_closed(treatment: float | None, control: float | None) -> bool:
    """Strict greater-than; fail-closed (False) if either side is None/NaN."""
    if treatment is None or control is None:
        return False
    return treatment > control


def _ge_fail_closed(treatment: float | None, control: float | None) -> bool:
    """Greater-than-or-equal; fail-closed (False) if either side is None/NaN."""
    if treatment is None or control is None:
        return False
    return treatment >= control


def decide_development_evaluation(
    *,
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
    entry_eligibility_divergence_observed: bool,
    minimum_trade_count: int = 50,
    max_trade_count_reduction_fraction: float = 0.5,
    cost_drag_fully_included: bool = True,
    technical_failure: bool = False,
) -> dict[str, Any]:
    """Apply locked decision thresholds from the preregistration contract.

    ``baseline`` is the control arm (unfiltered canonical baseline); ``treatment``
    is the entry-effective ATR-percentile eligibility gated arm. Both are
    metrics mappings using the shared aggregate keys ``trade_count``,
    ``net_return``, ``max_drawdown``, ``profit_factor``.
    """
    bt_control = int(baseline.get("trade_count") or 0)
    tt_treatment = int(treatment.get("trade_count") or 0)

    pf_control = _as_float(baseline, "profit_factor")
    pf_treatment = _as_float(treatment, "profit_factor")
    dd_control = _as_float(baseline, "max_drawdown")
    dd_treatment = _as_float(treatment, "max_drawdown")
    ret_control = _as_float(baseline, "net_return")
    ret_treatment = _as_float(treatment, "net_return")

    divergence = bool(entry_eligibility_divergence_observed)

    common: dict[str, Any] = {
        "minimum_trade_count": int(minimum_trade_count),
        "max_trade_count_reduction_fraction": float(max_trade_count_reduction_fraction),
        "cost_drag_fully_included_flag": bool(cost_drag_fully_included),
        "entry_eligibility_divergence_observed": divergence,
        "control_trade_count": bt_control,
        "treatment_trade_count": tt_treatment,
        "control_profit_factor": pf_control,
        "treatment_profit_factor": pf_treatment,
        "control_max_drawdown": dd_control,
        "treatment_max_drawdown": dd_treatment,
        "control_net_return": ret_control,
        "treatment_net_return": ret_treatment,
        "technical_failure": bool(technical_failure),
    }

    # Rule 0: technical failure is always INCONCLUSIVE, never a proxy for
    # poor economics.
    if technical_failure:
        return {
            **common,
            "result_class": RESULT_INCONCLUSIVE,
            "reason": REASON_TECHNICAL_FAILURE,
            "checks": {},
            "evaluable": False,
        }

    # Rule 1: insufficient control (baseline) trade count => INCONCLUSIVE.
    # Never INCONCLUSIVE for poor economics alone.
    if bt_control < int(minimum_trade_count):
        return {
            **common,
            "result_class": RESULT_INCONCLUSIVE,
            "reason": REASON_INSUFFICIENT_CONTROL_TRADE_COUNT,
            "checks": {},
            "evaluable": False,
        }

    evaluable = True

    checks = {
        "entry_eligibility_divergence_observed": divergence,
        "trade_count_treatment_ge_minimum": tt_treatment >= int(minimum_trade_count),
        "trade_count_treatment_ge_control_floor": float(tt_treatment)
        >= float(bt_control) * (1.0 - float(max_trade_count_reduction_fraction)),
        "profit_factor_treatment_gt_control": _gt_fail_closed(pf_treatment, pf_control),
        "max_drawdown_treatment_ge_control": _ge_fail_closed(dd_treatment, dd_control),
        "net_return_treatment_gt_control": _gt_fail_closed(ret_treatment, ret_control),
        "cost_drag_fully_included": bool(cost_drag_fully_included),
    }

    # Rule 2: identical-arms (no observed entry-eligibility divergence) is a
    # hard FAIL, independent of how favorable the economics otherwise look.
    if not divergence:
        result_class = RESULT_FAIL
        reason = REASON_NO_DIVERGENCE
    elif all(checks.values()):
        result_class = RESULT_PASS
        reason = REASON_ALL_PASS_REQUIRES_MET
    else:
        result_class = RESULT_FAIL
        if not checks["trade_count_treatment_ge_minimum"]:
            reason = REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT
        elif not checks["trade_count_treatment_ge_control_floor"]:
            reason = REASON_EXCESSIVE_TRADE_COUNT_REDUCTION
        elif not checks["profit_factor_treatment_gt_control"]:
            reason = REASON_PROFIT_FACTOR_NOT_IMPROVED
        elif not checks["max_drawdown_treatment_ge_control"]:
            reason = REASON_MAX_DRAWDOWN_WORSE
        elif not checks["net_return_treatment_gt_control"]:
            reason = REASON_NET_RETURN_NOT_IMPROVED
        elif not checks["cost_drag_fully_included"]:
            reason = REASON_COST_DRAG_NOT_FULLY_INCLUDED
        else:
            reason = REASON_PASS_REQUIRES_NOT_MET

    return {
        **common,
        "result_class": result_class,
        "reason": reason,
        "checks": checks,
        "evaluable": evaluable,
    }


__all__ = [
    "REASON_ALL_PASS_REQUIRES_MET",
    "REASON_COST_DRAG_NOT_FULLY_INCLUDED",
    "REASON_EXCESSIVE_TRADE_COUNT_REDUCTION",
    "REASON_INSUFFICIENT_CONTROL_TRADE_COUNT",
    "REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT",
    "REASON_MAX_DRAWDOWN_WORSE",
    "REASON_NET_RETURN_NOT_IMPROVED",
    "REASON_NO_DIVERGENCE",
    "REASON_PASS_REQUIRES_NOT_MET",
    "REASON_PROFIT_FACTOR_NOT_IMPROVED",
    "REASON_TECHNICAL_FAILURE",
    "RESULT_FAIL",
    "RESULT_INCONCLUSIVE",
    "RESULT_PASS",
    "decide_development_evaluation",
]
