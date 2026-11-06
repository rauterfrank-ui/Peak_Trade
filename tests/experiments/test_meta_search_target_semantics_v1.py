"""Typed research targets must not gain priority from unrelated equal text."""

from dataclasses import replace

import pytest

from src.experiments.canonical_advanced_search_v1 import build_canonical_advanced_search_v1
from src.experiments.canonical_meta_learning_v1 import build_canonical_meta_learning_v1
from tests.experiments.test_canonical_advanced_search_v1 import _request, _signal
from tests.experiments.test_canonical_meta_learning_v1 import _request as _meta_request


def _search(signal):
    return build_canonical_advanced_search_v1(
        _request(meta_learning_signals=(signal,), meta_learning_identity="b" * 64)
    )


@pytest.mark.parametrize(
    "target_kind", ["robustness_test", "backtest_metric", "cost_model", "regime", "research_path", "unknown_kind"]
)
@pytest.mark.parametrize("target", ["ma_crossover", "search.ma.v1", "trend_following"])
def test_other_target_kinds_cannot_match_unrelated_candidate_identity_text(target_kind, target):
    result = _search(_signal(target_kind=target_kind, target=target))
    assert all(c["search_priority_score"] == 0 for c in result["candidates"])
    assert all(not c["matched_meta_learning_proposal_ids"] for c in result["candidates"])


@pytest.mark.parametrize("target_kind", ["search_space", "search_space_id"])
def test_search_space_names_bind_only_to_the_actual_search_space(target_kind):
    result = _search(_signal(target_kind=target_kind, target="search.ma.v1"))
    assert all(c["search_priority_score"] == 20 for c in result["candidates"])
    assert all(c["matched_meta_learning_proposal_ids"] for c in result["candidates"])
    unrelated = _search(_signal(target_kind=target_kind, target="ma_crossover"))
    assert all(c["search_priority_score"] == 0 for c in unrelated["candidates"])


def test_actual_meta_metric_proposal_does_not_turn_into_a_same_named_strategy_hint():
    request = _meta_request()
    units = tuple(
        replace(
            unit,
            backtest_metrics={"ma_crossover": 1.2},
            later_outcome=replace(unit.later_outcome, metric_name="ma_crossover"),
        )
        for unit in request.units
    )
    meta = build_canonical_meta_learning_v1(replace(request, units=units))
    proposal = next(p for p in meta["research_proposals"] if p["target_kind"] == "backtest_metric")
    assert proposal["target"] == "ma_crossover"
    result = build_canonical_advanced_search_v1(
        _request(
            meta_learning_signals=(proposal,),
            meta_learning_identity=meta["meta_learning_identity"],
        )
    )
    assert all(c["search_priority_score"] == 0 for c in result["candidates"])
    assert all(not c["matched_meta_learning_proposal_ids"] for c in result["candidates"])
    assert result["search_can_promote"] is False


def test_actual_meta_search_space_proposal_keeps_its_typed_effect():
    request = _meta_request()
    units = tuple(
        replace(
            unit,
            robustness_test_statuses={
                "TRAIN_VALIDATION_HOLDOUT": "PASS", "WALK_FORWARD": "FAIL", "ROLLING_OOS": "FAIL"
            },
        )
        for unit in request.units
    )
    meta = build_canonical_meta_learning_v1(replace(request, units=units))
    proposal = next(p for p in meta["research_proposals"] if p["target_kind"] == "search_space")
    assert proposal["target"] == "search.ma.v1"
    result = build_canonical_advanced_search_v1(
        _request(
            meta_learning_signals=(proposal,),
            meta_learning_identity=meta["meta_learning_identity"],
        )
    )
    assert all(c["search_priority_score"] == -20 for c in result["candidates"])
    assert all(c["matched_meta_learning_proposal_ids"] == [proposal["proposal_id"]] for c in result["candidates"])
    assert result["productive_config_mutation"] is False
