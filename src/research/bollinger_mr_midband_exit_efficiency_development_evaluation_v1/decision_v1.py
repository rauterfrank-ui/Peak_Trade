"""Preregistered PASS/FAIL/INCONCLUSIVE decision for midband exit-efficiency DEVELOPMENT run.

Implements frozen pass_requires_all from the midband measurement contract.
INCONCLUSIVE never for poor economics alone.
"""

from __future__ import annotations

from typing import Any, Mapping

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_INCONCLUSIVE = "INCONCLUSIVE"

REASON_TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
REASON_INSUFFICIENT_CONTROL_TRADE_COUNT = "INSUFFICIENT_CONTROL_TRADE_COUNT"
REASON_NO_EXIT_DIVERGENCE = "identical_arms_no_exit_divergence"
REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT = "INSUFFICIENT_TREATMENT_TRADE_COUNT"
REASON_EXCESSIVE_TRADE_COUNT_REDUCTION = "EXCESSIVE_TRADE_COUNT_REDUCTION"
REASON_NET_PROFIT_FACTOR_NOT_IMPROVED = "NET_PROFIT_FACTOR_NOT_IMPROVED"
REASON_NET_PNL_NOT_IMPROVED = "NET_PNL_NOT_IMPROVED"
REASON_NET_RETURN_NOT_IMPROVED = "NET_RETURN_NOT_IMPROVED"
REASON_MFE_CAPTURE_NOT_IMPROVED = "MFE_CAPTURE_NOT_IMPROVED"
REASON_MFE_LEAKAGE_NOT_REDUCED = "MFE_LEAKAGE_NOT_REDUCED"
REASON_IMPROVEMENT_SOLELY_TRADE_COUNT_OR_TURNOVER = (
    "IMPROVEMENT_SOLELY_EXPLAINED_BY_REDUCED_TRADE_COUNT_OR_ARTIFICIALLY_LOWER_TURNOVER"
)
REASON_NEW_INSTRUMENT_CONCENTRATION = "NEW_INSTRUMENT_CONCENTRATION"
REASON_COST_MULTIPLIER_INVALID = "COST_MULTIPLIER_INVALID"
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


