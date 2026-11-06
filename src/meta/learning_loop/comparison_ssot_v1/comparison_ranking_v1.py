"""Optional lexicographic ranking for comparison_ssot.v1."""

from __future__ import annotations

from functools import cmp_to_key

from src.meta.learning_loop.comparison_ssot_v1.constants import (
    LEXICOGRAPHIC_RANKING_RULE_V1,
    LEXICOGRAPHIC_RANKING_SEQUENCE,
    RANKING_RULE_NONE,
)
from src.meta.learning_loop.comparison_ssot_v1.comparison_pareto_v1 import (
    _metric_value,
    _within_tolerance,
)
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError, LoadedMetricInput


def _ref_sort_key(item: LoadedMetricInput) -> tuple[str, str, str, str]:
    return item.source_ref.sort_key()


def _compare_lex(a: LoadedMetricInput, b: LoadedMetricInput) -> int:
    for metric, direction in LEXICOGRAPHIC_RANKING_SEQUENCE:
        av = _metric_value(a, metric)
        bv = _metric_value(b, metric)
        if _within_tolerance(metric, av, bv):
            continue
        if direction == "MAXIMIZE":
            if av > bv:
                return -1
            if av < bv:
                return 1
        elif direction == "MINIMIZE":
            if av < bv:
                return -1
            if av > bv:
                return 1
        else:
            raise ComparisonSsotError(f"metric {metric} is not a ranking objective")
    ref_a = _ref_sort_key(a)
    ref_b = _ref_sort_key(b)
    if ref_a < ref_b:
        return -1
    if ref_a > ref_b:
        return 1
    return 0


def compute_ranking(
    inputs: list[LoadedMetricInput],
    *,
    ranking_rule_version: str,
) -> dict[str, object]:
    if ranking_rule_version == RANKING_RULE_NONE:
        return {
            "ranking_status": "NONE",
            "ranking_rule_version": RANKING_RULE_NONE,
            "ranked_input_ids": [],
        }
    if ranking_rule_version != LEXICOGRAPHIC_RANKING_RULE_V1:
        raise ComparisonSsotError(f"unknown ranking_rule_version: {ranking_rule_version}")

    ordered = sorted(inputs, key=cmp_to_key(_compare_lex))
    return {
        "ranking_status": "LEXICOGRAPHIC",
        "ranking_rule_version": LEXICOGRAPHIC_RANKING_RULE_V1,
        "ranked_input_ids": [item.comparison_metric_input_id for item in ordered],
        "ranking_sequence": [
            {"metric": metric, "direction": direction}
            for metric, direction in LEXICOGRAPHIC_RANKING_SEQUENCE
        ],
    }
