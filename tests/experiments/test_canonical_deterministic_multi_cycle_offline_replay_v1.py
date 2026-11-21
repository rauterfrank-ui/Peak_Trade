"""Tests for M8 deterministic multi-cycle offline replay."""

from __future__ import annotations

import ast
from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.experiments.canonical_deterministic_multi_cycle_offline_replay_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    BOUND_CONTRACT_VERSIONS,
    LEARNING_STATE_MUTATION_PERFORMED,
    MINIMUM_CYCLE_COUNT,
    OfflineMultiCycleReplayError,
    OfflineReplayCycleInputV1,
    DeterministicMultiCycleOfflineReplayRequestV1,
    REPLAY_STATUS_COMPLETE,
    REPLAY_STATUS_REJECTED_CYCLE_ORDER,
    REPLAY_STATUS_REJECTED_STALE,
    SEARCH_EXECUTED,
    run_deterministic_multi_cycle_offline_replay_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT / "src" / "experiments" / "canonical_deterministic_multi_cycle_offline_replay_v1.py"
)


def _two_cycle_request(tmp_path: Path) -> DeterministicMultiCycleOfflineReplayRequestV1:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    plane = _plane_request(evidence)
    base = OfflineReplayCycleInputV1(
        cycle_index=0,
        learning_evidence=evidence,
        plane_request=plane,
        replay_seed=42,
    )
    n1 = OfflineReplayCycleInputV1(
        cycle_index=1,
        learning_evidence=evidence,
        plane_request=plane,
        replay_seed=42,
    )
    return DeterministicMultiCycleOfflineReplayRequestV1(cycles=(base, n1))


@pytest.fixture(params=("native", "mi_crossing", "federated"))
def bounded_replay(request, tmp_path):
    if request.param == "native":
        from src.experiments import canonical_deterministic_multi_cycle_offline_replay_v1 as owner

        return (
            owner,
            owner.run_deterministic_multi_cycle_offline_replay_v1,
            "run_offline_evidence_cycle_v1",
            _two_cycle_request(tmp_path),
        )
    if request.param == "mi_crossing":
        from src.experiments import (
            canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 as owner,
        )
        from tests.experiments.test_canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1 import (
            _two_cycle_request as mi_request,
        )

        return (
            owner,
            owner.run_mi_crossing_deterministic_multi_cycle_offline_replay_v1,
            "run_mi_crossing_offline_evidence_cycle_v1",
            mi_request(tmp_path),
        )
    from src.experiments import canonical_federated_bounded_multi_cycle_offline_replay_v1 as owner
    from tests.experiments.test_canonical_federated_bounded_multi_cycle_offline_replay_v1 import (
        _two_cycle_request as federated_request,
    )

    return (
        owner,
        owner.run_federated_deterministic_multi_cycle_offline_replay_v1,
        "run_federated_offline_evidence_cycle_v1",
        federated_request(),
    )


@pytest.mark.parametrize(
    "fault", ("source_meta", "research_priority", "search_outcome", "typed_proposal_flag")
)
@pytest.mark.parametrize("reseal_transport", (False, True))
def test_changed_feedback_cannot_reuse_prior_identity_before_next_cycle(
    bounded_replay, monkeypatch, fault, reseal_transport
):
    from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
        DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT,
        DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
        OUTCOME_APPLICABLE,
    )
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    owner, replay, cycle_name, request = bounded_replay
    original_cycle = getattr(owner, cycle_name)
    original = original_cycle(request.cycles[0])["bounded_research_feedback_decision"]
    changed = json.loads(json.dumps(original, default=dict))
    if fault == "source_meta":
        source = changed["source_meta_evidence_id"]
        changed["source_meta_evidence_id"] = ("0" if source[0] != "0" else "1") + source[1:]
    elif fault == "typed_proposal_flag":
        assert changed["feedback_items"][0]["proposal_not_authority"] is True
        changed["feedback_items"][0]["proposal_not_authority"] = 1
    else:
        disposition = (
            DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT
            if fault == "research_priority"
            else DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD
        )
        item = next(
            item for item in changed["feedback_items"] if item["disposition"] == disposition
        )
        item["outcome"] = OUTCOME_APPLICABLE
        if fault == "research_priority":
            item["payload"]["experiment_ids"] = ["experiment.foreign.original"]
    if reseal_transport:
        changed["result_digest"] = compute_content_sha256(
            {key: value for key, value in changed.items() if key != "result_digest"}
        )
    assert changed["feedback_decision_identity"] == original["feedback_decision_identity"]

    called_indices = []

    def guarded_cycle(spec, **kwargs):
        called_indices.append(spec.cycle_index)
        if spec.cycle_index > 0:
            pytest.fail("Changed prior feedback reached the next cycle consumer")
        return original_cycle(spec, **kwargs)

    monkeypatch.setattr(owner, cycle_name, guarded_cycle)
    result = replay(
        replace(
            request,
            cycles=(request.cycles[0], replace(request.cycles[1], prior_feedback_decision=changed)),
        )
    )
    assert result["status"] == owner.REPLAY_STATUS_REJECTED_LINEAGE
    assert result["reason"] == "PRIOR_FEEDBACK_DECISION_MISMATCH"
    assert result["cycle_count"] == 1
    assert result["multi_cycle_loop_closed"] is False
    assert result["replay_identity"] is None
    assert called_indices == [0]


