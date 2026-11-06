"""Real P4 L6 → runtime apply materialization continuation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    P4_L6_REAL_SEAM_STATUS,
    RealP4RuntimeApplyMaterializationContinuationRequestV1,
    RUNTIME_APPLY_STARTED,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    prove_real_p4_l6_runtime_apply_materialization_continuation_v1,
    run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1,
)
from src.governance.governed_runtime_apply_materialization_v1 import (
    RuntimeApplyMaterializationCallerClassV1,
    RuntimeApplyMaterializationEvaluateRequestV1,
    RuntimeApplyMaterializationIngressV1,
    evaluate_runtime_apply_materialization_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
    RuntimePrimarySourceModeV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    SEAM_BIND_DISPOSITION,
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
def test_real_runtime_through_runtime_apply_materialization(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1(
        RealP4RuntimeApplyMaterializationContinuationRequestV1(
            projection_request=req,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.real_upstream_source_used is True
    assert result.ddo_fixture_state_used is False
    assert result.p4_l6_real_seam_used is True
    assert result.p4_seam_disposition == SEAM_BIND_DISPOSITION
    assert result.runtime_apply_ingress_reached is True
    assert result.runtime_materialization_performed is True
    assert result.apply_record_produced is True
    assert result.configuration_materialized is True
    assert result.configuration_applied is False
    assert result.lineage_join_valid is True
    assert prove_real_p4_l6_runtime_apply_materialization_continuation_v1(
        projection_request=req,
        repo_root=REPO_ROOT,
    )


def test_ddo_fixture_forbidden_on_real_runtime_apply_path(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1(
        RealP4RuntimeApplyMaterializationContinuationRequestV1(
            projection_request=req,
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"
    assert result.decision_code == "DDO_FIXTURE_LEARNING_STATE_FORBIDDEN_ON_REAL_PATH"


def test_lineage_mismatch_denies_materialization() -> None:
    ingress = RuntimeApplyMaterializationIngressV1(
        p4_l6_seam_result_digest="a" * 64,
        p3_binding_result_digest="b" * 64,
        component_a_adjudication_digest="c" * 64,
        optimization_envelope_content_hash="d" * 64,
        p4_seam_disposition=SEAM_BIND_DISPOSITION,
        lineage_chain=("optimization_envelope://" + "e" * 64,),
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
    )
    denied = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(ingress=ingress),
        repo_root=REPO_ROOT,
    )
    assert denied.decision_state.value == "MATERIALIZATION_DENIED"


def test_component_b_caller_denied() -> None:
    ingress = RuntimeApplyMaterializationIngressV1(
        p4_l6_seam_result_digest="a" * 64,
        p3_binding_result_digest="b" * 64,
        component_a_adjudication_digest="c" * 64,
        optimization_envelope_content_hash="d" * 64,
        p4_seam_disposition=SEAM_BIND_DISPOSITION,
        lineage_chain=(
            f"optimization_envelope://{'d' * 64}",
            f"adjudicator_a_opt://{'c' * 64}",
            f"p3_binding://{'b' * 64}",
            f"p4_l6_seam://{'a' * 64}",
        ),
        real_upstream_source_used=True,
        ddo_fixture_state_used=False,
    )
    denied = evaluate_runtime_apply_materialization_v1(
        RuntimeApplyMaterializationEvaluateRequestV1(
            ingress=ingress,
            caller_class=RuntimeApplyMaterializationCallerClassV1.COMPONENT_B,
        ),
        repo_root=REPO_ROOT,
    )
    assert denied.reason_codes[0] == "COMPONENT_B_CANNOT_INVOKE_RUNTIME_APPLY_MATERIALIZATION"


def test_authority_gates_unchanged() -> None:
    assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    assert prove_continuation_authority_invariants_v1()


def test_decision_config() -> None:
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["p4_l6_real_seam_status"] == P4_L6_REAL_SEAM_STATUS
    assert decision["runtime_apply_started"] is False
    assert decision["productive_activation_authorized"] is False
