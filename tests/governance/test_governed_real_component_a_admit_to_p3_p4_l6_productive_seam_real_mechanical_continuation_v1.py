"""Real Component A ADMIT → P3 binder → P4 L6 productive seam tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.governance.governed_real_component_a_admit_to_p3_p4_l6_productive_seam_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION,
    P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS,
    P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS,
    RealP3P4ProductiveSeamContinuationRequestV1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    prove_real_p3_p4_l6_productive_seam_continuation_v1,
    run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1,
    validate_real_component_a_to_p3_p4_lineage_join_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.binder_v1 import (
    bind_layer_input_from_adjudication_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.reason_codes_v1 import (
    LayerInputBindingIntakeFailureCodeV1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)
from tests.governance.test_master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1 import (
    _admit,
    _context,
    _request,
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
def test_observation_archive_cannot_reach_p3_or_p4(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "G2_ORIGINAL_OUTCOME_EVIDENCE_REQUIRED"
    assert result.ddo_fixture_state_used is False
    assert result.component_a_real_admit_used is False
    assert result.p3_input_creator_binder_reached is False
    assert result.p4_l6_seam_reached is False
    assert result.lineage_join_valid is False
    assert result.component_a_adjudication_disposition is None
    assert not prove_real_p3_p4_l6_productive_seam_continuation_v1(
        projection_request=req,
        repo_root=REPO_ROOT,
    )


def test_ddo_fixture_forbidden_on_real_p3_p4_path(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_real_runtime_to_p3_p4_l6_productive_seam_continuation_v1(
        RealP3P4ProductiveSeamContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"
    assert result.ddo_fixture_state_used is False


def test_lineage_join_rejects_missing_adjudication_ref() -> None:
    reasons = validate_real_component_a_to_p3_p4_lineage_join_v1(
        lineage_chain=("optimization_envelope://" + "a" * 64,),
        optimization_adjudication_digest="b" * 64,
        optimization_envelope_content_hash="a" * 64,
        expected_envelope_in_lineage="a" * 64,
    )
    assert "COMPONENT_A_ADJUDICATION_LINEAGE_MISSING" in reasons


def test_non_admit_component_a_rejects_p3_bind() -> None:
    admitted = _admit()
    assert admitted.disposition == ADMIT_DISPOSITION
    rejected = replace(admitted, disposition=REJECT_DISPOSITION)
    binding = bind_layer_input_from_adjudication_v1(_request(rejected), context=_context())
    assert binding.disposition == "NO_BIND"
    assert LayerInputBindingIntakeFailureCodeV1.ADJUDICATION_NOT_ADMIT.value in binding.reason_codes


def test_authority_gates_unchanged_and_invariants() -> None:
    assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    assert EVIDENCE_ADMIT_IMPLIES_PRODUCTIVE_ACTIVATION is False
    assert prove_continuation_authority_invariants_v1()


def test_decision_config_and_files() -> None:
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert (
        decision["p3_input_creator_binder_real_bind_status"]
        == P3_INPUT_CREATOR_BINDER_REAL_BIND_STATUS
    )
    assert (
        decision["p4_l6_productive_seam_real_bind_status"] == P4_L6_PRODUCTIVE_SEAM_REAL_BIND_STATUS
    )
    assert decision["runtime_apply_started"] is False
    assert decision["component_b_activated"] is False
