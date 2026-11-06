"""F1/M9 scoped Owner Apply execution real mechanical continuation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.f1_m9_scoped_owner_apply_authority_v1 import RUNTIME_APPLY_AUTHORITY_VALUE
from src.governance.governed_f1_m9_scoped_owner_apply_execution_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_apply_execution_v1,
)
from src.governance.governed_f1_m9_scoped_owner_apply_execution_evidence_v1 import (
    F1M9ApplyExecutionPhaseStateV1,
)
from src.governance.governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1 import (
    DECISION_CONFIG,
    F1M9PerIngressExecutionContextV1,
    GovernedF1M9ApplyExecutionContinuationRequestV1,
    REAL_P4_TO_F1_M9_JOIN_STATUS,
    RUNTIME_APPLY_STARTED,
    build_f1_m9_per_ingress_context_from_admitted_ingress_v1,
    prove_continuation_authority_invariants_v1,
    prove_continuation_decision_files_v1,
    run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1,
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
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import (
    evaluate_real_p4_to_f1_m9_apply_join_v1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)
from tests.governance.test_f1_m9_scoped_owner_apply_authority_v1 import (
    _build_chain_artifacts,
    _ledger_paths,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


def _f1_context(tmp_path: Path) -> F1M9PerIngressExecutionContextV1:
    artifacts = _build_chain_artifacts(tmp_path)
    paths = _ledger_paths(tmp_path)
    return F1M9PerIngressExecutionContextV1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        binding=artifacts["binding"],
        authorization=artifacts["authorization"],
        configuration=artifacts["configuration"],
        registry_digest=artifacts["registry_digest"],
        ledger_paths=paths,
        offline_plane_workspace=tmp_path,
        real_upstream_source_used=False,
        ddo_fixture_state_used=True,
    )


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
    ],
)
def test_real_p4_boundary_plus_f1_m9_apply_execution_proof(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    req = projection_request(source_mode=mode, primary_root=root)
    result = run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1(
        GovernedF1M9ApplyExecutionContinuationRequestV1(
            projection_request=req,
            f1_m9_context=_f1_context(tmp_path / "f1"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE", result.blocking_reasons
    assert result.real_upstream_source_used is True
    assert result.p4_l6_real_seam_used is True
    assert result.runtime_materialization_record_used is True
    assert result.real_p4_to_f1_m9_join_status == REAL_P4_TO_F1_M9_JOIN_STATUS
    assert result.f1_m9_canonical_apply_owner_used is True
    assert result.apply_completed is True
    assert result.configuration_runtime_applied is True
    assert result.apply_started is True
    assert result.ddo_fixture_state_used_on_real_path is False
    assert result.f1_m9_per_ingress_real_upstream_source_used is False
    assert result.apply_execution_evidence is not None
    assert (
        result.apply_execution_evidence.phase_state
        == F1M9ApplyExecutionPhaseStateV1.APPLY_COMPLETED
    )
    assert result.value_ratification_status == "THRESHOLD_HOT_PATH_NOT_RATIFIED"


def test_ddo_forbidden_on_real_p4_leg(tmp_path: Path) -> None:
    from tests.learning.test_learning_evidence_export_v1 import _learning_state

    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1(
        GovernedF1M9ApplyExecutionContinuationRequestV1(
            projection_request=req,
            f1_m9_context=_f1_context(tmp_path / "f1"),
            ddo_fixture_learning_state=_learning_state(tmp_path / "ddo"),
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "REJECTED"


def test_out_of_domain_m9_value_rejected_at_configuration_materialization(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path, parameter_config_delta={"fast": 10})
    ctx = build_f1_m9_per_ingress_context_from_admitted_ingress_v1(
        ingress=ingress,
        workspace=tmp_path,
        repo_root=REPO_ROOT,
    )
    from src.governance.governed_productive_configuration_v1 import STATUS_MATERIALIZED

    assert ctx.configuration.configuration_status != STATUS_MATERIALIZED


def test_join_negative_with_mismatched_configuration(tmp_path: Path) -> None:
    from src.governance.governed_runtime_apply_materialization_record_v1 import (
        RuntimeApplyMaterializationDecisionStateV1,
        build_materialization_record_body_v1,
        compute_lineage_chain_digest_v1,
    )

    artifacts = _build_chain_artifacts(tmp_path)
    p4 = "a" * 64
    lineage = compute_lineage_chain_digest_v1(lineage_chain=(f"p4_l6_seam://{p4}",))
    record = dict(
        build_materialization_record_body_v1(
            decision_state=RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_AUTHORIZED,
            p4_l6_seam_result_digest=p4,
            p3_binding_result_digest="b" * 64,
            component_a_adjudication_digest="c" * 64,
            optimization_envelope_content_hash="d" * 64,
            lineage_chain_digest=lineage,
            reason_codes=("T",),
            real_runtime_materialization_performed=True,
        )
    )
    record["source_configuration_digest"] = "0" * 64
    join = evaluate_real_p4_to_f1_m9_apply_join_v1(
        materialization_record=record,
        configuration=artifacts["configuration"],
    )
    assert join.join_permitted is False
    assert "CROSS_PLANE_CONFIGURATION_DIGEST_MISMATCH" in join.reason_codes


def test_closure_and_invariants() -> None:
    assert prove_governed_f1_m9_scoped_owner_apply_execution_v1(repo_root=REPO_ROOT)
    assert prove_continuation_decision_files_v1(repo_root=REPO_ROOT)
    assert prove_continuation_authority_invariants_v1()
    assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False


def test_decision_config() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["real_p4_to_f1_m9_join_status"] == REAL_P4_TO_F1_M9_JOIN_STATUS
    assert decision["runtime_apply_started"] is False


def test_runtime_applied_uses_scoped_authority(tmp_path: Path) -> None:
    ctx = _f1_context(tmp_path)
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    result = run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1(
        GovernedF1M9ApplyExecutionContinuationRequestV1(
            projection_request=req,
            f1_m9_context=ctx,
            repo_root=REPO_ROOT,
        )
    )
    assert result.status == "CONTINUATION_COMPLETE"
    rec = result.apply_execution_evidence
    assert rec is not None
    assert rec.configuration_runtime_applied is True
    assert rec.threshold_value_ratified is False
    assert rec.candidate_value_applied is False
