"""M10 promotion boundary v1 — Phase 13 negative proofs and F1/M9 reference path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.governance.explicit_productive_authorization_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_owner_explicit_productive_authorization_input_v1,
    compute_owner_authorization_record_digest_v1,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    M10PromotionBoundaryEvaluateRequestV1,
    M10PromotionState,
    OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
    OPTIMIZATION_PROMOTION_AUTHORITY,
    build_m10_promotion_proposal_from_ingress_v1,
    compute_promotion_proposal_digest_v1,
    evaluate_m10_promotion_boundary_v1,
    replay_m10_promotion_boundary_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
    _plane_and_evidence,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)


def _ingress_for_surface(tmp_path: Path, surface_id: str, delta: dict[str, Any]):
    plane, opt_evidence = _plane_and_evidence(tmp_path)
    return build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=opt_evidence,
        optimization_surface_id=surface_id,
        parameter_config_delta=delta,
    )


def _rehash_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    mutated = dict(proposal)
    mutated["proposal_digest"] = compute_promotion_proposal_digest_v1(mutated)
    return mutated


def _m9_bundle(tmp_path: Path):
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert admission.admission_status == ADMISSION_ADMITTED
    proposal = build_m10_promotion_proposal_from_ingress_v1(ingress)
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    return ingress, admission, proposal, owner_input


def test_f1_m9_authorized_promotion_record_without_runtime_apply(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.AUTHORIZED
    assert result.authorized_promotion_record is not None
    rec = result.authorized_promotion_record
    assert rec["runtime_apply_authorized"] is False
    assert rec["productive_configuration_write_authorized"] is False
    assert rec["external_effect_authorized"] is False
    assert rec["optimization_promotion_authority"] == "NONE"
    assert rec["trading_decision_authority_owner"] == TRADING_DECISION_AUTHORITY_OWNER
    assert rec["current_consumer_module"] == (
        "src/governance/f1_m9_bounded_threshold_enforcement_mv2_consumer_v1.py"
    )
    assert replay_m10_promotion_boundary_v1(
        promotion_proposal=proposal,
        ingress=ingress,
        governance_admission=admission,
        owner_authorization_input=owner_input,
        prior_result=result,
    )


def test_proposal_alone_stops_at_validated(tmp_path: Path) -> None:
    ingress, admission, proposal, _ = _m9_bundle(tmp_path)
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=None,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.VALIDATED
    assert result.authorized_promotion_record is None
    assert "EXPLICIT_AUTHORIZATION_REQUIRED_FOR_PROMOTION" in result.reason_codes


def test_missing_authorization_fails_closed(tmp_path: Path) -> None:
    test_proposal_alone_stops_at_validated(tmp_path)


def test_wrong_owner_authorization_id_denied(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    record = dict(owner_input.owner_authorization_record)
    record["owner_authorization_id"] = "unknown_owner/v1"
    bad = type(owner_input)(
        owner_authorization_record=record,
        owner_authorization_record_digest=compute_owner_authorization_record_digest_v1(record),
    )
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=bad,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "OWNER_AUTHORIZATION_ID_NOT_ALLOWED" in result.reason_codes


def test_wrong_ingress_digest_in_proposal_rejected(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    mutated = dict(proposal)
    mutated["ingress_digest"] = "0" * 64
    mutated["proposal_digest"] = proposal["proposal_digest"]
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=mutated,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert result.promotion_state in (M10PromotionState.REJECTED, M10PromotionState.INVALID)


def test_wrong_candidate_digest_rejected(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    mutated = _rehash_proposal({**proposal, "candidate_parameter_value_digest": "0" * 64})
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=mutated,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "CANDIDATE_DIGEST_MISMATCH" in result.reason_codes


def test_out_of_domain_candidate_rejected(tmp_path: Path) -> None:
    ingress = _ingress_for_m9(tmp_path, parameter_config_delta={"fast": 10})
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    assert admission.admission_status != ADMISSION_ADMITTED


def test_f2_research_only_cannot_promote(tmp_path: Path) -> None:
    ingress = _ingress_for_surface(
        tmp_path,
        F2_SURFACE_ID,
        {"fee_bps": BASELINE_FEE_BPS, "slippage_bps": BASELINE_SLIPPAGE_BPS},
    )
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    proposal = build_m10_promotion_proposal_from_ingress_v1(ingress)
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "RESEARCH_ONLY_SURFACE_PROMOTION_FORBIDDEN" in result.reason_codes


def test_f5_fresh_research_only_cannot_promote(tmp_path: Path) -> None:
    ingress = _ingress_for_surface(tmp_path, F5_SURFACE_ID, {"max_age_seconds": 60})
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    proposal = build_m10_promotion_proposal_from_ingress_v1(ingress)
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "RESEARCH_ONLY_SURFACE_PROMOTION_FORBIDDEN" in result.reason_codes


def test_requested_runtime_apply_forbidden(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=owner_input,
            requested_runtime_apply=True,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "REQUESTED_RUNTIME_APPLY_FORBIDDEN" in result.reason_codes


def test_authority_invariant_pins() -> None:
    assert OPTIMIZATION_PROMOTION_AUTHORITY == "NONE"
    assert OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE is False
    assert AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is False
    assert OPTIMIZATION_CORE_MUTATION_AUTHORITY == "NONE"
    assert LEARNING_CORE_MUTATION_AUTHORITY == "NONE"
    assert runtime_apply_possible_v1() is False


def test_wrong_productive_target_in_proposal_rejected(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    mutated = _rehash_proposal(
        {
            **proposal,
            "productive_target_id": "peak_trade.governance.productive_target.unknown/v1",
        }
    )
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=mutated,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED


def test_wrong_consumer_module_rejected(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    mutated = _rehash_proposal({**proposal, "current_consumer_module": "src/unknown_consumer.py"})
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=mutated,
            governance_admission=admission,
            owner_authorization_input=owner_input,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED
    assert "CONSUMER_MODULE_MISMATCH" in result.reason_codes


def test_meta_learning_cannot_self_authorize(tmp_path: Path) -> None:
    ingress, admission, proposal, owner_input = _m9_bundle(tmp_path)
    record = dict(owner_input.owner_authorization_record)
    record["authorizer_identity"] = "META_LEARNING_SELF_AUTHORIZE"
    record["owner_authorization_id"] = "meta_learning_self/v1"
    bad = type(owner_input)(
        owner_authorization_record=record,
        owner_authorization_record_digest=compute_owner_authorization_record_digest_v1(record),
    )
    result = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=bad,
        ),
        ingress=ingress,
    )
    assert result.promotion_state == M10PromotionState.REJECTED


def test_surface_id_m9_only_for_productive_promotion(tmp_path: Path) -> None:
    ingress, _, proposal, _ = _m9_bundle(tmp_path)
    assert proposal["surface_id"] == M9_SURFACE_ID
