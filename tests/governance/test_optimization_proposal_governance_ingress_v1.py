"""Contract tests for optimization proposal governance ingress v1 (M10)."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

import pytest

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    RISK_CONSTRAINTS_REF as F2_RISK_CONSTRAINTS_REF,
    SURFACE_ID as F2_SURFACE_ID,
    SURFACE_OWNER_REF as F2_SURFACE_OWNER_REF,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    RISK_CONSTRAINTS_REF as F5_RISK_CONSTRAINTS_REF,
    SURFACE_ID as F5_SURFACE_ID,
    SURFACE_OWNER_REF as F5_SURFACE_OWNER_REF,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    RISK_CONSTRAINTS_REF as M9_RISK_CONSTRAINTS_REF,
    SURFACE_ID as M9_SURFACE_ID,
    SURFACE_OWNER_REF as M9_SURFACE_OWNER_REF,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    SYNTHETIC_OFFLINE_SURFACE_ID,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
    build_optimization_experiment_evidence_from_plane_v1,
    validate_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    PROPOSAL_DISPOSITION,
    SCHEMA_VERSION as EXPERIMENT_PLANE_SCHEMA_VERSION,
    run_optimization_universe_experiment_plane_v1,
)
from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    ADMISSION_DENIED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    OptimizationProposalGovernanceIngressError,
    SCHEMA_VERSION,
    INGRESS_DOMAIN,
    PROMOTION_AUTHORITY,
    PRODUCTIVE_APPLY_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
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
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex


_SURFACE_CONSTRAINT_REFS: Final[dict[str, tuple[str, str]]] = {
    M9_SURFACE_ID: (M9_RISK_CONSTRAINTS_REF, M9_SURFACE_OWNER_REF),
    F2_SURFACE_ID: (F2_RISK_CONSTRAINTS_REF, F2_SURFACE_OWNER_REF),
    F5_SURFACE_ID: (F5_RISK_CONSTRAINTS_REF, F5_SURFACE_OWNER_REF),
}


def _surface_constraint_refs_v1(surface_id: str) -> tuple[str, str]:
    entry = _SURFACE_CONSTRAINT_REFS.get(surface_id)
    if entry is None:
        raise OptimizationProposalGovernanceIngressError(
            f"UNKNOWN_OPTIMIZATION_SURFACE:{surface_id}"
        )
    risk_ref, owner_ref = entry
    return risk_ref, owner_ref


def _build_legacy_plane_ingress_fixture(
    *,
    plane_result: Mapping[str, Any],
    optimization_experiment_evidence: Mapping[str, Any],
    optimization_surface_id: str,
    parameter_config_delta: Mapping[str, Any] | None = None,
    requested_productive_target: str | None = None,
    historical_direct_handoff: bool = False,
) -> MappingProxyType[str, Any]:
    """Historical M4/M5 payload for downstream governance contract tests."""
    if plane_result.get("schema_version") != EXPERIMENT_PLANE_SCHEMA_VERSION:
        raise OptimizationProposalGovernanceIngressError("PLANE_SCHEMA_VERSION_MISMATCH")
    if plane_result.get("status") != PLANE_STATUS_COMPLETE:
        raise OptimizationProposalGovernanceIngressError("PLANE_STATUS_NOT_COMPLETE")

    evidence = validate_optimization_experiment_evidence_v1(optimization_experiment_evidence)
    plane_identity = str(plane_result.get("plane_identity") or "")
    if plane_identity != str(evidence.get("plane_identity") or ""):
        raise OptimizationProposalGovernanceIngressError("PLANE_IDENTITY_MISMATCH")
    plane_digest = plane_result.get("result_digest")
    if plane_digest and evidence.get("provenance", {}).get("plane_result_digest") != plane_digest:
        raise OptimizationProposalGovernanceIngressError("PLANE_RESULT_DIGEST_MISMATCH")

    chain = plane_result.get("chain")
    if not isinstance(chain, Mapping):
        raise OptimizationProposalGovernanceIngressError("PLANE_CHAIN_MISSING")
    proposal = chain.get("proposal")
    selected = chain.get("selected_candidate")
    learning_input = chain.get("learning_input_validation")
    if not isinstance(proposal, Mapping) or not isinstance(selected, Mapping):
        raise OptimizationProposalGovernanceIngressError("PROPOSAL_OR_CANDIDATE_MISSING")
    if not isinstance(learning_input, Mapping):
        raise OptimizationProposalGovernanceIngressError("LEARNING_INPUT_VALIDATION_MISSING")

    if proposal.get("disposition") != PROPOSAL_DISPOSITION:
        raise OptimizationProposalGovernanceIngressError("PROPOSAL_DISPOSITION_NOT_PROPOSAL_ONLY")

    surface_id = optimization_surface_id.strip()
    if not surface_id:
        raise OptimizationProposalGovernanceIngressError("OPTIMIZATION_SURFACE_ID_REQUIRED")

    delta = (
        dict(parameter_config_delta)
        if parameter_config_delta is not None
        else dict(selected.get("parameter_region") or {})
    )
    if not delta:
        raise OptimizationProposalGovernanceIngressError("PARAMETER_CONFIG_DELTA_EMPTY")

    envelope_resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    if envelope_resolution.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise OptimizationProposalGovernanceIngressError(
            f"ENVELOPE_NOT_AUTHORIZED:{envelope_resolution.get('reason')}"
        )

    envelope_identity = str(envelope_resolution.get("envelope_identity") or "")
    if not is_valid_sha256_hex(envelope_identity):
        raise OptimizationProposalGovernanceIngressError("ENVELOPE_IDENTITY_INVALID")

    risk_constraints_ref, owner_auth_ref = _surface_constraint_refs_v1(surface_id)
    if not risk_constraints_ref:
        raise OptimizationProposalGovernanceIngressError("RISK_CONSTRAINTS_REF_MISSING")

    experiment_id = str(selected.get("experiment_id") or proposal.get("experiment_id") or "")
    candidate_ref = str(selected.get("candidate_ref") or proposal.get("candidate_ref") or "")
    if not experiment_id or not candidate_ref:
        raise OptimizationProposalGovernanceIngressError("EXPERIMENT_OR_CANDIDATE_REF_MISSING")

    learning_digest = str(learning_input.get("learning_evidence_digest") or "")
    if not is_valid_sha256_hex(learning_digest):
        raise OptimizationProposalGovernanceIngressError("LEARNING_EVIDENCE_DIGEST_INVALID")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": INGRESS_DOMAIN,
        "disposition": DISPOSITION_PROPOSAL_ONLY,
        "plane_identity": plane_identity,
        "experiment_id": experiment_id,
        "candidate_ref": candidate_ref,
        "optimization_surface_id": surface_id,
        "parameter_config_delta": delta,
        "requested_productive_target": requested_productive_target,
        "optimization_evidence_record_id": evidence.get("record_id"),
        "optimization_evidence_content_hash": evidence.get("content_hash"),
        "optimization_evidence_reproducibility_digest": evidence.get("reproducibility_digest"),
        "learning_evidence_digest": learning_digest,
        "plane_result_digest": plane_digest,
        "search_identity": chain.get("search_identity"),
        "template_identity_digest": chain.get("template_identity_digest"),
        "envelope_identity": envelope_identity,
        "envelope_owner_authorization_ref": owner_auth_ref,
        "risk_constraints_ref": risk_constraints_ref,
        "governance_risk_constraints_ref": risk_constraints_ref,
        "envelope_resolution_digest": envelope_resolution.get("result_digest"),
        "promotion_authority": PROMOTION_AUTHORITY,
        "productive_apply_authority": PRODUCTIVE_APPLY_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "optimization_provenance": {
            "source_plane_schema_version": EXPERIMENT_PLANE_SCHEMA_VERSION,
            "source_evidence_schema_version": OPTIMIZATION_EXPERIMENT_EVIDENCE_SCHEMA_VERSION,
            "plane_result_digest": plane_digest,
            "evidence_content_hash": evidence.get("content_hash"),
            "evidence_record_id": evidence.get("record_id"),
            "reproducibility_digest": evidence.get("reproducibility_digest"),
            "proposal_disposition": proposal.get("disposition"),
            "proposal_not_authority": proposal.get("proposal_not_authority"),
            "identity_digest": proposal.get("identity_digest"),
            "robustness_suite_identity": proposal.get("robustness_suite_identity"),
            "evidence_slices_digest": compute_content_sha256(
                {"evidence_slices": evidence.get("evidence_slices")}
            ),
            "ingress_is_not_config_patch": True,
            "config_patch_is_downstream_projection_only": True,
        },
    }
    if not historical_direct_handoff:
        provenance = body["optimization_provenance"]
        provenance.pop("source_plane_schema_version")
        provenance["source"] = "TEST_ONLY_GOVERNANCE_PROPOSAL"
    body["ingress_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "ingress_digest"}
    )
    return MappingProxyType(body)


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
    return _build_legacy_plane_ingress_fixture(
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


def test_historical_direct_m4_m5_handoff_is_denied(tmp_path: Path) -> None:
    plane, evidence = _plane_and_evidence(tmp_path)
    ingress = _build_legacy_plane_ingress_fixture(
        plane_result=plane,
        optimization_experiment_evidence=evidence,
        optimization_surface_id=M9_SURFACE_ID,
        parameter_config_delta={"max_age_seconds": 300},
        historical_direct_handoff=True,
    )
    result = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert result.admission_status == ADMISSION_DENIED
    assert result.reason_codes == ("DIRECT_M4_M5_GOVERNANCE_HANDOFF_RETIRED",)
    assert result.config_patch_manifest_projection is None


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
        _build_legacy_plane_ingress_fixture(
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
