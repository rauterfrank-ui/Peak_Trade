"""Actual Phase-11 proposals must address complete regions in Phase-12 Search."""

from src.experiments.canonical_advanced_search_v1 import (
    SearchAxisV1,
    SearchSpaceV1,
    build_canonical_advanced_search_v1,
)
from src.experiments.canonical_meta_learning_v1 import build_canonical_meta_learning_v1
from tests.experiments.test_canonical_advanced_search_v1 import _request, _signal
from tests.experiments.test_canonical_meta_learning_v1 import _request as _meta_request


def _selected(record):
    return [dict(c["parameter_region"]) for c in record["candidates"] if c["status"] == "PROPOSED"]


def test_actual_meta_region_proposal_changes_only_the_whole_region_and_budget_choice():
    meta = build_canonical_meta_learning_v1(_meta_request())
    proposal = next(p for p in meta["research_proposals"] if p["target_kind"] == "parameter_region")
    baseline = build_canonical_advanced_search_v1(_request(budget=1))
    result = build_canonical_advanced_search_v1(
        _request(
            budget=1,
            meta_learning_signals=(proposal,),
            meta_learning_identity=meta["meta_learning_identity"],
        )
    )
    assert _selected(baseline) == [{"fast": 10, "slow": 50}]
    assert _selected(result) != _selected(baseline)
    for candidate in result["candidates"]:
        matching_region = dict(candidate["parameter_region"]) == {"fast": 10, "slow": 50}
        assert candidate["search_priority_score"] == (-20 if matching_region else 0)
        assert candidate["matched_meta_learning_proposal_ids"] == (
            [proposal["proposal_id"]] if matching_region else []
        )
    assert result["search_can_promote"] is False
    assert result["productive_config_mutation"] is False
    assert all(
        request["executed"] is False and request["loop_started"] is False
        for request in result["offline_experiment_requests"]
    )


def test_unrelated_whole_region_digest_does_not_change_candidates():
    result = build_canonical_advanced_search_v1(
        _request(
            meta_learning_signals=(_signal(target_kind="parameter_region", target="a" * 64),),
            meta_learning_identity="b" * 64,
        )
    )
    assert all(c["search_priority_score"] == 0 for c in result["candidates"])
    assert all(not c["matched_meta_learning_proposal_ids"] for c in result["candidates"])


def test_region_digest_cannot_accidentally_match_an_individual_hash_shaped_value():
    result = build_canonical_advanced_search_v1(
        _request(
            search_space=SearchSpaceV1(
                search_space_id="hash.shaped.parameter.value",
                axes=(SearchAxisV1("fast", ("a" * 64,)), SearchAxisV1("slow", (50,))),
            ),
            meta_learning_signals=(_signal(target_kind="parameter_region", target="a" * 64),),
            meta_learning_identity="b" * 64,
        )
    )
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["search_priority_score"] == 0
    assert not result["candidates"][0]["matched_meta_learning_proposal_ids"]


def test_existing_non_digest_value_signal_keeps_its_bounded_legacy_meaning():
    result = build_canonical_advanced_search_v1(
        _request(
            meta_learning_signals=(_signal(target_kind="parameter_region", target="10"),),
            meta_learning_identity="b" * 64,
        )
    )
    for candidate in result["candidates"]:
        assert candidate["search_priority_score"] == (
            20 if candidate["parameter_region"]["fast"] == 10 else 0
        )


def test_region_target_does_not_implicitly_expand_a_differently_declared_subspace():
    meta = build_canonical_meta_learning_v1(_meta_request())
    proposal = next(p for p in meta["research_proposals"] if p["target_kind"] == "parameter_region")
    result = build_canonical_advanced_search_v1(
        _request(
            search_space=SearchSpaceV1(
                search_space_id="only.fast.axis",
                axes=(SearchAxisV1("fast", (10, 15)),),
            ),
            meta_learning_signals=(proposal,),
            meta_learning_identity=meta["meta_learning_identity"],
        )
    )
    # The template still has slow=50, but the declared region is only {fast: ...}.
    # A region address is not an instruction to silently infer missing axes.
    assert all(c["search_priority_score"] == 0 for c in result["candidates"])
    assert all(not c["matched_meta_learning_proposal_ids"] for c in result["candidates"])
