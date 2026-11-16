"""Real M4–M8 → meta-learning → optimization feedback continuation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.governance.governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1 import (
    CLOSED_MECHANICAL_LEARNING_LOOP,
    CLOSED_PRODUCTIVE_OPTIMIZATION_LOOP,
    DECISION_CONFIG,
    M4M8MetaOptimizationFeedbackContinuationRequestV1,
    REAL_FEEDBACK_END_TO_END_STATUS,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    prove_real_meta_optimization_feedback_continuation_v1,
    run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1,
    validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1,
)
from src.governance.governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1 import (
    BINDING_PRODUCER_ID,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO_ROOT = Path(__file__).resolve().parents[2]


def _plain(value: object) -> object:
    from types import MappingProxyType

    if isinstance(value, (MappingProxyType, dict)):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


@pytest.fixture
def offline_lineage_fixture(tmp_path):
    learning = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    loop = run_m4_m8_evidence_return_loop_v1(
        M4M8EvidenceReturnLoopRequestV1(
            learning_evidence=learning, plane_request=_plane_request(learning), replay_seed=19
        )
    )
    assert loop["status"] == LOOP_STATUS_COMPLETE
    assert not validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning, m4_m8_loop=loop, require_runtime_g2_producer=False
    )
    return learning, _plain(loop)


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_observation_archive_cannot_reach_meta_or_feedback(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1(
        M4M8MetaOptimizationFeedbackContinuationRequestV1(projection_request=req)
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert result.ddo_fixture_learning_state_used is False
    assert result.m4_m8_real_output_used is False
    assert result.meta_learning_real_ingress_reached is False
    assert result.optimization_feedback_real_ingress_reached is False
    assert result.feedback_output_produced is False
    assert result.meta_learning_evidence is None
    assert result.bounded_research_feedback_decision is None
    assert not prove_real_meta_optimization_feedback_continuation_v1(projection_request=req)


def test_ddo_fixture_forbidden_on_real_feedback_path(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_real_runtime_g2_to_meta_learning_optimization_feedback_continuation_v1(
        M4M8MetaOptimizationFeedbackContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"


def test_lineage_mismatch_rejected(offline_lineage_fixture) -> None:
    learning, loop = offline_lineage_fixture
    loop["cycle"]["learning_input_validation"]["learning_evidence_digest"] = "0" * 64
    reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning,
        m4_m8_loop=loop,
        require_runtime_g2_producer=False,
    )
    assert reasons == ("LEARNING_EVIDENCE_DIGEST_LINEAGE_MISMATCH",)


def test_malformed_meta_evidence_rejected(offline_lineage_fixture) -> None:
    learning, loop = offline_lineage_fixture
    loop["cycle"]["meta_learning_evidence"].pop("meta_evidence_id")
    reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning,
        m4_m8_loop=loop,
        require_runtime_g2_producer=False,
    )
    assert reasons == ("M6_META_LEARNING_EVIDENCE_MALFORMED",)


def test_cross_source_optimization_digest_rejected(offline_lineage_fixture) -> None:
    learning, loop = offline_lineage_fixture
    loop["cycle"]["meta_learning_evidence"]["source_optimization_experiment_evidence_digest"] = (
        "f" * 64
    )
    reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning,
        m4_m8_loop=loop,
        require_runtime_g2_producer=False,
    )
    assert "M6_SOURCE_OPTIMIZATION_EVIDENCE_DIGEST_MISMATCH" in reasons


def test_m4_and_m5_must_reference_the_same_original_learning_evidence(
    offline_lineage_fixture,
) -> None:
    learning, loop = offline_lineage_fixture
    cycle = loop["cycle"]
    cycle["experiment_plane_result"]["learning_input_validation"]["learning_evidence_digest"] = (
        "f" * 64
    )
    cycle["optimization_experiment_evidence"]["learning_evidence_digest"] = "f" * 64
    assert validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=learning, m4_m8_loop=loop, require_runtime_g2_producer=False
    ) == (
        "M4_LEARNING_EVIDENCE_DIGEST_LINEAGE_MISMATCH",
        "M5_LEARNING_EVIDENCE_DIGEST_LINEAGE_MISMATCH",
    )


def test_ddo_producer_cannot_substitute_for_runtime_binding(offline_lineage_fixture) -> None:
    ddo_evidence, loop = offline_lineage_fixture
    reasons = validate_real_m4_m8_cycle_meta_optimization_feedback_join_v1(
        learning_evidence=ddo_evidence,
        m4_m8_loop=loop,
        require_runtime_g2_producer=True,
    )
    assert reasons == ("LEARNING_EVIDENCE_NOT_RUNTIME_G2_BINDING",)
    assert ddo_evidence.get("producer_id") != BINDING_PRODUCER_ID


def test_authority_invariants_and_decision_config() -> None:
    assert prove_continuation_authority_invariants_v1() is True
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT) is True
    assert CLOSED_MECHANICAL_LEARNING_LOOP is True
    assert CLOSED_PRODUCTIVE_OPTIMIZATION_LOOP is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["real_feedback_end_to_end_status"] == REAL_FEEDBACK_END_TO_END_STATUS
    assert decision["closed_mechanical_learning_loop"] is True
    assert decision["closed_productive_optimization_loop"] is False
