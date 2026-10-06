"""GHV-referenced complete intelligence superstructure offline cycle v1 (compose-only).

Single bounded offline entrypoint composing existing M4–M8, governance ingress, M10 boundary,
and GVEF-style reproof. Terminates at M10 HARD STOP (no Owner-GO, no apply, no POST).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopError,
    M4M8EvidenceReturnLoopRequestV1,
    run_m4_m8_evidence_return_loop_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    OptimizationUniverseExperimentPlaneRequestV1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    M10PromotionBoundaryEvaluateRequestV1,
    M10PromotionState,
    build_m10_promotion_proposal_from_ingress_v1,
    evaluate_m10_promotion_boundary_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.ghv_intelligence_lineage_completeness_v1 import (
    derive_realized_economic_completeness_v1,
    derive_structural_outcome_completeness_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1"
CYCLE_DOMAIN: Final[str] = "peak_trade.ghv_referenced_intelligence_superstructure_offline.v1"
CYCLE_STATUS_COMPLETE: Final[str] = "INTELLIGENCE_OFFLINE_CYCLE_COMPLETE_M10_HARD_STOP"
CYCLE_STATUS_REJECTED: Final[str] = "INTELLIGENCE_OFFLINE_CYCLE_REJECTED"

GHV_AUTHORITY: Final[str] = "NONE"
GVEF_AUTHORITY: Final[str] = "NONE"
DDO_TRADING_AUTHORITY: Final[str] = "NONE"
PRODUCTIVE_CONFIG_MUTATION_PERFORMED: Final[bool] = False
POST_ALLOWED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
EIP_ACTIVATION_PERFORMED: Final[bool] = False
SUPERVISOR_ACTIVATION_PERFORMED: Final[bool] = False


class LineageSlotStatusV1(str, Enum):
    PRESENT = "PRESENT"
    NOT_REACHED = "NOT_REACHED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INTENTIONALLY_DISCONNECTED = "INTENTIONALLY_DISCONNECTED"
    HISTORICAL_REF_NOT_PRESENT = "HISTORICAL_REF_NOT_PRESENT"


class GhvReferencedIntelligenceOfflineCycleError(ValueError):
    """Fail-closed offline intelligence cycle error."""


@dataclass(frozen=True)
class GhvReferencedIntelligenceOfflineCycleRequestV1:
    learning_evidence: Mapping[str, Any]
    plane_request: OptimizationUniverseExperimentPlaneRequestV1
    optimization_surface_id: str
    parameter_config_delta: Mapping[str, Any] | None = None
    replay_seed: int = 0
    cycle_index: int = 0
    productive_cycle_id: str | None = None
    selected_instrument: str | None = None
    pending_outcome_ref: str | None = None
    ghv_reference_digest: str | None = None


def run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
    request: GhvReferencedIntelligenceOfflineCycleRequestV1,
) -> MappingProxyType[str, Any]:
    learning_validation = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(
            learning_evidence=request.learning_evidence
        )
    )
    if learning_validation.get("status") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        return _cycle_result(
            status=CYCLE_STATUS_REJECTED,
            reason="LEARNING_INPUT_NOT_ACCEPTED",
            lineage=_lineage_shell(
                request,
                optimization_input_status=LineageSlotStatusV1.INSUFFICIENT_EVIDENCE,
            ),
            m4_m8=None,
            ingress=None,
            m10=None,
            gvef=None,
        )

    try:
        m4_m8 = run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=request.learning_evidence,
                plane_request=request.plane_request,
                replay_seed=request.replay_seed,
                cycle_index=request.cycle_index,
            )
        )
    except M4M8EvidenceReturnLoopError as exc:
        raise GhvReferencedIntelligenceOfflineCycleError(str(exc)) from exc

    if m4_m8.get("status") != LOOP_STATUS_COMPLETE:
        return _cycle_result(
            status=CYCLE_STATUS_REJECTED,
            reason=str(m4_m8.get("reason") or "M4_M8_LOOP_INCOMPLETE"),
            lineage=_lineage_from_m4_partial(request, m4_m8),
            m4_m8=m4_m8,
            ingress=None,
            m10=None,
            gvef=None,
        )

    cycle = m4_m8.get("cycle") or {}
    plane = cycle.get("experiment_plane_result") or {}
    opt_evidence = cycle.get("optimization_experiment_evidence")
    if opt_evidence is None:
        opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)

    ingress = build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=opt_evidence,
        optimization_surface_id=request.optimization_surface_id,
        parameter_config_delta=request.parameter_config_delta,
    )
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    proposal = build_m10_promotion_proposal_from_ingress_v1(ingress)
    m10 = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=proposal,
            governance_admission=admission,
            owner_authorization_input=None,
        ),
        ingress=ingress,
    )
    gvef = build_gvef_intelligence_superstructure_reproof_v1(
        learning_evidence=request.learning_evidence,
        m4_m8_loop=m4_m8,
        ingress=ingress,
        m10_result=m10,
    )
    lineage = _lineage_from_complete_cycle(
        request=request,
        m4_m8=m4_m8,
        ingress=ingress,
        proposal=proposal,
        m10=m10,
        gvef=gvef,
    )
    return _cycle_result(
        status=CYCLE_STATUS_COMPLETE,
        reason="M10_HARD_STOP_EXPLICIT_AUTHORIZATION_REQUIRED",
        lineage=lineage,
        m4_m8=m4_m8,
        ingress=ingress,
        m10=m10,
        gvef=gvef,
    )


def build_gvef_intelligence_superstructure_reproof_v1(
    *,
    learning_evidence: Mapping[str, Any],
    m4_m8_loop: Mapping[str, Any],
    ingress: Mapping[str, Any],
    m10_result: Any,
) -> MappingProxyType[str, Any]:
    """Lightweight GVEF reproof bundle (AUTHORITY=NONE; architectural invariants only)."""
    meta = (m4_m8_loop.get("cycle") or {}).get("meta_learning_evidence") or {}
    checks: list[str] = []
    if m4_m8_loop.get("optimization_productive_authority") != "NONE":
        checks.append("OPTIMIZATION_PRODUCTIVE_AUTHORITY_NOT_NONE")
    if m4_m8_loop.get("p5_producer_bridge_performed") is True:
        checks.append("P5_BRIDGE_PERFORMED")
    if m4_m8_loop.get("search_executed") is True:
        checks.append("SEARCH_EXECUTED")
    if meta.get("meta_evidence_authority") not in (None, "NONE"):
        checks.append("META_EVIDENCE_AUTHORITY_NOT_NONE")
    if ingress.get("disposition") != "PROPOSAL_ONLY":
        checks.append("INGRESS_DISPOSITION_NOT_PROPOSAL_ONLY")
    if getattr(m10_result, "promotion_state", None) == M10PromotionState.AUTHORIZED:
        checks.append("M10_AUTHORIZED_WITHOUT_EXPLICIT_OWNER_INPUT")
    if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is True:
        checks.append("M10_RUNTIME_APPLY_IMPLIES_VIOLATION")
    body: dict[str, Any] = {
        "schema_version": "gvef_intelligence_superstructure_reproof_v1",
        "gvef_authority": GVEF_AUTHORITY,
        "ghv_authority": GHV_AUTHORITY,
        "learning_evidence_digest": learning_evidence.get("content_hash")
        or learning_evidence.get("learning_evidence_digest"),
        "m4_m8_loop_identity": m4_m8_loop.get("loop_identity"),
        "ingress_digest": ingress.get("ingress_digest"),
        "m10_promotion_state": getattr(
            getattr(m10_result, "promotion_state", None), "value", m10_result.promotion_state
        ),
        "invariant_violations": tuple(checks),
        "reproof_pass": not checks,
    }
    body["reproof_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def _slot(value: str | None, *, status: LineageSlotStatusV1) -> dict[str, Any]:
    return {"status": status.value, "ref": value or ""}


def _lineage_shell(
    request: GhvReferencedIntelligenceOfflineCycleRequestV1,
    *,
    optimization_input_status: LineageSlotStatusV1,
) -> dict[str, Any]:
    return {
        "productive_cycle_id": request.productive_cycle_id or "",
        "selected_instrument": request.selected_instrument or "",
        "decision_event_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "dpo_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "pending_outcome_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "outcome_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "learning_state_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "learning_evidence_ref": _slot(
            str(request.learning_evidence.get("record_id") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if request.learning_evidence.get("record_id")
                else LineageSlotStatusV1.INSUFFICIENT_EVIDENCE
            ),
        ),
        "optimization_input_ref": _slot(None, status=optimization_input_status),
        "experiment_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "robustness_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "champion_challenger_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "meta_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "mi_ref": _slot(None, status=LineageSlotStatusV1.INTENTIONALLY_DISCONNECTED),
        "gvef_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "proposal_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "m10_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "ghv_reference_ref": _slot(None, status=LineageSlotStatusV1.NOT_REACHED),
        "structural_outcome_completeness": "UNAVAILABLE",
        "realized_economic_completeness": "UNAVAILABLE",
    }


def _lineage_from_m4_partial(
    request: GhvReferencedIntelligenceOfflineCycleRequestV1,
    m4_m8: Mapping[str, Any],
) -> dict[str, Any]:
    lineage = _lineage_shell(request, optimization_input_status=LineageSlotStatusV1.NOT_REACHED)
    cycle = m4_m8.get("cycle") or {}
    plane = cycle.get("experiment_plane_result") or {}
    lineage["optimization_input_ref"] = _slot(
        str((plane.get("chain") or {}).get("learning_input_validation", {}).get("status") or ""),
        status=LineageSlotStatusV1.INSUFFICIENT_EVIDENCE,
    )
    return lineage


def _lineage_from_complete_cycle(
    *,
    request: GhvReferencedIntelligenceOfflineCycleRequestV1,
    m4_m8: Mapping[str, Any],
    ingress: Mapping[str, Any],
    proposal: Mapping[str, Any],
    m10: Any,
    gvef: Mapping[str, Any],
) -> dict[str, Any]:
    cycle = m4_m8.get("cycle") or {}
    plane = cycle.get("experiment_plane_result") or {}
    chain = plane.get("chain") or {}
    opt_evidence = cycle.get("optimization_experiment_evidence") or {}
    meta = cycle.get("meta_learning_evidence") or {}
    learning_input = chain.get("learning_input_validation") or {}
    le = request.learning_evidence
    structural = derive_structural_outcome_completeness_v1(le)
    realized = derive_realized_economic_completeness_v1(le)
    ghv_digest = str(request.ghv_reference_digest or "")
    return {
        "productive_cycle_id": request.productive_cycle_id or "",
        "selected_instrument": request.selected_instrument or "",
        "ghv_reference_ref": _slot(
            ghv_digest,
            status=(
                LineageSlotStatusV1.PRESENT if ghv_digest else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "decision_event_ref": _slot(
            str(le.get("decision_event_ref") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if le.get("decision_event_ref")
                else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "dpo_ref": _slot(None, status=LineageSlotStatusV1.NOT_APPLICABLE),
        "pending_outcome_ref": _slot(
            str(request.pending_outcome_ref or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if request.pending_outcome_ref
                else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "outcome_ref": _slot(
            str(le.get("outcome_record_id") or le.get("source_outcome_ref") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if le.get("outcome_record_id") or le.get("source_outcome_ref")
                else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "learning_state_ref": _slot(
            str(le.get("learning_state_record_id") or ""),
            status=(
                LineageSlotStatusV1.PRESENT
                if le.get("learning_state_record_id")
                else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "learning_evidence_ref": _slot(
            str(le.get("record_id") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "optimization_input_ref": _slot(
            str(learning_input.get("learning_evidence_digest") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "experiment_ref": _slot(
            str(opt_evidence.get("content_hash") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "robustness_ref": _slot(
            str(
                (opt_evidence.get("evidence_slices") or {})
                .get("ROBUSTNESS_EVIDENCE", {})
                .get("slice_digest", "")
            ),
            status=(
                LineageSlotStatusV1.PRESENT
                if (opt_evidence.get("evidence_slices") or {}).get("ROBUSTNESS_EVIDENCE")
                else LineageSlotStatusV1.NOT_APPLICABLE
            ),
        ),
        "champion_challenger_ref": _slot(
            str(chain.get("selected_candidate", {}).get("candidate_ref") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "meta_ref": _slot(
            str(meta.get("meta_evidence_id") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "mi_ref": _slot(None, status=LineageSlotStatusV1.INTENTIONALLY_DISCONNECTED),
        "gvef_ref": _slot(
            str(gvef.get("reproof_digest") or ""), status=LineageSlotStatusV1.PRESENT
        ),
        "proposal_ref": _slot(
            str(proposal.get("proposal_digest") or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "m10_ref": _slot(
            str(getattr(m10, "replay_bundle_digest", None) or ""),
            status=LineageSlotStatusV1.PRESENT,
        ),
        "structural_outcome_completeness": structural,
        "realized_economic_completeness": realized,
        "m10_hard_stop": True,
        "m10_promotion_state": getattr(
            getattr(m10, "promotion_state", None), "value", m10.promotion_state
        ),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

        return _json_safe(asdict(value))
    from enum import Enum

    if isinstance(value, Enum):
        return str(value.value)
    return value


def _cycle_result(
    *,
    status: str,
    reason: str,
    lineage: Mapping[str, Any],
    m4_m8: Mapping[str, Any] | None,
    ingress: Mapping[str, Any] | None,
    m10: Any,
    gvef: Mapping[str, Any] | None,
) -> MappingProxyType[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": CYCLE_DOMAIN,
        "status": status,
        "reason": reason,
        "ghv_authority": GHV_AUTHORITY,
        "gvef_authority": GVEF_AUTHORITY,
        "ddo_trading_authority": DDO_TRADING_AUTHORITY,
        "productive_config_mutation_performed": PRODUCTIVE_CONFIG_MUTATION_PERFORMED,
        "post_allowed": POST_ALLOWED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "eip_activation_performed": EIP_ACTIVATION_PERFORMED,
        "supervisor_activation_performed": SUPERVISOR_ACTIVATION_PERFORMED,
        "m10_authorized_promotion_implies_runtime_apply": AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
        "intelligence_lineage": dict(lineage),
        "m4_m8_loop": _json_safe(m4_m8) if m4_m8 is not None else None,
        "optimization_governance_ingress_digest": (
            str(ingress.get("ingress_digest") or "") if ingress is not None else None
        ),
        "m10_promotion_state": (
            getattr(getattr(m10, "promotion_state", None), "value", None)
            if m10 is not None
            else None
        ),
        "gvef_reproof": _json_safe(gvef) if gvef is not None else None,
    }
    payload["result_digest"] = compute_content_sha256(
        _json_safe({k: v for k, v in payload.items() if k != "result_digest"})
    )
    return MappingProxyType(payload)


__all__ = [
    "AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY",
    "CYCLE_STATUS_COMPLETE",
    "CYCLE_STATUS_REJECTED",
    "DDO_TRADING_AUTHORITY",
    "EIP_ACTIVATION_PERFORMED",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "GVEF_AUTHORITY",
    "GHV_AUTHORITY",
    "GhvReferencedIntelligenceOfflineCycleError",
    "GhvReferencedIntelligenceOfflineCycleRequestV1",
    "LineageSlotStatusV1",
    "POST_ALLOWED",
    "PRODUCTIVE_CONFIG_MUTATION_PERFORMED",
    "SCHEMA_VERSION",
    "SUPERVISOR_ACTIVATION_PERFORMED",
    "build_gvef_intelligence_superstructure_reproof_v1",
    "run_ghv_referenced_intelligence_superstructure_offline_cycle_v1",
]
