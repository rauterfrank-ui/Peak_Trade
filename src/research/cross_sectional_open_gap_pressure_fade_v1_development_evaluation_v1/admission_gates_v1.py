"""Admission gates for CS open-gap pressure fade v1 development evaluation.

Applies preregistered measurement-contract thresholds only. Does not invent or
lower thresholds. Pure functions over already-computed metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_gap_pressure_fade_v1_development_evaluation_v1.constants_v1 import (
    MINIMUM_PASSING_SEGMENTS,
    MINIMUM_REBALANCE_OBSERVATIONS,
    TIME_SEGMENT_COUNT,
    TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
)


@dataclass(frozen=True)
class GateResultV1:
    gate_id: str
    passed: bool
    reason_code: str | None
    observed: Any
    threshold: Any


@dataclass(frozen=True)
class AdmissionGateBundleV1:
    sample_sufficiency: GateResultV1
    gross_edge: GateResultV1
    canonical_cost: GateResultV1
    cost_stress: GateResultV1
    max_drawdown: GateResultV1
    time_segment_robustness: GateResultV1
    all_segments_evaluable: GateResultV1
    trade_sample: GateResultV1

    @property
    def all_pass(self) -> bool:
        return all(
            g.passed
            for g in (
                self.sample_sufficiency,
                self.gross_edge,
                self.canonical_cost,
                self.cost_stress,
                self.max_drawdown,
                self.time_segment_robustness,
                self.all_segments_evaluable,
                self.trade_sample,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        def _one(g: GateResultV1) -> dict[str, Any]:
            return {
                "gate_id": g.gate_id,
                "passed": g.passed,
                "reason_code": g.reason_code,
                "observed": g.observed,
                "threshold": g.threshold,
            }

        return {
            "sample_sufficiency": _one(self.sample_sufficiency),
            "gross_edge": _one(self.gross_edge),
            "canonical_cost": _one(self.canonical_cost),
            "cost_stress": _one(self.cost_stress),
            "max_drawdown": _one(self.max_drawdown),
            "time_segment_robustness": _one(self.time_segment_robustness),
            "all_segments_evaluable": _one(self.all_segments_evaluable),
            "trade_sample": _one(self.trade_sample),
            "all_pass": self.all_pass,
        }


def _thresholds_from_contract(contract: Mapping[str, Any]) -> dict[str, float | int]:
    thr = (contract.get("economic_admission_contract") or {}).get("thresholds") or {}
    return {
        "minimum_rebalance_observations": int(thr["minimum_rebalance_observations"]["value"]),
        "time_segment_robustness_pass_ratio": float(
            thr["time_segment_robustness_pass_ratio"]["value"]
        ),
        "gross_profit_factor_min": float(thr["gross_profit_factor_min"]["value"]),
        "net_profit_factor_min": float(thr["net_profit_factor_min"]["value"]),
        "cost_stress_1_5x_net_profit_factor_min": float(
            thr["cost_stress_1_5x_net_profit_factor_min"]["value"]
        ),
        "maximum_max_drawdown": float(thr["maximum_max_drawdown"]["value"]),
        "minimum_trade_count": int(thr["minimum_trade_count"]["value"]),
        "minimum_net_expectancy": float(thr["minimum_net_expectancy"]["value"]),
        "single_trade_dominance_limit": float(thr["single_trade_dominance_limit"]["value"]),
        "min_eligible_members_for_rank": int(thr["min_eligible_members_for_rank"]["value"]),
    }


def evaluate_admission_gates_v1(
    *,
    contract: Mapping[str, Any],
    valid_rebalance_observations: int,
    gross_profit_factor: float,
    gross_pnl: float,
    net_profit_factor: float,
    net_expectancy: float,
    max_drawdown: float,
    cost_stress_1_5x_net_profit_factor: float,
    trade_count: int,
    segment_results: Sequence[Mapping[str, Any]],
    worst1_abs_net_share: float | None = None,
) -> AdmissionGateBundleV1:
    """Evaluate preregistered admission gates. Thresholds come from measurement contract."""
    thr = _thresholds_from_contract(contract)
    assert thr["minimum_rebalance_observations"] == MINIMUM_REBALANCE_OBSERVATIONS
    assert thr["time_segment_robustness_pass_ratio"] == TIME_SEGMENT_ROBUSTNESS_PASS_RATIO

    sample_ok = valid_rebalance_observations >= int(thr["minimum_rebalance_observations"])
    sample = GateResultV1(
        gate_id="SAMPLE_SUFFICIENCY",
        passed=sample_ok,
        reason_code=None if sample_ok else "INSUFFICIENT_REBALANCE_OBSERVATIONS",
        observed=valid_rebalance_observations,
        threshold=thr["minimum_rebalance_observations"],
    )

    gross_ok = gross_profit_factor >= float(thr["gross_profit_factor_min"]) and gross_pnl > 0.0
    gross = GateResultV1(
        gate_id="GROSS_EDGE",
        passed=gross_ok,
        reason_code=None if gross_ok else "GROSS_EDGE_NOT_MEANINGFUL",
        observed={"gross_profit_factor": gross_profit_factor, "gross_pnl": gross_pnl},
        threshold={"gross_profit_factor_min": thr["gross_profit_factor_min"], "gross_pnl_gt": 0.0},
    )

    cost_ok = net_profit_factor >= float(thr["net_profit_factor_min"]) and net_expectancy >= float(
        thr["minimum_net_expectancy"]
    )
    if worst1_abs_net_share is not None:
        cost_ok = cost_ok and worst1_abs_net_share <= float(thr["single_trade_dominance_limit"])
    canonical_cost = GateResultV1(
        gate_id="CANONICAL_COST",
        passed=cost_ok,
        reason_code=None if cost_ok else "NET_PROFIT_FACTOR_BELOW_THRESHOLD",
        observed={
            "net_profit_factor": net_profit_factor,
            "net_expectancy": net_expectancy,
            "worst1_abs_net_share": worst1_abs_net_share,
            "canonical_cost_multiplier": 1.0,
        },
        threshold={
            "net_profit_factor_min": thr["net_profit_factor_min"],
            "minimum_net_expectancy": thr["minimum_net_expectancy"],
            "single_trade_dominance_limit": thr["single_trade_dominance_limit"],
        },
    )

    stress_ok = cost_stress_1_5x_net_profit_factor >= float(
        thr["cost_stress_1_5x_net_profit_factor_min"]
    )
    cost_stress = GateResultV1(
        gate_id="COST_STRESS",
        passed=stress_ok,
        reason_code=None if stress_ok else "COST_STRESS_NOT_SURVIVED",
        observed=cost_stress_1_5x_net_profit_factor,
        threshold=thr["cost_stress_1_5x_net_profit_factor_min"],
    )

    dd_ok = abs(max_drawdown) <= float(thr["maximum_max_drawdown"])
    drawdown = GateResultV1(
        gate_id="MAX_DRAWDOWN",
        passed=dd_ok,
        reason_code=None if dd_ok else "MAX_DRAWDOWN_BREACH",
        observed=max_drawdown,
        threshold=thr["maximum_max_drawdown"],
    )

    trade_ok = trade_count >= int(thr["minimum_trade_count"])
    trade_sample = GateResultV1(
        gate_id="TRADE_SAMPLE",
        passed=trade_ok,
        reason_code=None if trade_ok else "INSUFFICIENT_TRADE_SAMPLE",
        observed=trade_count,
        threshold=thr["minimum_trade_count"],
    )

    if len(segment_results) != TIME_SEGMENT_COUNT:
        all_eval = GateResultV1(
            gate_id="ALL_SEGMENTS_EVALUABLE",
            passed=False,
            reason_code="ROBUSTNESS_SAMPLE_INSUFFICIENT",
            observed=len(segment_results),
            threshold=TIME_SEGMENT_COUNT,
        )
        robustness = GateResultV1(
            gate_id="TIME_SEGMENT_ROBUSTNESS",
            passed=False,
            reason_code="ROBUSTNESS_SAMPLE_INSUFFICIENT",
            observed=0.0,
            threshold=thr["time_segment_robustness_pass_ratio"],
        )
    else:
        evaluable = [s for s in segment_results if s.get("result") != "NON_EVALUABLE"]
        all_eval_ok = len(evaluable) == TIME_SEGMENT_COUNT and all(
            s.get("result") in ("PASS", "FAIL") for s in segment_results
        )
        all_eval = GateResultV1(
            gate_id="ALL_SEGMENTS_EVALUABLE",
            passed=all_eval_ok,
            reason_code=None if all_eval_ok else "ROBUSTNESS_SAMPLE_INSUFFICIENT",
            observed=len(evaluable),
            threshold=TIME_SEGMENT_COUNT,
        )
        passing = sum(1 for s in segment_results if s.get("result") == "PASS")
        ratio = passing / float(TIME_SEGMENT_COUNT)
        rob_ok = all_eval_ok and ratio >= float(thr["time_segment_robustness_pass_ratio"])
        assert MINIMUM_PASSING_SEGMENTS == int(
            float(thr["time_segment_robustness_pass_ratio"]) * TIME_SEGMENT_COUNT
        )
        robustness = GateResultV1(
            gate_id="TIME_SEGMENT_ROBUSTNESS",
            passed=rob_ok,
            reason_code=None if rob_ok else "TIME_SEGMENT_ROBUSTNESS_FAIL",
            observed={"passing_segments": passing, "pass_ratio": ratio},
            threshold=thr["time_segment_robustness_pass_ratio"],
        )

    return AdmissionGateBundleV1(
        sample_sufficiency=sample,
        gross_edge=gross,
        canonical_cost=canonical_cost,
        cost_stress=cost_stress,
        max_drawdown=drawdown,
        time_segment_robustness=robustness,
        all_segments_evaluable=all_eval,
        trade_sample=trade_sample,
    )


def evaluate_segment_local_result_v1(
    *,
    contract: Mapping[str, Any],
    valid_rebalance_observations: int,
    gross_profit_factor: float,
    gross_pnl: float,
    net_profit_factor: float,
    net_expectancy: float,
    max_drawdown: float,
    trade_count: int,
    worst1_abs_net_share: float | None = None,
) -> str:
    """Segment-local PASS/FAIL/NON_EVALUABLE using preregistered economic thresholds.

    Global sample-sufficiency (minimum_rebalance_observations=30) applies to the full
    development window, not per segment. A segment is NON_EVALUABLE only when it has
    zero valid rebalance observations.
    """
    if valid_rebalance_observations <= 0:
        return "NON_EVALUABLE"
    thr = _thresholds_from_contract(contract)
    gross_ok = gross_profit_factor >= float(thr["gross_profit_factor_min"]) and gross_pnl > 0.0
    cost_ok = net_profit_factor >= float(thr["net_profit_factor_min"]) and net_expectancy >= float(
        thr["minimum_net_expectancy"]
    )
    if worst1_abs_net_share is not None:
        cost_ok = cost_ok and worst1_abs_net_share <= float(thr["single_trade_dominance_limit"])
    dd_ok = abs(max_drawdown) <= float(thr["maximum_max_drawdown"])
    trade_ok = trade_count >= int(thr["minimum_trade_count"])
    return "PASS" if (gross_ok and cost_ok and dd_ok and trade_ok) else "FAIL"
