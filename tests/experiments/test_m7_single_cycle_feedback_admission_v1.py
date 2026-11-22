"""Standalone cycle admission preserves M7's research-only packet contract."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_deterministic_multi_cycle_offline_replay_v1 import (
    bounded_replay,
)

FAULTS = (
    "domain",
    "decision_schema",
    "identity",
    "digest",
    "source_parent",
    "authority",
    "external",
    "search_execution",
    "surface_count",
    "typed_top_flag",
    "typed_item_flag",
    "item_search_authority",
    "item_outcome",
)
VARIANTS = ("native", "mi_crossing", "federated")


def setup_cycle(variant, root):
    if variant == "native":
        from src.experiments import canonical_deterministic_multi_cycle_offline_replay_v1 as owner
        from tests.experiments.test_canonical_deterministic_multi_cycle_offline_replay_v1 import (
            _two_cycle_request,
        )

        return owner, owner.run_offline_evidence_cycle_v1, _two_cycle_request(root)
    if variant == "mi_crossing":
        from src.experiments import (
            canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 as owner,
        )
        from tests.experiments.test_canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
            _two_cycle_request,
        )

        return owner, owner.run_mi_crossing_offline_evidence_cycle_v1, _two_cycle_request(root)
    from src.experiments import canonical_federated_bounded_multi_cycle_offline_replay_v1 as owner
    from tests.experiments.test_canonical_federated_bounded_multi_cycle_offline_replay_v1 import (
        _two_cycle_request,
    )

    return owner, owner.run_federated_offline_evidence_cycle_v1, _two_cycle_request()


def changed_feedback(original, fault):
    changed = json.loads(json.dumps(original, default=dict))
    if fault == "domain":
        changed["domain"] = "foreign.research.feedback"
    elif fault == "decision_schema":
        changed["decision_schema_version"] = "foreign_decision_v1"
    elif fault == "identity":
        changed["feedback_decision_identity"] = "d" * 64
    elif fault == "source_parent":
        changed["source_meta_evidence_id"] = "d" * 64
    elif fault == "authority":
        changed["optimization_productive_authority"] = "LIVE"
    elif fault == "external":
        changed["external_effect_authorized"] = True
    elif fault == "search_execution":
        changed["search_executed"] = True
    elif fault == "surface_count":
        changed["authorized_productive_surfaces"] = 1
    elif fault == "typed_top_flag":
        changed["proposal_not_authority"] = 1
    elif fault == "typed_item_flag":
        changed["feedback_items"][0]["proposal_not_authority"] = 1
    elif fault == "item_search_authority":
        changed["feedback_items"][0]["search_execution_authorized"] = True
    elif fault == "item_outcome":
        changed["feedback_items"][0]["outcome"] = "UNSUPPORTED_OUTCOME"
    changed["result_digest"] = compute_content_sha256(
        {k: v for k, v in changed.items() if k != "result_digest"}
    )
    if fault == "digest":
        changed["result_digest"] = "d" * 64
    return changed


@pytest.mark.parametrize("fault", FAULTS)
def test_bad_prior_is_rejected_before_the_single_cycle_consumer(bounded_replay, monkeypatch, fault):
    owner, _, cycle_name, request = bounded_replay
    cycle = getattr(owner, cycle_name)
    original = cycle(request.cycles[0])["bounded_research_feedback_decision"]
    changed = changed_feedback(original, fault)
    before = deepcopy(changed)
    calls = []
    seam = next(
        name
        for name in (
            "run_optimization_universe_experiment_plane_v1",
            "run_market_intelligence_offline_orchestrator_cycle_v1",
            "perform_federated_m5_m6_return_join_v1",
        )
        if hasattr(owner, name)
    )
    downstream = getattr(owner, seam)

    def observe(*args, **kwargs):
        calls.append(seam)
        return downstream(*args, **kwargs)

    monkeypatch.setattr(owner, seam, observe)
    with pytest.raises(ValueError, match="PRIOR_FEEDBACK_INVALID"):
        cycle(replace(request.cycles[1], prior_feedback_decision=changed))
    assert calls == []
    assert changed == before


@pytest.mark.parametrize("transport", ["mapping", "json"])
def test_valid_original_prior_reaches_existing_single_cycle(bounded_replay, transport):
    owner, _, cycle_name, request = bounded_replay
    cycle = getattr(owner, cycle_name)
    original = cycle(request.cycles[0])["bounded_research_feedback_decision"]
    supplied = json.loads(json.dumps(original, default=dict)) if transport == "json" else original
    result = cycle(replace(request.cycles[1], prior_feedback_decision=supplied))
    semantics = result["cycle_body"]["cycle_n_plus_1_input_semantics"]
    assert semantics["search_execution_authorized"] is False
    assert semantics["proposal_not_authority"] is True
    assert result["search_executed"] is False
    assert result["learning_state_mutation_performed"] is False
    assert (
        result["cycle_body"]["prior_feedback_decision_identity"]
        == original["feedback_decision_identity"]
    )


def valid_packet(variant, root):
    owner, cycle, request = setup_cycle(variant, root)
    first = cycle(request.cycles[0])
    prior = first["bounded_research_feedback_decision"]
    transported = json.loads(json.dumps(prior, default=dict))
    second = cycle(replace(request.cycles[1], prior_feedback_decision=transported))
    replay_name = {
        "native": "run_deterministic_multi_cycle_offline_replay_v1",
        "mi_crossing": "run_mi_crossing_deterministic_multi_cycle_offline_replay_v1",
        "federated": "run_federated_deterministic_multi_cycle_offline_replay_v1",
    }[variant]
    replay = getattr(owner, replay_name)(request)
    assert json.dumps(replay["cycles"][1], sort_keys=True, default=dict) == json.dumps(
        second, sort_keys=True, default=dict
    )
    return {"first": first, "second": second, "replay": replay}


@pytest.mark.parametrize("variant", ["missing", "stale", "annotation"])
def test_native_no_action_and_annotation_packets_keep_their_meaning(bounded_replay, variant):
    from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
        MetaToOptimizationFeedbackInputRequestV1,
        validate_bounded_research_feedback_decision_v1,
        validate_meta_to_optimization_feedback_input_v1,
    )

    owner, _, cycle_name, request = bounded_replay
    cycle = getattr(owner, cycle_name)
    if variant == "annotation":
        prior = json.loads(
            json.dumps(cycle(request.cycles[0])["bounded_research_feedback_decision"], default=dict)
        )
        prior["source_note"] = "synthetic.opaque.annotation"
        prior["result_digest"] = compute_content_sha256(
            {k: v for k, v in prior.items() if k != "result_digest"}
        )
    else:
        prior = dict(
            validate_meta_to_optimization_feedback_input_v1(
                MetaToOptimizationFeedbackInputRequestV1(
                    meta_learning_evidence=None,
                    expected_meta_learning_evidence_schema_version=(
                        "stale" if variant == "stale" else None
                    ),
                )
            )
        )
    before = deepcopy(prior)
    validated = validate_bounded_research_feedback_decision_v1(prior)
    assert dict(validated) == prior == before
    result = cycle(replace(request.cycles[1], prior_feedback_decision=prior))
    semantics = result["cycle_body"]["cycle_n_plus_1_input_semantics"]
    if variant != "annotation":
        assert semantics["carried_forward_applicable_dispositions"] == []
        assert prior["source_meta_evidence_id"] is None
        assert prior["feedback_decision_identity"] is None
    assert semantics["search_execution_authorized"] is False
    assert result["search_executed"] is False
