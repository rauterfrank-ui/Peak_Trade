"""V7 decision helper bound to Operator Clarification Authority + immutable prereg.

Does not mutate the preregistration. B1–B6 executable semantics come from the
clarification authority overlay. Economic targets remain those registered in prereg.
"""

from __future__ import annotations

from typing import Any, Mapping

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_INVALID_IDENTICAL_ARMS = "INVALID_MEASUREMENT_IDENTICAL_ARMS"
RESULT_INVALID_BINDING = "INVALID_MEASUREMENT_BINDING_MISSING"
RESULT_INVALID_CONFIGS = "INVALID_MEASUREMENT_IDENTICAL_EFFECTIVE_CONFIGS"
RESULT_INVALID_NO_EXIT = "INVALID_MEASUREMENT_NO_EXIT_OBSERVABILITY"
RESULT_INCONCLUSIVE_INFRA = "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"

REASON_ALL_PASS_REQUIRES_MET = "ALL_PASS_REQUIRES_MET"
REASON_NET_RETURN_NOT_IMPROVED = "NET_RETURN_NOT_IMPROVED"
REASON_NET_PROFIT_FACTOR_NOT_IMPROVED = "NET_PROFIT_FACTOR_NOT_IMPROVED"
REASON_COST_DRAG_NOT_IMPROVED = "COST_DRAG_NOT_IMPROVED"
REASON_SHORT_TRADE_COUNT_NOT_REDUCED = "SHORT_TRADE_COUNT_NOT_REDUCED"
REASON_EXCESSIVE_TRADE_COUNT_REDUCTION = "EXCESSIVE_TRADE_COUNT_REDUCTION"
REASON_LONG_NET_PNL_DEGRADED = "LONG_NET_PNL_DEGRADED"
REASON_MAX_DRAWDOWN_WORSENED = "MAX_DRAWDOWN_WORSENED"
REASON_MAX_DRAWDOWN_REPRESENTATION_INVALID = "MAX_DRAWDOWN_POSITIVE_MAGNITUDE_FORBIDDEN"
REASON_PASS_REQUIRES_NOT_MET = "PASS_REQUIRES_NOT_MET"
REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT = "INSUFFICIENT_TREATMENT_TRADE_COUNT"
REASON_NEW_INSTRUMENT_CONCENTRATION = "NEW_INSTRUMENT_CONCENTRATION"
REASON_COST_MULTIPLIER_INVALID = "COST_MULTIPLIER_INVALID"
REASON_EXIT_FILLS_NOT_IDENTICAL = "EXIT_FILLS_NOT_IDENTICAL_INVALIDATES_V7_MEASUREMENT"
REASON_AUTHORITY_BINDING_MISSING = "OPERATOR_CLARIFICATION_AUTHORITY_BINDING_MISSING"
REASON_INFRA_INCOMPLETE = "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"


def _as_float(mapping: Mapping[str, Any], key: str) -> float | None:
    value = mapping.get(key)
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:
        return None
    return f


def _signed_max_drawdown_ok(control_dd: float, treatment_dd: float) -> tuple[bool, str | None]:
    """B2: signed negative returns; fail-closed on positive magnitudes."""
    if control_dd > 0.0 or treatment_dd > 0.0:
        return False, REASON_MAX_DRAWDOWN_REPRESENTATION_INVALID
    # treatment >= control (less negative or equal is better/tie)
    if treatment_dd + 0.0 < control_dd:
        return False, REASON_MAX_DRAWDOWN_WORSENED
    return True, None


