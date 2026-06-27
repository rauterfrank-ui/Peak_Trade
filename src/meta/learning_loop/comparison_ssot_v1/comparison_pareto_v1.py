"""Descriptive Pareto evaluation for comparison_ssot.v1."""

from __future__ import annotations

import math

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    METRIC_KEYS,
    PARETO_DIRECTIONALITY,
    TIE_TOLERANCE_CATALOG,
)
from src.meta.learning_loop.comparison_ssot_v1.models import LoadedMetricInput


def _metric_value(item: LoadedMetricInput, metric: str) -> float:
    value = item.metrics[metric]
    return float(value)


def _within_tolerance(metric: str, a: float, b: float) -> bool:
    tolerance = TIE_TOLERANCE_CATALOG.get(metric)
    if tolerance is None:
        return a == b
    return abs(a - b) <= float(tolerance)


def _better_or_equal(metric: str, candidate: float, other: float) -> bool:
    direction = PARETO_DIRECTIONALITY[metric]
    if direction == "ELIGIBILITY_ONLY_NOT_OBJECTIVE":
        return True
    if direction == "MAXIMIZE":
        if _within_tolerance(metric, candidate, other):
            return True
        return candidate > other
    if direction == "MINIMIZE":
        if _within_tolerance(metric, candidate, other):
            return True
        return candidate < other
    raise ValueError(f"unknown direction for metric {metric}")


def _strictly_better(metric: str, candidate: float, other: float) -> bool:
    direction = PARETO_DIRECTIONALITY[metric]
    if direction == "ELIGIBILITY_ONLY_NOT_OBJECTIVE":
        return False
    if _within_tolerance(metric, candidate, other):
        return False
    if direction == "MAXIMIZE":
        return candidate > other
    return candidate < other


def _pareto_objectives() -> tuple[str, ...]:
    return tuple(
        metric
        for metric in METRIC_KEYS
        if PARETO_DIRECTIONALITY[metric] != "ELIGIBILITY_ONLY_NOT_OBJECTIVE"
    )


def dominates(a: LoadedMetricInput, b: LoadedMetricInput) -> bool:
    objectives = _pareto_objectives()
    any_strict = False
    for metric in objectives:
        av = _metric_value(a, metric)
        bv = _metric_value(b, metric)
        if math.isnan(av) or math.isnan(bv) or math.isinf(av) or math.isinf(bv):
            return False
        if not _better_or_equal(metric, av, bv):
            return False
        if _strictly_better(metric, av, bv):
            any_strict = True
    return any_strict


def compute_pareto_front(inputs: list[LoadedMetricInput]) -> dict[str, object]:
    front: list[str] = []
    for candidate in inputs:
        dominated = False
        for other in inputs:
            if candidate is other:
                continue
            if dominates(other, candidate):
                dominated = True
                break
        if not dominated:
            front.append(candidate.comparison_metric_input_id)
    front_sorted = sorted(front)
    return {
        "pareto_status": "COMPUTED",
        "pareto_front_member_ids": front_sorted,
        "pareto_objective_metrics": list(_pareto_objectives()),
        "pareto_descriptive_only": True,
    }
