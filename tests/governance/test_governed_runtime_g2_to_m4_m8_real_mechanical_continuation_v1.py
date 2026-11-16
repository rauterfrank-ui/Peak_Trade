"""Real mechanical G2 → M4–M8 continuation tests (no DDO fixture on real path)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    REAL_RUNTIME_G2_TO_M4_M8_STATUS,
    G2RuntimeM4M8ContinuationRequestV1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    run_g2_runtime_to_m4_m8_evidence_return_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_closure_v1 import (
    G2_END_TO_END_STATUS,
    prove_g2_runtime_to_m4_m8_real_mechanical_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_runtime_observation_without_outcome_stops_before_m4_m8(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(projection_request=req)
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert result.g2_real_source_used is True
    assert result.ddo_fixture_learning_state_used is False
    assert result.canonical_optimization_input_validated is False
    assert result.m4_m8_real_ingress_reached is False
    assert result.m4_m8_evidence_return_output_produced is False
    assert result.learning_evidence is None
    assert result.m4_m8_loop is None


@pytest.mark.parametrize(
    "mode",
    [RuntimePrimarySourceModeV1.PAPER, RuntimePrimarySourceModeV1.SHADOW],
)
def test_closure_does_not_prove_m4_m8_from_observation_only(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    assert not prove_g2_runtime_to_m4_m8_real_mechanical_v1(
        projection_request=projection_request(source_mode=mode, primary_root=root)
    )


def test_ddo_fixture_forbidden_on_continuation_request(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    fixture_state = _learning_state(tmp_path / "ddo")
    result = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=fixture_state,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"
    assert result.ddo_fixture_learning_state_used is False


def test_non_runtime_learning_evidence_rejected_at_plane_build(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state
    from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
        export_learning_evidence_from_state_v1,
    )
    from src.governance.governed_runtime_g2_to_m4_m8_real_mechanical_continuation_v1 import (
        build_bounded_offline_m4_plane_request_from_runtime_learning_evidence_v1,
        GovernedRuntimeG2M4M8ContinuationError,
    )

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.TESTNET)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.TESTNET, primary_root=root)
    ddo_evidence = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    with pytest.raises(GovernedRuntimeG2M4M8ContinuationError):
        build_bounded_offline_m4_plane_request_from_runtime_learning_evidence_v1(
            learning_evidence=ddo_evidence,
            projection_request=req,
        )


def test_observation_archive_cannot_reach_p5_bridge(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_g2_runtime_to_m4_m8_evidence_return_continuation_v1(
        G2RuntimeM4M8ContinuationRequestV1(
            projection_request=req,
            requested_p5_producer_bridge=True,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert result.m4_m8_loop is None


def test_authority_invariants_and_decision_config() -> None:
    assert prove_continuation_authority_invariants_v1() is True
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT) is True
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["real_runtime_g2_to_m4_m8_status"] == REAL_RUNTIME_G2_TO_M4_M8_STATUS
    assert decision["g2_end_to_end_status"] == G2_END_TO_END_STATUS