def test_original_feedback_json_roundtrip_preserves_automatic_carry_forward(bounded_replay):
    owner, replay, cycle_name, request = bounded_replay
    original = getattr(owner, cycle_name)(request.cycles[0])["bounded_research_feedback_decision"]
    transported = json.loads(json.dumps(original, default=dict))
    explicit = replay(
        replace(
            request,
            cycles=(
                request.cycles[0],
                replace(request.cycles[1], prior_feedback_decision=transported),
            ),
        )
    )
    automatic = replay(request)
    assert explicit["status"] == owner.REPLAY_STATUS_COMPLETE
    assert explicit["replay_identity"] == automatic["replay_identity"]
    assert explicit["result_digest"] == automatic["result_digest"]
    assert explicit["search_executed"] is False
    assert explicit["learning_state_mutation_performed"] is False
    assert explicit["external_effect_authorized"] is False


def test_two_cycle_replay_closed_and_deterministic(tmp_path: Path) -> None:
    first = run_deterministic_multi_cycle_offline_replay_v1(_two_cycle_request(tmp_path))
    second = run_deterministic_multi_cycle_offline_replay_v1(_two_cycle_request(tmp_path))
    assert first["status"] == REPLAY_STATUS_COMPLETE
    assert first["multi_cycle_loop_closed"] is True
    assert first["cycle_count"] == MINIMUM_CYCLE_COUNT
    assert first["replay_identity"] == second["replay_identity"]
    assert first["result_digest"] == second["result_digest"]
    assert first["search_executed"] is False
    assert SEARCH_EXECUTED is False
    assert first["learning_state_mutation_performed"] is False
    assert LEARNING_STATE_MUTATION_PERFORMED is False
    assert first["authorized_productive_surfaces"] == 0
    cycle0 = first["cycles"][0]
    cycle1 = first["cycles"][1]
    assert cycle0["cycle_index"] == 0
    assert cycle1["cycle_index"] == 1
    assert (
        cycle1["cycle_body"]["prior_feedback_decision_identity"]
        == cycle0["cycle_body"]["feedback_decision_identity"]
    )
    assert cycle1["cycle_body"]["cycle_n_plus_1_input_semantics"] is not None
    assert cycle0["search_method_selection_outcome"] == "FAIL_CLOSED"
    assert cycle1["search_method_selection_outcome"] == "FAIL_CLOSED"


def test_rejects_stale_contract_version(tmp_path: Path) -> None:
    stale = dict(BOUND_CONTRACT_VERSIONS)
    stale["m8_replay"] = "canonical_deterministic_multi_cycle_offline_replay_v0"
    result = run_deterministic_multi_cycle_offline_replay_v1(
        DeterministicMultiCycleOfflineReplayRequestV1(
            cycles=_two_cycle_request(tmp_path).cycles,
            expected_contract_versions=stale,
        )
    )
    assert result["status"] == REPLAY_STATUS_REJECTED_STALE


def test_rejects_out_of_order_cycle_indices(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    plane = _plane_request(evidence)
    result = run_deterministic_multi_cycle_offline_replay_v1(
        DeterministicMultiCycleOfflineReplayRequestV1(
            cycles=(
                OfflineReplayCycleInputV1(1, evidence, plane, 42),
                OfflineReplayCycleInputV1(0, evidence, plane, 42),
            )
        )
    )
    assert result["status"] == REPLAY_STATUS_REJECTED_CYCLE_ORDER


def test_forbidden_search_execution_request() -> None:
    with pytest.raises(OfflineMultiCycleReplayError):
        run_deterministic_multi_cycle_offline_replay_v1(
            DeterministicMultiCycleOfflineReplayRequestV1(
                cycles=(),
                requested_search_execution=True,
            )
        )


def test_forbidden_graph_disjoint() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1",
        "src.experiments.canonical_advanced_search_v1.build_canonical_advanced_search_v1",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.trading",
        "src.trading.master_v2",
    }
    assert forbidden.isdisjoint(imported)
    assert "build_canonical_advanced_search_v1" not in source
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0
