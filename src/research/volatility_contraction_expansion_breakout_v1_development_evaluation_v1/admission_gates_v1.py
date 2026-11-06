"""Admission gates for VCEB v1 development evaluation.

Applies preregistered measurement-contract thresholds only. Does not invent or
lower thresholds. Pure functions over already-computed metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    COST_STRESS_1_5X_NET_PROFIT_FACTOR_MIN,
    GROSS_PROFIT_FACTOR_MIN,
    MAXIMUM_MAX_DRAWDOWN,
    MINIMUM_NET_EXPECTANCY,
    MINIMUM_PASSING_SEGMENTS,
    MIN_EVALUABLE_TREATMENT_BREAKOUT_EVENTS,
    MIN_EVALUABLE_TREATMENT_EVENTS_PER_TIME_SEGMENT,
    MIN_EXECUTED_TREATMENT_TRADES,
    NET_PROFIT_FACTOR_MIN,
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
    trades_sufficiency: GateResultV1
    segment_event_sufficiency: GateResultV1
    gross_edge: GateResultV1
    canonical_cost: GateResultV1
    cost_stress: GateResultV1
    max_drawdown: GateResultV1
    baseline_improvement: GateResultV1
    time_segment_robustness: GateResultV1
    all_segments_evaluable: GateResultV1

    @property
    def all_pass(self) -> bool:
        return all(
            g.passed
            for g in (
                self.sample_sufficiency,
                self.trades_sufficiency,
                self.segment_event_sufficiency,
                self.gross_edge,
                self.canonical_cost,
                self.cost_stress,
                self.max_drawdown,
                self.baseline_improvement,
                self.time_segment_robustness,
                self.all_segments_evaluable,
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
            "trades_sufficiency": _one(self.trades_sufficiency),
            "segment_event_sufficiency": _one(self.segment_event_sufficiency),
            "gross_edge": _one(self.gross_edge),
            "canonical_cost": _one(self.canonical_cost),
            "cost_stress": _one(self.cost_stress),
            "max_drawdown": _one(self.max_drawdown),
            "baseline_improvement": _one(self.baseline_improvement),
            "time_segment_robustness": _one(self.time_segment_robustness),
            "all_segments_evaluable": _one(self.all_segments_evaluable),
            "all_pass": self.all_pass,
        }


def _thresholds_from_contract(contract: Mapping[str, Any]) -> dict[str, float | int]:
    thr = (contract.get("economic_admission_contract") or {}).get("thresholds") or {}
    return {
        "min_evaluable_treatment_breakout_events": int(
            thr["min_evaluable_treatment_breakout_events"]["value"]
        ),
        "min_evaluable_treatment_events_per_time_segment": int(
            thr["min_evaluable_treatment_events_per_time_segment"]["value"]
        ),
        "min_executed_treatment_trades": int(thr["min_executed_treatment_trades"]["value"]),
        "time_segment_robustness_pass_ratio": float(
            thr["time_segment_robustness_pass_ratio"]["value"]
        ),
        "gross_profit_factor_min": float(thr["gross_profit_factor_min"]["value"]),
        "net_profit_factor_min": float(thr["net_profit_factor_min"]["value"]),
        "cost_stress_1_5x_net_profit_factor_min": float(
            thr["cost_stress_1_5x_net_profit_factor_min"]["value"]
        ),
        "maximum_max_drawdown": float(thr["maximum_max_drawdown"]["value"]),
        "minimum_net_expectancy": float(thr["minimum_net_expectancy"]["value"]),
    }


def evaluate_admission_gates_v1(
    *,
    contract: Mapping[str, Any],
    evaluable_treatment_breakout_events: int,
    trade_count: int,
    gross_profit_factor: float,
    gross_pnl: float,
    net_profit_factor: float,
    baseline_net_profit_factor: float,
    net_expectancy: float,
    max_drawdown: float,
    cost_stress_1_5x_net_profit_factor: float,
    segment_results: Sequence[Mapping[str, Any]],
) -> AdmissionGateBundleV1:
    thr = _thresholds_from_contract(contract)
    assert thr["min_evaluable_treatment_breakout_events"] == MIN_EVALUABLE_TREATMENT_BREAKOUT_EVENTS
    assert (
        thr["min_evaluable_treatment_events_per_time_segment"]
        == MIN_EVALUABLE_TREATMENT_EVENTS_PER_TIME_SEGMENT
    )
    assert thr["min_executed_treatment_trades"] == MIN_EXECUTED_TREATMENT_TRADES
    assert thr["time_segment_robustness_pass_ratio"] == TIME_SEGMENT_ROBUSTNESS_PASS_RATIO
    assert thr["gross_profit_factor_min"] == GROSS_PROFIT_FACTOR_MIN
    assert thr["net_profit_factor_min"] == NET_PROFIT_FACTOR_MIN
    assert thr["cost_stress_1_5x_net_profit_factor_min"] == COST_STRESS_1_5X_NET_PROFIT_FACTOR_MIN
    assert thr["maximum_max_drawdown"] == MAXIMUM_MAX_DRAWDOWN
    assert thr["minimum_net_expectancy"] == MINIMUM_NET_EXPECTANCY

    sample_ok = evaluable_treatment_breakout_events >= int(
        thr["min_evaluable_treatment_breakout_events"]
    )
    trades_ok = trade_count >= int(thr["min_executed_treatment_trades"])
    per_seg_ok = True
    for seg in segment_results:
        events = int(seg.get("evaluable_treatment_breakout_events") or 0)
        if events < int(thr["min_evaluable_treatment_events_per_time_segment"]):
            per_seg_ok = False
            break
    gross_ok = gross_profit_factor >= float(thr["gross_profit_factor_min"]) and gross_pnl > 0
    net_ok = net_profit_factor >= float(thr["net_profit_factor_min"]) and net_expectancy >= float(
        thr["minimum_net_expectancy"]
    )
    stress_ok = cost_stress_1_5x_net_profit_factor >= float(
        thr["cost_stress_1_5x_net_profit_factor_min"]
    )
    dd_ok = abs(max_drawdown) <= float(thr["maximum_max_drawdown"])
    baseline_ok = net_profit_factor > baseline_net_profit_factor
    passing = sum(1 for s in segment_results if s.get("result") == "PASS")
    evaluable_segments = sum(1 for s in segment_results if s.get("result") != "NON_EVALUABLE")
    ratio = passing / float(TIME_SEGMENT_COUNT)
    robustness_ok = (
        ratio >= float(thr["time_segment_robustness_pass_ratio"])
        and passing >= MINIMUM_PASSING_SEGMENTS
    )
    all_eval_ok = evaluable_segments == TIME_SEGMENT_COUNT

    return AdmissionGateBundleV1(
        sample_sufficiency=GateResultV1(
            "SAMPLE_SUFFICIENCY",
            sample_ok,
            None if sample_ok else "INSUFFICIENT_EVALUABLE_EVENTS",
            evaluable_treatment_breakout_events,
            thr["min_evaluable_treatment_breakout_events"],
        ),
        trades_sufficiency=GateResultV1(
            "TRADES_SUFFICIENCY",
            trades_ok,
            None if trades_ok else "INSUFFICIENT_EXECUTED_TRADES",
            trade_count,
            thr["min_executed_treatment_trades"],
        ),
        segment_event_sufficiency=GateResultV1(
            "SEGMENT_EVENT_SUFFICIENCY",
            per_seg_ok,
            None if per_seg_ok else "INSUFFICIENT_EVENTS_PER_TIME_SEGMENT",
            [s.get("evaluable_treatment_breakout_events") for s in segment_results],
            thr["min_evaluable_treatment_events_per_time_segment"],
        ),
        gross_edge=GateResultV1(
            "GROSS_EDGE",
            gross_ok,
            None if gross_ok else "GROSS_EDGE_NOT_MEANINGFUL",
            {"gross_profit_factor": gross_profit_factor, "gross_pnl": gross_pnl},
            thr["gross_profit_factor_min"],
        ),
        canonical_cost=GateResultV1(
            "CANONICAL_COST",
            net_ok,
            None if net_ok else "NET_PROFIT_FACTOR_BELOW_THRESHOLD",
            {"net_profit_factor": net_profit_factor, "net_expectancy": net_expectancy},
            thr["net_profit_factor_min"],
        ),
        cost_stress=GateResultV1(
            "COST_STRESS",
            stress_ok,
            None if stress_ok else "COST_STRESS_NOT_SURVIVED",
            cost_stress_1_5x_net_profit_factor,
            thr["cost_stress_1_5x_net_profit_factor_min"],
        ),
        max_drawdown=GateResultV1(
            "MAX_DRAWDOWN",
            dd_ok,
            None if dd_ok else "MAX_DRAWDOWN_BREACH",
            max_drawdown,
            thr["maximum_max_drawdown"],
        ),
        baseline_improvement=GateResultV1(
            "BASELINE_IMPROVEMENT",
            baseline_ok,
            None if baseline_ok else "NET_NOT_IMPROVED_VS_BASELINE",
            {
                "treatment_net_profit_factor": net_profit_factor,
                "baseline_net_profit_factor": baseline_net_profit_factor,
            },
            "treatment > baseline",
        ),
        time_segment_robustness=GateResultV1(
            "TIME_SEGMENT_ROBUSTNESS",
            robustness_ok,
            None if robustness_ok else "TIME_SEGMENT_ROBUSTNESS_FAIL",
            {"passing_segments": passing, "pass_ratio": ratio},
            thr["time_segment_robustness_pass_ratio"],
        ),
        all_segments_evaluable=GateResultV1(
            "ALL_SEGMENTS_EVALUABLE",
            all_eval_ok,
            None if all_eval_ok else "ROBUSTNESS_SAMPLE_INSUFFICIENT",
            evaluable_segments,
            TIME_SEGMENT_COUNT,
        ),
    )


def evaluate_segment_local_result_v1(
    *,
    contract: Mapping[str, Any],
    evaluable_treatment_breakout_events: int,
    gross_profit_factor: float,
    gross_pnl: float,
    net_profit_factor: float,
    baseline_net_profit_factor: float,
    net_expectancy: float,
    max_drawdown: float,
    trade_count: int,
) -> str:
    thr = _thresholds_from_contract(contract)
    if evaluable_treatment_breakout_events < int(
        thr["min_evaluable_treatment_events_per_time_segment"]
    ):
        return "NON_EVALUABLE"
    if trade_count <= 0:
        return "NON_EVALUABLE"
    ok = (
        gross_profit_factor >= float(thr["gross_profit_factor_min"])
        and gross_pnl > 0
        and net_profit_factor >= float(thr["net_profit_factor_min"])
        and net_expectancy >= float(thr["minimum_net_expectancy"])
        and abs(max_drawdown) <= float(thr["maximum_max_drawdown"])
        and net_profit_factor > baseline_net_profit_factor
    )
    return "PASS" if ok else "FAIL"
