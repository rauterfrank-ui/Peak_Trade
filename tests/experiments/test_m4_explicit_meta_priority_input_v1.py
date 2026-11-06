"""Explicit research proposals survive the outer M4 seam into the Search consumer."""

from pathlib import Path

import pytest

from src.experiments.canonical_advanced_search_v1 import AdvancedSearchValidationError
from src.experiments.canonical_experiment_identity_v1 import build_canonical_experiment_identity_v1
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_meta_learning_v1 import build_canonical_meta_learning_v1
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    run_optimization_universe_experiment_plane_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_advanced_search_v1 import _space
from tests.experiments.test_canonical_meta_learning_v1 import _request as _meta_request
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _champion,
    _identity_request,
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state


def _inputs(tmp_path: Path):
    evidence = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    meta = build_canonical_meta_learning_v1(_meta_request())
    proposal = next(p for p in meta["research_proposals"] if p["target_kind"] == "parameter_region")
    return evidence, meta, proposal


def test_actual_meta_proposal_changes_m4_candidate_and_retains_priority_provenance(tmp_path: Path):
    evidence, meta, proposal = _inputs(tmp_path)
    champion_identity = build_canonical_experiment_identity_v1(
        _identity_request(strategy_params={"fast": 20, "slow": 200})
    )
    context = {
        "champion": _champion(
            experiment_identity=champion_identity,
            experiment_id=derive_experiment_id_v1(str(champion_identity["identity_digest"])),
        ),
        "search_space": _space(),
        "parent_hypothesis_id": "hyp.ma-crossover.v1",
        "strategy_family": "ma_crossover",
        "hypothesis_kind": "trend_following",
        "regime": "high_vol",
    }
    before = run_optimization_universe_experiment_plane_v1(_plane_request(evidence, **context))
    after = run_optimization_universe_experiment_plane_v1(
        _plane_request(
            evidence,
            **context,
            meta_learning_signals=(proposal,),
            meta_learning_identity=meta["meta_learning_identity"],
        )
    )
    assert before["status"] == after["status"] == PLANE_STATUS_COMPLETE
    assert before["chain"]["selected_candidate"]["parameter_region"] == {"fast": 10, "slow": 50}
    assert after["chain"]["selected_candidate"]["parameter_region"] != {"fast": 10, "slow": 50}
    bound = after["chain"]["search_meta_priority_evidence"]
    assert bound["source_meta_learning_identity"] == meta["meta_learning_identity"]
    assert bound["supplied_proposal_ids"] == [proposal["proposal_id"]]
    for candidate in bound["candidates"]:
        targeted = candidate["parameter_region"] == {"fast": 10, "slow": 50}
        assert candidate["search_priority_score"] == (-20 if targeted else 0)
        assert candidate["matched_proposal_ids"] == ([proposal["proposal_id"]] if targeted else [])
    assert bound["research_priority_only"] is True
    assert bound["productive_apply_authorized"] is False
    assert after["chain"]["proposal"]["productive_config_mutation"] is False
    assert after["chain"]["proposal"]["promotion_authority"] == "NONE"


def test_m4_does_not_invent_missing_meta_identity(tmp_path: Path):
    evidence, _meta, proposal = _inputs(tmp_path)
    with pytest.raises(AdvancedSearchValidationError, match="meta_learning_identity"):
        run_optimization_universe_experiment_plane_v1(
            _plane_request(evidence, meta_learning_signals=(proposal,))
        )


def test_m4_does_not_translate_m7_budget_metadata_into_a_phase11_proposal(tmp_path: Path):
    evidence, meta, _proposal = _inputs(tmp_path)
    with pytest.raises(AdvancedSearchValidationError, match="kind is not canonical"):
        run_optimization_universe_experiment_plane_v1(
            _plane_request(
                evidence,
                meta_learning_signals=({"research_budget_units": 1},),
                meta_learning_identity=meta["meta_learning_identity"],
            )
        )


def test_default_m4_does_not_create_meta_provenance_or_adaptive_input(tmp_path: Path):
    evidence, _meta, _proposal = _inputs(tmp_path)
    result = run_optimization_universe_experiment_plane_v1(_plane_request(evidence))
    assert result["status"] == PLANE_STATUS_COMPLETE
    assert "search_meta_priority_evidence" not in result["chain"]