def decide_development_evaluation_v7(
    *,
    control: Mapping[str, Any],
    treatment: Mapping[str, Any],
    reentry_divergence_observed: bool,
    exit_fills_identical: bool | None,
    effective_configs_differ: bool,
    open_side_binding_observed: bool,
    exit_bars_observed: int,
    forced_midband_exit_count: int,
    cooldown_activation_count: int,
    blocked_same_side_reentry_count: int,
    authority_binding_ok: bool,
    control_treatment_isolation_ok: bool = True,
    minimum_trade_count: int = 20,
    max_trade_count_reduction_fraction: float = 0.5,
    instrument_concentration_worst1_max: float = 0.35,
    cost_multiplier_treatment: float = 1.0,
    cost_assumption_below_canonical_1x: bool = False,
    cost_drag_fully_included: bool = True,
    infrastructure_failure: bool = False,
    infrastructure_diagnostic_class: str = "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL",
    # Legacy unused; B1 clarification supersedes prereg exit-divergence execution.
    exit_divergence_observed: bool | None = None,
) -> dict[str, Any]:
    """Apply clarification-bound V7 decision order; never convert INVALID to FAIL."""
    _ = exit_divergence_observed  # retained for call-site compatibility only

    if infrastructure_failure:
        return {
            "result_class": RESULT_INCONCLUSIVE_INFRA,
            "reason": REASON_INFRA_INCOMPLETE,
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "diagnostic_class": infrastructure_diagnostic_class,
            "lifecycle_terminal_state": (
                "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
            ),
            "partial_metrics_authoritative": False,
            "auto_rerun_allowed": False,
            "checks": {},
        }

    # 1. Contract/Authority binding
    if not authority_binding_ok:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": REASON_AUTHORITY_BINDING_MISSING,
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }

    # 2–3. Measurement validity + isolation
    if not control_treatment_isolation_ok:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": "control_treatment_isolation_failed",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }
    if not effective_configs_differ:
        return {
            "result_class": RESULT_INVALID_CONFIGS,
            "reason": "identical_effective_config_digests",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }
    if not open_side_binding_observed:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": "open_side_binding_missing",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }
    if int(exit_bars_observed) <= 0:
        return {
            "result_class": RESULT_INVALID_NO_EXIT,
            "reason": "no_exit_observability",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }
    if int(forced_midband_exit_count) < 1 or int(cooldown_activation_count) < 1:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": "cooldown_or_forced_midband_binding_missing",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }

    # 4. Exit-fill identity (B1): must be identical; divergence invalidates measurement
    if exit_fills_identical is not True:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": REASON_EXIT_FILLS_NOT_IDENTICAL,
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {"exit_fills_identical": exit_fills_identical},
        }

    # 5. Reentry divergence (B1)
    if int(blocked_same_side_reentry_count) < 1 and not reentry_divergence_observed:
        return {
            "result_class": RESULT_INVALID_IDENTICAL_ARMS,
            "reason": "INVALID_MEASUREMENT_IDENTICAL_ARMS",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {
                "reentry_divergence_observed": False,
                "blocked_same_side_reentry_count": int(blocked_same_side_reentry_count),
            },
        }

    # 6–10. Full metrics after measurement validity
    trade_c = int(control.get("trade_count") or 0)
    trade_t = int(treatment.get("trade_count") or 0)
    if trade_t < int(minimum_trade_count):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_INSUFFICIENT_TREATMENT_TRADE_COUNT,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"trade_count_treatment": trade_t},
        }
    if trade_c > 0 and trade_t < float(max_trade_count_reduction_fraction) * float(trade_c):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_EXCESSIVE_TRADE_COUNT_REDUCTION,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"trade_count_control": trade_c, "trade_count_treatment": trade_t},
        }

    if cost_assumption_below_canonical_1x or float(cost_multiplier_treatment) != 1.0:
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_COST_MULTIPLIER_INVALID,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {},
        }
    if not cost_drag_fully_included:
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_PASS_REQUIRES_NOT_MET,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"cost_drag_fully_included": False},
        }

    worst1 = _as_float(treatment, "worst1_abs_net_share")
    if worst1 is not None and worst1 > float(instrument_concentration_worst1_max):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_NEW_INSTRUMENT_CONCENTRATION,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"worst1_abs_net_share": worst1},
        }

    nr_c = _as_float(control, "net_return")
    nr_t = _as_float(treatment, "net_return")
    if nr_c is None:
        nr_c = _as_float(control, "net_return_after_costs")
    if nr_t is None:
        nr_t = _as_float(treatment, "net_return_after_costs")
    if nr_c is None or nr_t is None or not (nr_t > nr_c):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_NET_RETURN_NOT_IMPROVED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"control_net_return": nr_c, "treatment_net_return": nr_t},
        }

    # 7. PF: treatment >= control (B7)
    pf_c = _as_float(control, "net_profit_factor")
    pf_t = _as_float(treatment, "net_profit_factor")
    if pf_c is None or pf_t is None or not (pf_t >= pf_c):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_NET_PROFIT_FACTOR_NOT_IMPROVED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"control_net_profit_factor": pf_c, "treatment_net_profit_factor": pf_t},
        }

    cd_c = _as_float(control, "cost_drag")
    cd_t = _as_float(treatment, "cost_drag")
    if cd_c is None or cd_t is None or not (cd_t < cd_c):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_COST_DRAG_NOT_IMPROVED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"control_cost_drag": cd_c, "treatment_cost_drag": cd_t},
        }

    short_c = int(control.get("short_trade_count") or control.get("short_trades") or 0)
    short_t = int(treatment.get("short_trade_count") or treatment.get("short_trades") or 0)
    if not (short_t < short_c):
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_SHORT_TRADE_COUNT_NOT_REDUCED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {
                "control_short_trade_count": short_c,
                "treatment_short_trade_count": short_t,
            },
        }

    long_c = _as_float(control, "long_net_pnl")
    long_t = _as_float(treatment, "long_net_pnl")
    if long_c is not None and long_t is not None and (long_t - long_c) < -1e-12:
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_LONG_NET_PNL_DEGRADED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"control_long_net_pnl": long_c, "treatment_long_net_pnl": long_t},
        }

    # 9. MaxDD: treatment >= control (B2 signed)
    dd_c = _as_float(control, "max_drawdown")
    dd_t = _as_float(treatment, "max_drawdown")
    if dd_c is None or dd_t is None:
        return {
            "result_class": RESULT_INVALID_BINDING,
            "reason": "max_drawdown_missing",
            "evaluable": False,
            "economic_verdict": "NOT_EVALUATED",
            "checks": {},
        }
    dd_ok, dd_reason = _signed_max_drawdown_ok(dd_c, dd_t)
    if not dd_ok:
        if dd_reason == REASON_MAX_DRAWDOWN_REPRESENTATION_INVALID:
            return {
                "result_class": RESULT_INVALID_BINDING,
                "reason": dd_reason,
                "evaluable": False,
                "economic_verdict": "NOT_EVALUATED",
                "checks": {"control_max_drawdown": dd_c, "treatment_max_drawdown": dd_t},
            }
        return {
            "result_class": RESULT_FAIL,
            "reason": REASON_MAX_DRAWDOWN_WORSENED,
            "evaluable": True,
            "economic_verdict": "FAIL",
            "checks": {"control_max_drawdown": dd_c, "treatment_max_drawdown": dd_t},
        }

    return {
        "result_class": RESULT_PASS,
        "reason": REASON_ALL_PASS_REQUIRES_MET,
        "evaluable": True,
        "economic_verdict": "PASS",
        "checks": {
            "exit_fills_identical": True,
            "reentry_divergence_observed": True,
            "net_profit_factor_operator": ">=",
            "max_drawdown_operator": "treatment >= control (signed negative)",
            "control_net_return": nr_c,
            "treatment_net_return": nr_t,
            "control_net_profit_factor": pf_c,
            "treatment_net_profit_factor": pf_t,
            "control_max_drawdown": dd_c,
            "treatment_max_drawdown": dd_t,
            "blocked_same_side_reentry_count": int(blocked_same_side_reentry_count),
        },
    }


__all__ = [
    "RESULT_PASS",
    "RESULT_FAIL",
    "RESULT_INCONCLUSIVE_INFRA",
    "RESULT_INVALID_IDENTICAL_ARMS",
    "decide_development_evaluation_v7",
]
