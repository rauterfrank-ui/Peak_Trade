"""Preregistered PASS/FAIL/INCONCLUSIVE decision for DEVELOPMENT evaluation."""

from __future__ import annotations

from typing import Any, Mapping


def decide_development_evaluation(
    *,
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
    minimum_trade_count: int,
    materiality_epsilon_net_return_abs: float,
) -> dict[str, Any]:
    """Apply locked decision thresholds from the preregistration contract."""
    bt = int(baseline.get("trade_count") or 0)
    tt = int(treatment.get("trade_count") or 0)
    b_ret = float(baseline["net_return"])
    t_ret = float(treatment["net_return"])
    b_dd = float(baseline["max_drawdown"])
    t_dd = float(treatment["max_drawdown"])
    b_to = float(baseline["turnover"])
    t_to = float(treatment["turnover"])
    b_cd = float(baseline["cost_drag"])
    t_cd = float(treatment["cost_drag"])

    checks = {
        "trade_count_treatment_ge_minimum": tt >= minimum_trade_count,
        "trade_count_baseline_ge_minimum": bt >= minimum_trade_count,
        "max_drawdown_treatment_ge_baseline": t_dd >= b_dd,
        "turnover_treatment_lt_baseline": t_to < b_to,
        "cost_drag_treatment_lt_baseline": t_cd < b_cd,
        "net_return_treatment_ge_baseline_minus_eps": t_ret
        >= (b_ret - materiality_epsilon_net_return_abs),
    }

    if bt < minimum_trade_count or tt < minimum_trade_count:
        result_class = "INCONCLUSIVE"
        reason = "INSUFFICIENT_TRADE_COUNT"
    elif tt >= minimum_trade_count and t_ret < (b_ret - materiality_epsilon_net_return_abs):
        result_class = "FAIL"
        reason = "NET_RETURN_MATERIAL_WORSE"
    elif tt >= minimum_trade_count and t_dd < b_dd:
        result_class = "FAIL"
        reason = "MAX_DRAWDOWN_WORSE"
    elif all(
        [
            checks["trade_count_treatment_ge_minimum"],
            checks["max_drawdown_treatment_ge_baseline"],
            checks["turnover_treatment_lt_baseline"],
            checks["cost_drag_treatment_lt_baseline"],
            checks["net_return_treatment_ge_baseline_minus_eps"],
        ]
    ):
        result_class = "PASS"
        reason = "ALL_PASS_REQUIRES_MET"
    else:
        result_class = "FAIL"
        reason = "PASS_REQUIRES_NOT_MET"

    return {
        "result_class": result_class,
        "reason": reason,
        "checks": checks,
        "minimum_trade_count": minimum_trade_count,
        "materiality_epsilon_net_return_abs": materiality_epsilon_net_return_abs,
        "baseline_trade_count": bt,
        "treatment_trade_count": tt,
        "baseline_net_return": b_ret,
        "treatment_net_return": t_ret,
        "baseline_max_drawdown": b_dd,
        "treatment_max_drawdown": t_dd,
        "baseline_turnover": b_to,
        "treatment_turnover": t_to,
        "baseline_cost_drag": b_cd,
        "treatment_cost_drag": t_cd,
    }


__all__ = ["decide_development_evaluation"]
