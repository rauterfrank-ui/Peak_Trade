"""Governed productive configuration apply authority v1 — F1/M9 proof and negative safety."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    bind_authorized_productive_parameter_seam_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    PRODUCTIVE_TARGET_ID,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.governed_productive_configuration_apply_authority_closure_v1 import (
    prove_governed_productive_configuration_apply_authority_v1,
)
from src.governance.governed_productive_configuration_apply_authority_v1 import (
    APPLY_AUTHORITY_ID,
    ApplyAuthorityCallerClassV1,
    GovernedProductiveConfigurationApplyEvaluateRequestV1,
    apply_authorization_implies_external_effect_v1,
    evaluate_governed_productive_configuration_apply_v1,
    experiment_evidence_implies_apply_authorization_v1,
    m10_authorization_alone_produces_applied_state_v1,
    meta_learning_can_invoke_apply_authority_v1,
    optimization_can_invoke_apply_authority_v1,
    p5_evidence_intake_implies_apply_authorization_v1,
    primary_runtime_evidence_implies_apply_authorization_v1,
    prove_negative_apply_authority_safety_invariants_v1,
)
from src.governance.governed_productive_configuration_apply_record_v1 import (
    ProductiveConfigurationApplyDecisionStateV1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
)
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    M10PromotionBoundaryEvaluateRequestV1,
    M10PromotionState,
    build_m10_promotion_proposal_from_ingress_v1,
    evaluate_m10_promotion_boundary_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from tests.governance.test_m10_promotion_boundary_v1 import _ingress_for_surface
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _f1_m9_chain(tmp_path: Path) -> dict[str, Any]:
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert admission.admission_status == ADMISSION_ADMITTED
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=configuration)
    )
    proposal = build_m10_promotion_proposal_from_ingress_v1(ingress)
    m10 = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert m10.promotion_state == M10PromotionState.AUTHORIZED
    assert m10.authorized_promotion_record is not None
    return {
        "ingress": ingress,
        "configuration": configuration,
        "seam": seam,
        "promotion": dict(m10.authorized_promotion_record),
    }


def test_closure_proof_passes() -> None:
    assert prove_governed_productive_configuration_apply_authority_v1(repo_root=REPO_ROOT)


def test_f1_m9_bounded_apply_eligible_and_authorized(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    eligible = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=chain["promotion"],
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
            request_apply_authorization=False,
        )
    )
    assert eligible.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_ELIGIBLE
    assert eligible.apply_record is not None
    rec = eligible.apply_record.apply_record
    assert rec["apply_authority_id"] == APPLY_AUTHORITY_ID
    assert rec["decision_state"] == ProductiveConfigurationApplyDecisionStateV1.APPLY_ELIGIBLE.value
    assert rec["runtime_materialization_performed"] is False
    assert rec["runtime_apply_started"] is False
    assert "applied_at" not in rec

    authorized = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=chain["promotion"],
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
            request_apply_authorization=True,
        )
    )
    assert authorized.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_AUTHORIZED
    assert authorized.apply_record is not None
    assert (
        authorized.apply_record.apply_record["decision_state"]
        == ProductiveConfigurationApplyDecisionStateV1.APPLY_AUTHORIZED.value
    )
    assert authorized.external_effect_authorized is False


def test_missing_m10_authorization_denied(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    promotion = dict(chain["promotion"])
    promotion.pop("authorized_promotion_record_digest", None)
    result = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=promotion,
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
        )
    )
    assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED
    assert "M10_AUTHORIZED_RECORD_DIGEST_INVALID" in result.reason_codes


def test_malformed_m10_authorization_denied(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    promotion = dict(chain["promotion"])
    promotion["authorized_promotion_record_digest"] = "0" * 64
    result = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=promotion,
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
        )
    )
    assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED


def test_surface_mismatch_denied(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    promotion = dict(chain["promotion"])
    promotion["surface_id"] = "wrong_surface"
    result = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=promotion,
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
        )
    )
    assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED
    assert "SURFACE_MISMATCH" in result.reason_codes


def test_unratified_f2_surface_denied(tmp_path: Path) -> None:
    ingress = _ingress_for_surface(
        tmp_path,
        F2_SURFACE_ID,
        {"baseline_fee_bps": 2.0, "baseline_slippage_bps": 1.0},
    )
    chain = _f1_m9_chain(tmp_path)
    promotion = dict(chain["promotion"])
    promotion["surface_id"] = F2_SURFACE_ID
    result = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=promotion,
            ingress=ingress,
            configuration=chain["configuration"],
            seam=chain["seam"],
        )
    )
    assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED
    assert "UNSUPPORTED_SURFACE_RESEARCH_OR_SHADOW_ONLY" in result.reason_codes


def test_candidate_and_value_mismatch_denied(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    promotion = dict(chain["promotion"])
    promotion["candidate_ref"] = "wrong_candidate"
    result = evaluate_governed_productive_configuration_apply_v1(
        GovernedProductiveConfigurationApplyEvaluateRequestV1(
            authorized_promotion_record=promotion,
            ingress=chain["ingress"],
            configuration=chain["configuration"],
            seam=chain["seam"],
        )
    )
    assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED
    assert "CANDIDATE_ID_MISMATCH" in result.reason_codes


def test_caller_class_negative_proofs(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    for caller, code in (
        (ApplyAuthorityCallerClassV1.OPTIMIZATION, "OPTIMIZATION_CANNOT_INVOKE_APPLY_AUTHORITY"),
        (
            ApplyAuthorityCallerClassV1.META_LEARNING,
            "META_LEARNING_CANNOT_INVOKE_APPLY_AUTHORITY",
        ),
        (
            ApplyAuthorityCallerClassV1.P5_EVIDENCE,
            "P5_EVIDENCE_INTAKE_CANNOT_INVOKE_APPLY_AUTHORITY",
        ),
        (
            ApplyAuthorityCallerClassV1.PRIMARY_RUNTIME_EVIDENCE,
            "PRIMARY_RUNTIME_EVIDENCE_CANNOT_INVOKE_APPLY_AUTHORITY",
        ),
        (
            ApplyAuthorityCallerClassV1.EXPERIMENT_EVIDENCE,
            "EXPERIMENT_EVIDENCE_CANNOT_INVOKE_APPLY_AUTHORITY",
        ),
        (
            ApplyAuthorityCallerClassV1.M10_PROMOTION_ONLY,
            "M10_AUTHORIZATION_ALONE_INSUFFICIENT_FOR_APPLY",
        ),
    ):
        result = evaluate_governed_productive_configuration_apply_v1(
            GovernedProductiveConfigurationApplyEvaluateRequestV1(
                authorized_promotion_record=chain["promotion"],
                ingress=chain["ingress"],
                configuration=chain["configuration"],
                seam=chain["seam"],
                caller_class=caller,
            )
        )
        assert result.decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED
        assert code in result.reason_codes


def test_global_negative_invariants() -> None:
    assert prove_negative_apply_authority_safety_invariants_v1()
    assert AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is False
    assert optimization_can_invoke_apply_authority_v1() is False
    assert meta_learning_can_invoke_apply_authority_v1() is False
    assert p5_evidence_intake_implies_apply_authorization_v1() is False
    assert primary_runtime_evidence_implies_apply_authorization_v1() is False
    assert experiment_evidence_implies_apply_authorization_v1() is False
    assert m10_authorization_alone_produces_applied_state_v1() is False
    assert apply_authorization_implies_external_effect_v1() is False


def test_m10_surface_id_matches_m9(tmp_path: Path) -> None:
    chain = _f1_m9_chain(tmp_path)
    assert chain["promotion"]["surface_id"] == M9_SURFACE_ID
