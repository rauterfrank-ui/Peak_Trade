"""M10 promotion governance boundary v1 — proposal, validation, authorization, promotion record.

Fail-closed canonical boundary for Unified Blueprint Phase 13. Composes existing ingress,
Phase-12 lineage, and explicit Owner authorization. Stops at AUTHORIZED_PROMOTION_RECORD;
does not materialize productive configuration or runtime apply.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_M9_SURFACE_ID,
)
from src.governance.explicit_productive_authorization_v1 import (
    DISPOSITION_AUTHORIZATION_ONLY,
    PRODUCTIVE_TARGET_ID,
    STATUS_AUTHORIZED_BOUNDARY,
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    OwnerExplicitProductiveAuthorizationInputV1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    DISPOSITION_PROPOSAL_ONLY,
    PROMOTION_AUTHORITY,
    OptimizationProposalGovernanceAdmissionRequestV1,
    OptimizationProposalGovernanceAdmissionResultV1,
    direct_productive_write_possible_v1,
    evaluate_optimization_proposal_governance_admission_v1,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "m10_promotion_boundary_v1"
PROMOTION_PROPOSAL_SCHEMA_VERSION: Final[str] = "m10_promotion_proposal_v1"
AUTHORIZED_PROMOTION_RECORD_SCHEMA_VERSION: Final[str] = "m10_authorized_promotion_record_v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_13_M10_PROMOTION_BOUNDARY_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = "config/governance/m10_promotion_boundary_v1_decision_v1.json"
TOPOLOGY_ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/m10_promotion_topology_adjudication_v1.json"
)
CONSUMER_BINDING_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_productive_consumer_binding_registry_v1.json"
)

OPTIMIZATION_PROMOTION_AUTHORITY: Final[str] = PROMOTION_AUTHORITY
OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE: Final[bool] = direct_productive_write_possible_v1()
NO_SELF_DEPLOY: Final[bool] = True
RISK_IS_HARD_BOUNDARY: Final[bool] = True
AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY: Final[bool] = False
AUTHORIZED_PROMOTION_IMPLIES_EXTERNAL_EFFECT: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]

_PROMOTION_PROPOSAL_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "promotion_proposal_id",
    "state",
    "surface_id",
    "candidate_ref",
    "candidate_parameter_value_digest",
    "candidate_value",
    "candidate_unit",
    "productive_target_id",
    "productive_target_version",
    "current_consumer_module",
    "current_consumer_symbol",
    "consumer_binding_version",
    "evidence_content_hash",
    "evidence_reproducibility_digest",
    "learning_evidence_digest",
    "evidence_record_id",
    "lineage_digest",
    "ingress_digest",
    "experiment_id",
    "disposition",
    "risk_constraints_ref",
    "governance_risk_constraints_ref",
    "robustness_suite_identity",
    "evidence_slices_digest",
    "proposal_created_at",
    "proposal_digest",
)

_AUTHORIZED_RECORD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "authorized_promotion_record_id",
    "promotion_state",
    "promotion_proposal_id",
    "proposal_digest",
    "surface_id",
    "productive_target_id",
    "current_consumer_module",
    "candidate_ref",
    "candidate_parameter_value_digest",
    "lineage_digest",
    "ingress_digest",
    "explicit_authorization_digest",
    "owner_authorization_record_digest",
    "authorization_disposition",
    "runtime_apply_authorized",
    "productive_configuration_write_authorized",
    "external_effect_authorized",
    "optimization_promotion_authority",
    "trading_decision_authority_owner",
    "authorized_promotion_record_digest",
)


class M10PromotionState(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    INVALID = "INVALID"


class M10PromotionBoundaryError(ValueError):
    """Fail-closed M10 promotion boundary error."""


@dataclass(frozen=True)
class M10PromotionGovernanceValidationResultV1:
    validation_state: M10PromotionState
    reason_codes: tuple[str, ...]
    promotion_proposal_id: str | None
    proposal_digest: str | None


@dataclass(frozen=True)
class M10PromotionBoundaryEvaluateRequestV1:
    promotion_proposal: Mapping[str, Any]
    governance_admission: OptimizationProposalGovernanceAdmissionResultV1 | None = None
    owner_authorization_input: OwnerExplicitProductiveAuthorizationInputV1 | None = None
    requested_promotion_without_authorization: bool = False
    requested_runtime_apply: bool = False
    requested_productive_configuration_write: bool = False


@dataclass(frozen=True)
class M10PromotionBoundaryResultV1:
    promotion_state: M10PromotionState
    reason_codes: tuple[str, ...]
    promotion_proposal_id: str | None
    proposal_digest: str | None
    authorized_promotion_record: MappingProxyType[str, Any] | None
    explicit_authorization_digest: str | None
    replay_bundle_digest: str | None


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise M10PromotionBoundaryError(f"config_not_mapping:{relative_path}")
    return payload


def _consumer_binding_for_surface(surface_id: str) -> Mapping[str, Any] | None:
    reg = _load_json(CONSUMER_BINDING_REGISTRY)
    for row in reg.get("bindings") or ():
        if isinstance(row, dict) and row.get("surface_id") == surface_id:
            return row
    for row in reg.get("non_productive_surfaces") or ():
        if isinstance(row, dict) and row.get("surface_id") == surface_id:
            return row
    return None


def compute_promotion_proposal_digest_v1(proposal_body: Mapping[str, Any]) -> str:
    body = {
        key: proposal_body[key]
        for key in _PROMOTION_PROPOSAL_KEYS
        if key in proposal_body and key != "proposal_digest"
    }
    return compute_content_sha256(body)


def build_m10_promotion_proposal_from_ingress_v1(
    ingress: Mapping[str, Any],
    *,
    proposal_created_at: datetime | None = None,
) -> MappingProxyType[str, Any]:
    """Typed promotion proposal from optimization ingress — PROPOSAL_ONLY, no authority."""
    validated = validate_optimization_proposal_governance_ingress_v1(ingress)
    surface_id = str(validated["optimization_surface_id"])
    binding = _consumer_binding_for_surface(surface_id)
    if binding is None:
        raise M10PromotionBoundaryError(f"CONSUMER_BINDING_MISSING:{surface_id}")

    from src.experiments.canonical_optimization_productive_lineage_registry_v1 import (
        resolve_productive_lineage_v1,
    )

    lineage = resolve_productive_lineage_v1(surface_id=surface_id)
    lineage_digest = str(lineage.get("lineage_record_digest") or lineage.get("result_digest") or "")

    delta = dict(validated["parameter_config_delta"])
    candidate_value_digest = compute_content_sha256(
        {
            "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
            "parameter_config_delta": delta,
        }
    )
    provenance = dict(validated.get("optimization_provenance") or {})
    ingress_digest = str(validated["ingress_digest"])
    promotion_proposal_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"m10-proposal:{ingress_digest}"))

    created = proposal_created_at or datetime(1970, 1, 1, tzinfo=timezone.utc)

    body: dict[str, Any] = {
        "schema_version": PROMOTION_PROPOSAL_SCHEMA_VERSION,
        "promotion_proposal_id": promotion_proposal_id,
        "state": M10PromotionState.PROPOSED.value,
        "surface_id": surface_id,
        "candidate_ref": str(validated["candidate_ref"]),
        "candidate_parameter_value_digest": candidate_value_digest,
        "candidate_value": delta,
        "candidate_unit": TARGET_UNIT if surface_id == F1_M9_SURFACE_ID else "UNKNOWN",
        "productive_target_id": binding.get("productive_target_id"),
        "productive_target_version": binding.get("productive_target_version"),
        "current_consumer_module": binding.get("current_consumer_module"),
        "current_consumer_symbol": binding.get("current_consumer_symbol"),
        "consumer_binding_version": CONSUMER_BINDING_REGISTRY,
        "evidence_content_hash": str(validated["optimization_evidence_content_hash"]),
        "evidence_reproducibility_digest": str(
            validated["optimization_evidence_reproducibility_digest"]
        ),
        "learning_evidence_digest": str(validated["learning_evidence_digest"]),
        "evidence_record_id": validated.get("optimization_evidence_record_id"),
        "lineage_digest": lineage_digest,
        "ingress_digest": ingress_digest,
        "experiment_id": str(validated["experiment_id"]),
        "disposition": DISPOSITION_PROPOSAL_ONLY,
        "risk_constraints_ref": str(validated["risk_constraints_ref"]),
        "governance_risk_constraints_ref": str(validated["governance_risk_constraints_ref"]),
        "robustness_suite_identity": provenance.get("robustness_suite_identity"),
        "evidence_slices_digest": provenance.get("evidence_slices_digest"),
        "proposal_created_at": created.isoformat(),
    }
    body["proposal_digest"] = compute_promotion_proposal_digest_v1(body)
    return MappingProxyType(body)


def validate_m10_promotion_proposal_contract_v1(
    proposal: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if proposal.get("schema_version") != PROMOTION_PROPOSAL_SCHEMA_VERSION:
        errors.append("PROPOSAL_SCHEMA_VERSION_MISMATCH")
    if proposal.get("disposition") != DISPOSITION_PROPOSAL_ONLY:
        errors.append("DISPOSITION_NOT_PROPOSAL_ONLY")
    if proposal.get("state") != M10PromotionState.PROPOSED.value:
        errors.append("PROPOSAL_STATE_NOT_PROPOSED")
    missing = [key for key in _PROMOTION_PROPOSAL_KEYS if key not in proposal]
    if missing:
        errors.append(f"PROPOSAL_REQUIRED_FIELDS_MISSING:{','.join(missing)}")
    stored_digest = proposal.get("proposal_digest")
    if not isinstance(stored_digest, str) or not is_valid_sha256_hex(stored_digest):
        errors.append("PROPOSAL_DIGEST_MALFORMED")
    elif compute_promotion_proposal_digest_v1(proposal) != stored_digest:
        errors.append("PROPOSAL_DIGEST_MISMATCH")
    ingress_digest = str(proposal.get("ingress_digest") or "")
    if not is_valid_sha256_hex(ingress_digest):
        errors.append("INGRESS_DIGEST_MALFORMED")
    proposal_id = str(proposal.get("promotion_proposal_id") or "")
    expected_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"m10-proposal:{ingress_digest}"))
    if proposal_id != expected_id:
        errors.append("PROMOTION_PROPOSAL_ID_NOT_DETERMINISTIC")
    return not errors, tuple(errors)


def validate_m10_promotion_governance_v1(
    *,
    promotion_proposal: Mapping[str, Any],
    ingress: Mapping[str, Any],
    governance_admission: OptimizationProposalGovernanceAdmissionResultV1,
) -> M10PromotionGovernanceValidationResultV1:
    """Fail-closed M10 governance validation — no promotion authority minted."""
    reason_codes: list[str] = []
    contract_ok, contract_errors = validate_m10_promotion_proposal_contract_v1(promotion_proposal)
    reason_codes.extend(contract_errors)
    if not contract_ok:
        return M10PromotionGovernanceValidationResultV1(
            validation_state=M10PromotionState.INVALID,
            reason_codes=tuple(reason_codes),
            promotion_proposal_id=str(promotion_proposal.get("promotion_proposal_id") or "")
            or None,
            proposal_digest=str(promotion_proposal.get("proposal_digest") or "") or None,
        )

    proposal_id = str(promotion_proposal["promotion_proposal_id"])
    proposal_digest = str(promotion_proposal["proposal_digest"])
    surface_id = str(promotion_proposal["surface_id"])

    try:
        validated_ingress = validate_optimization_proposal_governance_ingress_v1(ingress)
    except Exception as exc:
        reason_codes.append(str(exc))
        return M10PromotionGovernanceValidationResultV1(
            validation_state=M10PromotionState.REJECTED,
            reason_codes=tuple(reason_codes),
            promotion_proposal_id=proposal_id,
            proposal_digest=proposal_digest,
        )

    if str(validated_ingress["ingress_digest"]) != str(promotion_proposal["ingress_digest"]):
        reason_codes.append("PROPOSAL_INGRESS_DIGEST_MISMATCH")

    if governance_admission.admission_status != ADMISSION_ADMITTED:
        reason_codes.append("GOVERNANCE_REVIEW_ADMISSION_NOT_ADMITTED")
    if governance_admission.ingress_digest != str(promotion_proposal["ingress_digest"]):
        reason_codes.append("ADMISSION_INGRESS_DIGEST_MISMATCH")

    from src.experiments.canonical_optimization_productive_lineage_registry_v1 import (
        ProductiveRelevanceDisposition,
        resolve_productive_lineage_v1,
    )

    lineage = resolve_productive_lineage_v1(surface_id=surface_id)
    disposition = str(lineage.get("disposition") or "")
    if disposition != ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANT.value:
        if surface_id in (F2_SURFACE_ID, F5_FRESH_SURFACE_ID):
            reason_codes.append("RESEARCH_ONLY_SURFACE_PROMOTION_FORBIDDEN")
        elif disposition == ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANCE_UNKNOWN.value:
            reason_codes.append("PRODUCTIVE_RELEVANCE_UNKNOWN")
        else:
            reason_codes.append("SURFACE_NOT_PRODUCTIVE_RELEVANT")

    if lineage.get("lineage_chain_proven") is not True:
        reason_codes.append("PHASE_12_LINEAGE_CHAIN_NOT_PROVEN")

    if str(promotion_proposal["lineage_digest"]) != str(
        lineage.get("lineage_record_digest") or lineage.get("result_digest") or ""
    ):
        reason_codes.append("LINEAGE_DIGEST_MISMATCH")

    binding = _consumer_binding_for_surface(surface_id)
    if binding is None:
        reason_codes.append("CONSUMER_BINDING_MISSING")
    elif binding.get("current_consumer_module") != promotion_proposal.get(
        "current_consumer_module"
    ):
        reason_codes.append("CONSUMER_MODULE_MISMATCH")
    elif binding.get("productive_target_id") != promotion_proposal.get("productive_target_id"):
        reason_codes.append("PRODUCTIVE_TARGET_MISMATCH")

    if surface_id == F1_M9_SURFACE_ID:
        if promotion_proposal.get("productive_target_id") != PRODUCTIVE_TARGET_ID:
            reason_codes.append("F1_M9_PRODUCTIVE_TARGET_ID_MISMATCH")
        delta = dict(validated_ingress["parameter_config_delta"])
        if set(delta.keys()) != {SOURCE_CANDIDATE_PARAMETER}:
            reason_codes.append("CANDIDATE_PARAMETER_OUT_OF_DOMAIN")
        expected_candidate_digest = compute_content_sha256(
            {
                "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
                "parameter_config_delta": delta,
            }
        )
        if promotion_proposal.get("candidate_parameter_value_digest") != expected_candidate_digest:
            reason_codes.append("CANDIDATE_DIGEST_MISMATCH")
        if promotion_proposal.get("candidate_unit") != TARGET_UNIT:
            reason_codes.append("CANDIDATE_UNIT_MISMATCH")

    evidence_bindings: tuple[tuple[str, str, str], ...] = (
        (
            "evidence_content_hash",
            str(promotion_proposal["evidence_content_hash"]),
            str(validated_ingress["optimization_evidence_content_hash"]),
        ),
        (
            "evidence_reproducibility_digest",
            str(promotion_proposal["evidence_reproducibility_digest"]),
            str(validated_ingress["optimization_evidence_reproducibility_digest"]),
        ),
        (
            "learning_evidence_digest",
            str(promotion_proposal["learning_evidence_digest"]),
            str(validated_ingress["learning_evidence_digest"]),
        ),
        (
            "experiment_id",
            str(promotion_proposal["experiment_id"]),
            str(validated_ingress["experiment_id"]),
        ),
        (
            "candidate_ref",
            str(promotion_proposal["candidate_ref"]),
            str(validated_ingress["candidate_ref"]),
        ),
    )
    for field, proposal_val, ingress_val in evidence_bindings:
        if proposal_val != ingress_val:
            reason_codes.append(f"EVIDENCE_BINDING_MISMATCH:{field}")

    if reason_codes:
        return M10PromotionGovernanceValidationResultV1(
            validation_state=M10PromotionState.REJECTED,
            reason_codes=tuple(reason_codes),
            promotion_proposal_id=proposal_id,
            proposal_digest=proposal_digest,
        )

    return M10PromotionGovernanceValidationResultV1(
        validation_state=M10PromotionState.VALIDATED,
        reason_codes=("M10_GOVERNANCE_VALIDATION_PASS",),
        promotion_proposal_id=proposal_id,
        proposal_digest=proposal_digest,
    )


def _build_authorized_promotion_record_v1(
    *,
    promotion_proposal: Mapping[str, Any],
    explicit_authorization_digest: str,
    owner_authorization_record_digest: str,
) -> MappingProxyType[str, Any]:
    proposal_id = str(promotion_proposal["promotion_proposal_id"])
    proposal_digest = str(promotion_proposal["proposal_digest"])
    record_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"m10-authorized:{proposal_digest}"))

    body: dict[str, Any] = {
        "schema_version": AUTHORIZED_PROMOTION_RECORD_SCHEMA_VERSION,
        "authorized_promotion_record_id": record_id,
        "promotion_state": M10PromotionState.AUTHORIZED.value,
        "promotion_proposal_id": proposal_id,
        "proposal_digest": proposal_digest,
        "surface_id": promotion_proposal["surface_id"],
        "productive_target_id": promotion_proposal["productive_target_id"],
        "current_consumer_module": promotion_proposal["current_consumer_module"],
        "candidate_ref": promotion_proposal["candidate_ref"],
        "candidate_parameter_value_digest": promotion_proposal["candidate_parameter_value_digest"],
        "lineage_digest": promotion_proposal["lineage_digest"],
        "ingress_digest": promotion_proposal["ingress_digest"],
        "explicit_authorization_digest": explicit_authorization_digest,
        "owner_authorization_record_digest": owner_authorization_record_digest,
        "authorization_disposition": DISPOSITION_AUTHORIZATION_ONLY,
        "runtime_apply_authorized": False,
        "productive_configuration_write_authorized": False,
        "external_effect_authorized": False,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "trading_decision_authority_owner": TRADING_DECISION_AUTHORITY_OWNER,
        "target_policy_parameter": TARGET_POLICY_PARAMETER,
        "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
    }
    digest_keys = tuple(
        key for key in _AUTHORIZED_RECORD_KEYS if key != "authorized_promotion_record_digest"
    )
    body["authorized_promotion_record_digest"] = compute_content_sha256(
        {key: body[key] for key in digest_keys}
    )
    return MappingProxyType(body)


def compute_m10_replay_bundle_digest_v1(
    *,
    promotion_proposal_id: str | None,
    proposal_digest: str | None,
    validation_state: M10PromotionState,
    validation_reason_codes: tuple[str, ...],
    promotion_state: M10PromotionState,
    authorized_promotion_record_digest: str | None,
    explicit_authorization_digest: str | None,
) -> str:
    body = {
        "promotion_proposal_id": promotion_proposal_id,
        "proposal_digest": proposal_digest,
        "validation_state": validation_state.value,
        "validation_reason_codes": validation_reason_codes,
        "promotion_state": promotion_state.value,
        "authorized_promotion_record_digest": authorized_promotion_record_digest,
        "explicit_authorization_digest": explicit_authorization_digest,
    }
    return compute_content_sha256(body)


def evaluate_m10_promotion_boundary_v1(
    request: M10PromotionBoundaryEvaluateRequestV1,
    *,
    ingress: Mapping[str, Any],
) -> M10PromotionBoundaryResultV1:
    """Full M10 boundary evaluation: validation → optional explicit auth → promotion record."""
    forbidden: list[str] = []
    if request.requested_promotion_without_authorization:
        forbidden.append("REQUESTED_PROMOTION_WITHOUT_AUTHORIZATION_FORBIDDEN")
    if request.requested_runtime_apply:
        forbidden.append("REQUESTED_RUNTIME_APPLY_FORBIDDEN")
    if request.requested_productive_configuration_write:
        forbidden.append("REQUESTED_PRODUCTIVE_CONFIGURATION_WRITE_FORBIDDEN")
    if forbidden:
        proposal_id = str(request.promotion_proposal.get("promotion_proposal_id") or "") or None
        proposal_digest = str(request.promotion_proposal.get("proposal_digest") or "") or None
        return M10PromotionBoundaryResultV1(
            promotion_state=M10PromotionState.REJECTED,
            reason_codes=tuple(forbidden),
            promotion_proposal_id=proposal_id,
            proposal_digest=proposal_digest,
            authorized_promotion_record=None,
            explicit_authorization_digest=None,
            replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
                promotion_proposal_id=proposal_id,
                proposal_digest=proposal_digest,
                validation_state=M10PromotionState.REJECTED,
                validation_reason_codes=tuple(forbidden),
                promotion_state=M10PromotionState.REJECTED,
                authorized_promotion_record_digest=None,
                explicit_authorization_digest=None,
            ),
        )

    admission = request.governance_admission
    if admission is None:
        admission = evaluate_optimization_proposal_governance_admission_v1(
            OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
        )

    validation = validate_m10_promotion_governance_v1(
        promotion_proposal=request.promotion_proposal,
        ingress=ingress,
        governance_admission=admission,
    )
    if validation.validation_state != M10PromotionState.VALIDATED:
        return M10PromotionBoundaryResultV1(
            promotion_state=validation.validation_state,
            reason_codes=validation.reason_codes,
            promotion_proposal_id=validation.promotion_proposal_id,
            proposal_digest=validation.proposal_digest,
            authorized_promotion_record=None,
            explicit_authorization_digest=None,
            replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
                promotion_proposal_id=validation.promotion_proposal_id,
                proposal_digest=validation.proposal_digest,
                validation_state=validation.validation_state,
                validation_reason_codes=validation.reason_codes,
                promotion_state=validation.validation_state,
                authorized_promotion_record_digest=None,
                explicit_authorization_digest=None,
            ),
        )

    if request.owner_authorization_input is None:
        return M10PromotionBoundaryResultV1(
            promotion_state=M10PromotionState.VALIDATED,
            reason_codes=("EXPLICIT_AUTHORIZATION_REQUIRED_FOR_PROMOTION",),
            promotion_proposal_id=validation.promotion_proposal_id,
            proposal_digest=validation.proposal_digest,
            authorized_promotion_record=None,
            explicit_authorization_digest=None,
            replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
                promotion_proposal_id=validation.promotion_proposal_id,
                proposal_digest=validation.proposal_digest,
                validation_state=M10PromotionState.VALIDATED,
                validation_reason_codes=validation.reason_codes,
                promotion_state=M10PromotionState.VALIDATED,
                authorized_promotion_record_digest=None,
                explicit_authorization_digest=None,
            ),
        )

    auth_result = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=str(request.promotion_proposal.get("productive_target_id") or ""),
            owner_authorization_input=request.owner_authorization_input,
        )
    )
    if auth_result.authorization_status != STATUS_AUTHORIZED_BOUNDARY:
        merged = validation.reason_codes + auth_result.reason_codes
        return M10PromotionBoundaryResultV1(
            promotion_state=M10PromotionState.REJECTED,
            reason_codes=merged,
            promotion_proposal_id=validation.promotion_proposal_id,
            proposal_digest=validation.proposal_digest,
            authorized_promotion_record=None,
            explicit_authorization_digest=auth_result.authorization_digest,
            replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
                promotion_proposal_id=validation.promotion_proposal_id,
                proposal_digest=validation.proposal_digest,
                validation_state=M10PromotionState.VALIDATED,
                validation_reason_codes=validation.reason_codes,
                promotion_state=M10PromotionState.REJECTED,
                authorized_promotion_record_digest=None,
                explicit_authorization_digest=auth_result.authorization_digest,
            ),
        )

    assert auth_result.authorization_record is not None
    assert auth_result.authorization_digest is not None
    if str(auth_result.authorization_record.get("ingress_digest")) != str(
        request.promotion_proposal.get("ingress_digest")
    ):
        return M10PromotionBoundaryResultV1(
            promotion_state=M10PromotionState.REJECTED,
            reason_codes=("AUTHORIZATION_INGRESS_BINDING_MISMATCH",),
            promotion_proposal_id=validation.promotion_proposal_id,
            proposal_digest=validation.proposal_digest,
            authorized_promotion_record=None,
            explicit_authorization_digest=auth_result.authorization_digest,
            replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
                promotion_proposal_id=validation.promotion_proposal_id,
                proposal_digest=validation.proposal_digest,
                validation_state=M10PromotionState.VALIDATED,
                validation_reason_codes=validation.reason_codes,
                promotion_state=M10PromotionState.REJECTED,
                authorized_promotion_record_digest=None,
                explicit_authorization_digest=auth_result.authorization_digest,
            ),
        )

    record = _build_authorized_promotion_record_v1(
        promotion_proposal=request.promotion_proposal,
        explicit_authorization_digest=auth_result.authorization_digest,
        owner_authorization_record_digest=(
            request.owner_authorization_input.owner_authorization_record_digest
        ),
    )
    return M10PromotionBoundaryResultV1(
        promotion_state=M10PromotionState.AUTHORIZED,
        reason_codes=("AUTHORIZED_PROMOTION_RECORD_MINTED",),
        promotion_proposal_id=validation.promotion_proposal_id,
        proposal_digest=validation.proposal_digest,
        authorized_promotion_record=record,
        explicit_authorization_digest=auth_result.authorization_digest,
        replay_bundle_digest=compute_m10_replay_bundle_digest_v1(
            promotion_proposal_id=validation.promotion_proposal_id,
            proposal_digest=validation.proposal_digest,
            validation_state=M10PromotionState.VALIDATED,
            validation_reason_codes=validation.reason_codes,
            promotion_state=M10PromotionState.AUTHORIZED,
            authorized_promotion_record_digest=str(record["authorized_promotion_record_digest"]),
            explicit_authorization_digest=auth_result.authorization_digest,
        ),
    )


def replay_m10_promotion_boundary_v1(
    *,
    promotion_proposal: Mapping[str, Any],
    ingress: Mapping[str, Any],
    governance_admission: OptimizationProposalGovernanceAdmissionResultV1,
    owner_authorization_input: OwnerExplicitProductiveAuthorizationInputV1 | None,
    prior_result: M10PromotionBoundaryResultV1,
) -> bool:
    """Deterministic replay — same inputs must yield identical dispositions and digests."""
    replay = evaluate_m10_promotion_boundary_v1(
        M10PromotionBoundaryEvaluateRequestV1(
            promotion_proposal=promotion_proposal,
            governance_admission=governance_admission,
            owner_authorization_input=owner_authorization_input,
        ),
        ingress=ingress,
    )
    return (
        replay.promotion_state == prior_result.promotion_state
        and replay.promotion_proposal_id == prior_result.promotion_proposal_id
        and replay.proposal_digest == prior_result.proposal_digest
        and replay.replay_bundle_digest == prior_result.replay_bundle_digest
        and (
            prior_result.authorized_promotion_record is None
            and replay.authorized_promotion_record is None
            or prior_result.authorized_promotion_record is not None
            and replay.authorized_promotion_record is not None
            and prior_result.authorized_promotion_record.get("authorized_promotion_record_digest")
            == replay.authorized_promotion_record.get("authorized_promotion_record_digest")
        )
    )


def build_m10_promotion_topology_adjudication_v1() -> MappingProxyType[str, Any]:
    """Read-only census of promotion-related paths — CURRENT vs superseded."""
    entries: tuple[dict[str, Any], ...] = (
        {
            "path_id": "optimization_proposal_governance_ingress_v1",
            "module": "src/governance/optimization_proposal_governance_ingress_v1.py",
            "classification": "CURRENT",
            "role": "M10_PROPOSAL_INGRESS",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "FORBIDDEN",
            "reachable": True,
        },
        {
            "path_id": "explicit_productive_authorization_v1",
            "module": "src/governance/explicit_productive_authorization_v1.py",
            "classification": "CURRENT",
            "role": "M10_EXPLICIT_EXTERNAL_AUTHORIZATION",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "NOT_IMPLIED",
            "reachable": True,
        },
        {
            "path_id": "m10_promotion_boundary_v1",
            "module": "src/governance/m10_promotion_boundary_v1.py",
            "classification": "CURRENT",
            "role": "M10_CANONICAL_PROMOTION_BOUNDARY",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "STOP_AT_AUTHORIZED_PROMOTION_RECORD",
            "reachable": True,
        },
        {
            "path_id": "governed_productive_configuration_v1",
            "module": "src/governance/governed_productive_configuration_v1.py",
            "classification": "CURRENT",
            "role": "SUCCESSOR_MATERIALIZATION_NOT_M10_DEFAULT",
            "can_mutate_productive_config": True,
            "can_self_authorize": False,
            "runtime_apply_relation": "SEPARATE_GOVERNED_EDGE",
            "reachable": False,
        },
        {
            "path_id": "promotion_loop_engine",
            "module": "src/governance/promotion_loop/engine.py",
            "classification": "HISTORICAL_DOMAIN_SCOPED",
            "role": "LEGACY_PROMOTION_LOOP",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "NOT_M10_CANONICAL",
            "reachable": False,
        },
        {
            "path_id": "promotion_economic_gate_v1",
            "module": "src/governance/promotion_loop/promotion_economic_gate_v1.py",
            "classification": "CURRENT",
            "role": "CANDIDATE_ELIGIBILITY_GATE_NOT_PROMOTION_AUTHORITY",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "NON_AUTHORIZING",
            "reachable": True,
        },
        {
            "path_id": "learning_promotion_records_v0",
            "module": "src/learning/deterministic_decision_outcome_v0/promotion_records_v0.py",
            "classification": "HISTORICAL",
            "role": "LEARNING_DOMAIN_PROMOTION_EVIDENCE",
            "can_mutate_productive_config": False,
            "can_self_authorize": False,
            "runtime_apply_relation": "NOT_M10_CANONICAL",
            "reachable": False,
        },
    )
    body = {
        "schema_version": "m10_promotion_topology_adjudication_v1",
        "canonical_m10_boundary_module": "src/governance/m10_promotion_boundary_v1.py",
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "entries": list(entries),
    }
    body["adjudication_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "adjudication_digest"}
    )
    return MappingProxyType(body)


def prove_m10_promotion_boundary_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if not (root / NORMATIVE_SPEC).is_file():
        return False
    if not (root / DECISION_CONFIG).is_file():
        return False
    if not (root / "src/governance/m10_promotion_boundary_v1.py").is_file():
        return False
    if OPTIMIZATION_PROMOTION_AUTHORITY != "NONE":
        return False
    if OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE is not False:
        return False
    if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is not False:
        return False
    decision = _load_json(DECISION_CONFIG)
    if decision.get("phase_13_m10_promotion_boundary_status") != "PROVEN_COMPLETE":
        return False
    return True