def _gt(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return False
    return a > b


def _lt(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return False
    return a < b


def decide_development_evaluation(
    *,
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
    exit_divergence_observed: bool,
    minimum_trade_count: int = 20,
    max_trade_count_reduction_fraction: float = 0.5,
    instrument_concentration_worst1_max: float = 0.35,
    cost_multiplier_treatment: float = 1.0,
    cost_assumption_below_canonical_1x: bool = False,
    cost_drag_fully_included: bool = True,
    technical_failure: bool = False,
) -> dict[str, Any]:
    bt_c = int(baseline.get("trade_count") or 0)
    bt_t = int(treatment.get("trade_count") or 0)
    pf_c = _as_float(baseline, "net_profit_factor")
    if pf_c is None:
        pf_c = _as_float(baseline, "profit_factor")
    pf_t = _as_float(treatment, "net_profit_factor")
    if pf_t is None:
        pf_t = _as_float(treatment, "profit_factor")
    pnl_c = _as_float(baseline, "net_pnl")
    pnl_t = _as_float(treatment, "net_pnl")
    ret_c = _as_float(baseline, "net_return")
    ret_t = _as_float(treatment, "net_return")
    cap_c = _as_float(baseline, "mean_realized_pnl_over_mfe_capture_ratio")
    cap_t = _as_float(treatment, "mean_realized_pnl_over_mfe_capture_ratio")
    leak_c = _as_float(baseline, "mean_mfe_to_exit_leakage")
    leak_t = _as_float(treatment, "mean_mfe_to_exit_leakage")
    turn_c = _as_float(baseline, "turnover")
    turn_t = _as_float(treatment, "turnover")
    conc_c = _as_float(baseline, "worst1_abs_net_share")
    conc_t = _as_float(treatment, "worst1_abs_net_share")

    divergence = bool(exit_divergence_observed)
    common: dict[str, Any] = {
        "minimum_trade_count": int(minimum_trade_count),
        "max_trade_count_reduction_fraction": float(max_trade_count_reduction_fraction),
        "exit_divergence_observed": divergence,
        "control_trade_count": bt_c,
        "treatment_trade_count": bt_t,
        "control_net_profit_factor": pf_c,
        "treatment_net_profit_factor": pf_t,
        "control_net_pnl": pnl_c,
        "treatment_net_pnl": pnl_t,
        "control_net_return": ret_c,
        "treatment_net_return": ret_t,
        "control_mean_realized_pnl_over_mfe_capture_ratio": cap_c,
        "treatment_mean_realized_pnl_over_mfe_capture_ratio": cap_t,
        "control_mean_mfe_to_exit_leakage": leak_c,
        "treatment_mean_mfe_to_exit_leakage": leak_t,
        "control_worst1_abs_net_share": conc_c,
        "treatment_worst1_abs_net_share": conc_t,
        "cost_multiplier_treatment": float(cost_multiplier_treatment),
        "cost_assumption_below_canonical_1x": bool(cost_assumption_below_canonical_1x),
        "cost_drag_fully_included": bool(cost_drag_fully_included),
        "technical_failure": bool(technical_failure),
    }

    if technical_failure:
        return {
            **common,
            "result_class": RESULT_INCONCLUSIVE,
            "reason": REASON_TECHNICAL_FAILURE,
            "checks": {},
            "evaluable": False,
        }

    if bt_c < int(minimum_trade_count):
        return {
            **common,
            "result_class": RESULT_INCONCLUSIVE,
            "reason": REASON_INSUFFICIENT_CONTROL_TRADE_COUNT,
            "checks": {},
            "evaluable": False,
        }

    trade_floor = float(bt_c) * (1.0 - float(max_trade_count_reduction_fraction))
    capture_improved = _gt(cap_t, cap_c)
    leakage_reduced = _lt(leak_t, leak_c)
    trade_count_reduced = bt_t < bt_c
    turnover_reduced = turn_t is not None and turn_c is not None and turn_t < turn_c
    solely_explained = bool(
        trade_count_reduced and turnover_reduced and not (capture_improved and leakage_reduced)
    )
    no_new_concentration = conc_t is not None and conc_t <= float(
        instrument_concentration_worst1_max
    )
    if (
        conc_c is not None
        and conc_t is not None
        and conc_t > conc_c
        and conc_t > float(instrument_concentration_worst1_max)
    ):
        no_new_concentration = False

    checks = {
        "exit_divergence_observed": divergence,
        "trade_count_treatment_ge_minimum": bt_t >= int(minimum_trade_count),
        "trade_count_treatment_ge_control_floor": float(bt_t) >= trade_floor,
        "net_profit_factor_treatment_gt_control": _gt(pf_t, pf_c),
        "net_pnl_treatment_gt_control": _gt(pnl_t, pnl_c),
        "net_return_treatment_gt_control": _gt(ret_t, ret_c),
        "mean_realized_pnl_over_mfe_capture_ratio_treatment_gt_control": capture_improved,
        "mean_mfe_to_exit_leakage_treatment_lt_control": leakage_reduced,
        "improvement_not_solely_explained_by_reduced_trade_count_or_artificially_lower_turnover": (
            not solely_explained
        ),
        "no_new_instrument_concentration": bool(no_new_concentration),
        "cost_multiplier_treatment_eq_1": float(cost_multiplier_treatment) == 1.0,
        "cost_assumption_below_canonical_1x_false": cost_assumption_below_canonical_1x is False,
        "cost_drag_fully_included": bool(cost_drag_fully_included),
    }

    if not divergence:
        result_class = RESULT_FAIL
        reason = REASON_NO_EXIT_DIVERGENCE
    elif all(checks.values()):
        result_class = RESULT_PASS
        reason = REASON_ALL_PASS_REQUIRES_MET
    else:
        result_class = RESULT_FAIL
        if not checks["trade_count_treatment_ge_minimum"]:
            reason = REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT
        elif not checks["trade_count_treatment_ge_control_floor"]:
            reason = REASON_EXCESSIVE_TRADE_COUNT_REDUCTION
        elif not checks["net_profit_factor_treatment_gt_control"]:
            reason = REASON_NET_PROFIT_FACTOR_NOT_IMPROVED
        elif not checks["net_pnl_treatment_gt_control"]:
            reason = REASON_NET_PNL_NOT_IMPROVED
        elif not checks["net_return_treatment_gt_control"]:
            reason = REASON_NET_RETURN_NOT_IMPROVED
        elif not checks["mean_realized_pnl_over_mfe_capture_ratio_treatment_gt_control"]:
            reason = REASON_MFE_CAPTURE_NOT_IMPROVED
        elif not checks["mean_mfe_to_exit_leakage_treatment_lt_control"]:
            reason = REASON_MFE_LEAKAGE_NOT_REDUCED
        elif not checks[
            "improvement_not_solely_explained_by_reduced_trade_count_or_artificially_lower_turnover"
        ]:
            reason = REASON_IMPROVEMENT_SOLELY_TRADE_COUNT_OR_TURNOVER
        elif not checks["no_new_instrument_concentration"]:
            reason = REASON_NEW_INSTRUMENT_CONCENTRATION
        elif (
            not checks["cost_multiplier_treatment_eq_1"]
            or not checks["cost_assumption_below_canonical_1x_false"]
        ):
            reason = REASON_COST_MULTIPLIER_INVALID
        else:
            reason = REASON_PASS_REQUIRES_NOT_MET

    return {
        **common,
        "result_class": result_class,
        "reason": reason,
        "checks": checks,
        "evaluable": True,
    }


__all__ = [
    "REASON_ALL_PASS_REQUIRES_MET",
    "REASON_COST_MULTIPLIER_INVALID",
    "REASON_EXCESSIVE_TRADE_COUNT_REDUCTION",
    "REASON_IMPROVEMENT_SOLELY_TRADE_COUNT_OR_TURNOVER",
    "REASON_INSUFFICIENT_CONTROL_TRADE_COUNT",
    "REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT",
    "REASON_MFE_CAPTURE_NOT_IMPROVED",
    "REASON_MFE_LEAKAGE_NOT_REDUCED",
    "REASON_NET_PNL_NOT_IMPROVED",
    "REASON_NET_PROFIT_FACTOR_NOT_IMPROVED",
    "REASON_NET_RETURN_NOT_IMPROVED",
    "REASON_NEW_INSTRUMENT_CONCENTRATION",
    "REASON_NO_EXIT_DIVERGENCE",
    "REASON_PASS_REQUIRES_NOT_MET",
    "REASON_TECHNICAL_FAILURE",
    "RESULT_FAIL",
    "RESULT_INCONCLUSIVE",
    "RESULT_PASS",
    "decide_development_evaluation",
]
