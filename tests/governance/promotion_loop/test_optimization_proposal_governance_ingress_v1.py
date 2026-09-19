"""Contract tests for optimization proposal governance ingress v1 (M10)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    run_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import SYNTHETIC_OFFLINE_SURFACE_ID
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.promotion_loop.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    ADMISSION_DENIED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    OptimizationProposalGovernanceIngressError,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
    direct_productive_write_possible_v1,
    evaluate_optimization_proposal_governance_admission_v1,
    optimization_ingress_contract_fence_layer_v1,
    project_optimization_ingress_to_config_patch_manifest_v1,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.governance.promotion_loop.policy import AutoApplyPolicy
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state


def _plane_and_evidence(tmp_path: Path) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    plane = run_optimization_universe_experiment_plane_v1(_plane_request(evidence))
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    return plane, opt_evidence


def _ingress_for_m9(
    tmp_path: Path,
    *,
    parameter_config_delta: Mapping[str, Any] | None = None,
    surface_id: str = M9_SURFACE_ID,
) -> Mapping[str, Any]:
    plane, opt_evidence = _plane_and_evidence(tmp_path)
    delta = parameter_config_delta or {"max_age_seconds": 300}
    return build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=opt_evidence,
        optimization_surface_id=surface_id,
        parameter_config_delta=dict(delta),
    )


def test_admitted_for_governance_review_m9_surface(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path)
    assert ingress["disposition"] == DISPOSITION_PROPOSAL_ONLY
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert result.admission_status == ADMISSION_ADMITTED
    assert result.promotion_authority == "NONE"
    assert result.productive_apply_authority == "NONE"
    assert result.config_patch_manifest_projection is not None
    meta = result.config_patch_manifest_projection.metadata
    assert meta.get("optimization_provenance_preserved") is True
    provenance = result.config_patch_manifest_projection.source_scope.get("optimization_provenance")
    assert provenance.get("ingress_is_not_config_patch") is True


def test_requested_promotion_denied(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path)
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(
            ingress=ingress,
            requested_promotion=True,
        )
    )
    assert result.admission_status == ADMISSION_DENIED
    assert "REQUESTED_PROMOTION_FORBIDDEN" in result.reason_codes


def test_requested_productive_apply_denied(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path)
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(
            ingress=ingress,
            requested_productive_apply=True,
        )
    )
    assert result.admission_status == ADMISSION_DENIED


def test_unknown_surface_denied(tmp_path: Path) -> None:
    plane, opt_evidence = _plane_and_evidence(tmp_path)
    with pytest.raises(OptimizationProposalGovernanceIngressError):
        build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
            plane_result=plane,
            optimization_experiment_evidence=opt_evidence,
            optimization_surface_id=SYNTHETIC_OFFLINE_SURFACE_ID,
            parameter_config_delta={"max_age_seconds": 300},
        )


def test_candidate_target_mismatch_denied(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path, parameter_config_delta={"fast": 10})
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert result.admission_status == ADMISSION_DENIED
    assert "CANDIDATE_TARGET_MISMATCH" in result.reason_codes


def test_missing_provenance_field_denied(tmp_path: Path) -> None:
    ingress = dict(_ingress_for_m9(tmp_path))
    ingress.pop("optimization_provenance")
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert result.admission_status == ADMISSION_DENIED


def test_config_patch_projection_preserves_lineage(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path)
    manifest = project_optimization_ingress_to_config_patch_manifest_v1(ingress)
    patch = manifest.patches[0]
    assert patch.status.value == "PROPOSED"
    assert patch.meta.get("ingress_is_authoritative_provenance") is True
    assert patch.meta.get("optimization_ingress_digest") == ingress["ingress_digest"]
    assert manifest.source_scope.get("ingress_digest") == ingress["ingress_digest"]


def test_live_override_writer_fail_closed() -> None:
    assert (
        apply_proposals_to_live_overrides(
            [], policy=AutoApplyPolicy(), live_override_path=Path("x")
        )
        is None
    )


def test_direct_productive_write_impossible() -> None:
    assert direct_productive_write_possible_v1() is False


def test_ingress_deterministic(tmp_path: Path) -> None:
    first = _ingress_for_m9(tmp_path)
    second = _ingress_for_m9(tmp_path)
    assert first["ingress_digest"] == second["ingress_digest"]
    validate_optimization_proposal_governance_ingress_v1(first)


def test_fence_layer_before_productive_mutation() -> None:
    layers = optimization_ingress_contract_fence_layer_v1()
    assert layers.index("PROPOSAL") < layers.index("PRODUCTIVE_MUTATION")
