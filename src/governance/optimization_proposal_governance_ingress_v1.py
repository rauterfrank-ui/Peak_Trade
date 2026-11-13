"""Optimization proposal → Governance/Risk ingress v1 (M10 edge, fail-closed).

Validates supplied governance ingress records for review admission.
Does not authorize productive apply, promotion decisions, or config mutation.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.governance.offline_observation_proposal_contract_fences_v1 import CONTRACT_LAYERS
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE as ECONOMIC_GATE_AUTHORITY_EFFECT_NONE,
    REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN,
    REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN,
)
from src.meta.learning_loop.config_patch_manifest_v1 import ConfigPatchManifestV1, ManifestIntegrity
from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    compute_content_sha256,
    is_valid_sha256_hex,
    validate_patch_target,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus

SCHEMA_VERSION: Final[str] = "optimization_proposal_governance_ingress_v1"
INGRESS_DOMAIN: Final[str] = "peak_trade.governance.optimization_proposal_ingress.v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/OPTIMIZATION_PROPOSAL_GOVERNANCE_INGRESS_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/optimization_proposal_governance_ingress_v1_decision_v1.json"
)

DISPOSITION_PROPOSAL_ONLY: Final[str] = "PROPOSAL_ONLY"
ADMISSION_ADMITTED: Final[str] = "ADMITTED_FOR_GOVERNANCE_REVIEW"
ADMISSION_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

PROMOTION_AUTHORITY: Final[str] = "NONE"
PRODUCTIVE_APPLY_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]

_REQUIRED_INGRESS_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "domain",
        "disposition",
        "plane_identity",
        "experiment_id",
        "candidate_ref",
        "optimization_surface_id",
        "parameter_config_delta",
        "optimization_evidence_record_id",
        "optimization_evidence_content_hash",
        "optimization_evidence_reproducibility_digest",
        "learning_evidence_digest",
        "plane_result_digest",
        "envelope_identity",
        "envelope_owner_authorization_ref",
        "risk_constraints_ref",
        "governance_risk_constraints_ref",
        "optimization_provenance",
        "ingress_digest",
    }
)


class OptimizationProposalGovernanceIngressError(ValueError):
    """Fail-closed ingress build/validation error."""


@dataclass(frozen=True)
class OptimizationProposalGovernanceAdmissionRequestV1:
    ingress: Mapping[str, Any]
    requested_promotion: bool = False
    requested_productive_apply: bool = False
    requested_runtime_authority: bool = False
    requested_deployment_activation: bool = False


@dataclass(frozen=True)
class OptimizationProposalGovernanceAdmissionResultV1:
    admission_status: str
    reason_codes: tuple[str, ...]
    ingress_digest: str | None
    config_patch_manifest_projection: ConfigPatchManifestV1 | None = None
    fence_layer: str = "PROPOSAL"
    promotion_authority: str = PROMOTION_AUTHORITY
    productive_apply_authority: str = PRODUCTIVE_APPLY_AUTHORITY
    economic_gate_authority_effect: str = ECONOMIC_GATE_AUTHORITY_EFFECT_NONE


def validate_optimization_proposal_governance_ingress_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise OptimizationProposalGovernanceIngressError("INGRESS_MUST_BE_MAPPING")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OptimizationProposalGovernanceIngressError("INGRESS_SCHEMA_VERSION_MISMATCH")
    if payload.get("domain") != INGRESS_DOMAIN:
        raise OptimizationProposalGovernanceIngressError("INGRESS_DOMAIN_MISMATCH")
    if payload.get("disposition") != DISPOSITION_PROPOSAL_ONLY:
        raise OptimizationProposalGovernanceIngressError("DISPOSITION_MUST_BE_PROPOSAL_ONLY")
    missing = _REQUIRED_INGRESS_KEYS - frozenset(payload.keys())
    if missing:
        raise OptimizationProposalGovernanceIngressError(
            f"INGRESS_REQUIRED_FIELDS_MISSING:{','.join(sorted(missing))}"
        )
    for digest_field in (
        "plane_identity",
        "optimization_evidence_content_hash",
        "optimization_evidence_reproducibility_digest",
        "learning_evidence_digest",
        "envelope_identity",
        "ingress_digest",
    ):
        if not is_valid_sha256_hex(str(payload.get(digest_field) or "")):
            raise OptimizationProposalGovernanceIngressError(f"{digest_field.upper()}_INVALID")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise OptimizationProposalGovernanceIngressError("PROMOTION_AUTHORITY_MUST_BE_NONE")
    if payload.get("productive_apply_authority") != PRODUCTIVE_APPLY_AUTHORITY:
        raise OptimizationProposalGovernanceIngressError("PRODUCTIVE_APPLY_AUTHORITY_MUST_BE_NONE")
    if payload.get("external_effect_authorized") is not False:
        raise OptimizationProposalGovernanceIngressError("EXTERNAL_EFFECT_MUST_BE_FALSE")
    provenance = payload.get("optimization_provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        raise OptimizationProposalGovernanceIngressError("OPTIMIZATION_PROVENANCE_REQUIRED")
    if "source_plane_schema_version" in provenance:
        raise OptimizationProposalGovernanceIngressError("DIRECT_M4_M5_GOVERNANCE_HANDOFF_RETIRED")
    return MappingProxyType(dict(payload))


def project_optimization_ingress_to_config_patch_manifest_v1(
    ingress: Mapping[str, Any],
    *,
    manifest_id: str | None = None,
    generated_at: datetime | None = None,
) -> ConfigPatchManifestV1:
    """Provenance-preserving governed projection — ingress ≠ ConfigPatch."""
    validated = validate_optimization_proposal_governance_ingress_v1(ingress)
    surface_id = str(validated["optimization_surface_id"])
    patch_target = f"research.optimizable_surface.{surface_id}.candidate_parameter_region"
    target_check = validate_patch_target(patch_target)
    if not target_check.valid:
        raise OptimizationProposalGovernanceIngressError(f"PATCH_TARGET_FORBIDDEN:{patch_target}")

    provenance = dict(validated["optimization_provenance"])
    patch_id = f"opt-ingress-{str(validated['ingress_digest'])[:16]}"
    patch = ConfigPatch(
        id=patch_id,
        target=patch_target,
        old_value=None,
        new_value=dict(validated["parameter_config_delta"]),
        status=PatchStatus.PROPOSED,
        generated_at=generated_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reason="optimization_proposal_governance_ingress_v1_projection",
        source_experiment_id=str(validated["experiment_id"]),
        meta={
            "optimization_ingress_digest": validated["ingress_digest"],
            "optimization_evidence_record_id": validated["optimization_evidence_record_id"],
            "optimization_evidence_content_hash": validated["optimization_evidence_content_hash"],
            "candidate_ref": validated["candidate_ref"],
            "plane_identity": validated["plane_identity"],
            "optimization_provenance_ref": provenance,
            "ingress_is_authoritative_provenance": True,
            "config_patch_manifest_is_change_representation_only": True,
        },
    )

    patch_payload = {
        "id": patch.id,
        "target": patch.target,
        "old_value": patch.old_value,
        "new_value": patch.new_value,
        "status": patch.status.value,
        "reason": patch.reason,
        "source_experiment_id": patch.source_experiment_id,
        "meta": dict(patch.meta),
    }
    manifest_body_without_integrity = {
        "schema_version": SCHEMA_VERSION_V1,
        "manifest_id": manifest_id or str(uuid.uuid4()),
        "generated_at": (generated_at or datetime(1970, 1, 1, tzinfo=timezone.utc)).isoformat(),
        "source_scope": {
            "ingress_schema_version": SCHEMA_VERSION,
            "ingress_domain": INGRESS_DOMAIN,
            "optimization_surface_id": surface_id,
            "ingress_digest": validated["ingress_digest"],
            "optimization_provenance": provenance,
        },
        "trading_logic_immutability_ref": canonical_trading_logic_immutability_ref(),
        "patches": [patch_payload],
        "generated_by": INGRESS_DOMAIN,
        "metadata": {
            "projection_kind": "OPTIMIZATION_INGRESS_TO_CONFIG_PATCH_MANIFEST_V1",
            "optimization_provenance_preserved": True,
            "futures_scope_ref": canonical_futures_scope_ref(),
        },
    }
    content_hash = compute_content_sha256(manifest_body_without_integrity)
    return ConfigPatchManifestV1(
        schema_version=SCHEMA_VERSION_V1,
        manifest_id=str(manifest_body_without_integrity["manifest_id"]),
        generated_at=generated_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
        source_scope=dict(manifest_body_without_integrity["source_scope"]),
        trading_logic_immutability_ref=canonical_trading_logic_immutability_ref(),
        patches=[patch],
        generated_by=INGRESS_DOMAIN,
        metadata=dict(manifest_body_without_integrity["metadata"]),
        integrity=ManifestIntegrity(content_sha256=content_hash),
    )


def _load_json_ref(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    if not path.is_file():
        raise OptimizationProposalGovernanceIngressError(
            f"CONSTRAINT_REF_NOT_FOUND:{relative_path}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OptimizationProposalGovernanceIngressError(
            f"CONSTRAINT_REF_NOT_MAPPING:{relative_path}"
        )
    return payload


def _validate_parameter_delta_for_surface_v1(
    *,
    surface_id: str,
    parameter_config_delta: Mapping[str, Any],
    risk_constraints_ref: str,
) -> tuple[bool, str]:
    risk_doc = _load_json_ref(risk_constraints_ref)
    if risk_doc.get("surface_id") and str(risk_doc["surface_id"]) != surface_id:
        return False, "RISK_CONSTRAINT_SURFACE_MISMATCH"
    if risk_doc.get("promotion_forbidden") is not True:
        return False, "RISK_CONSTRAINT_PROMOTION_NOT_FORBIDDEN"
    if risk_doc.get("master_v2_mutation_forbidden") is not True:
        return False, "RISK_CONSTRAINT_CORE_MUTATION_NOT_FORBIDDEN"

    if surface_id == M9_SURFACE_ID:
        bounds = _load_json_ref(
            "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json"
        )
        allowed = bounds.get("candidate_max_age_seconds")
        if not isinstance(allowed, list):
            return False, "M9_BOUNDS_MISSING"
        if set(parameter_config_delta.keys()) != {"max_age_seconds"}:
            return False, "CANDIDATE_TARGET_MISMATCH"
        value = parameter_config_delta.get("max_age_seconds")
        if value not in allowed:
            return False, "CANDIDATE_TARGET_OUT_OF_BOUNDS"
        return True, "PARAMETER_DELTA_BOUND_OK"

    if not parameter_config_delta:
        return False, "CANDIDATE_TARGET_EMPTY"
    return True, "PARAMETER_DELTA_BOUND_OK_SURFACE_GENERIC"


def evaluate_optimization_proposal_governance_admission_v1(
    request: OptimizationProposalGovernanceAdmissionRequestV1,
) -> OptimizationProposalGovernanceAdmissionResultV1:
    """Fail-closed governance/risk admission — review slot only, never productive apply."""
    reason_codes: list[str] = []

    if request.requested_promotion:
        reason_codes.append("REQUESTED_PROMOTION_FORBIDDEN")
    if request.requested_productive_apply:
        reason_codes.append("REQUESTED_PRODUCTIVE_APPLY_FORBIDDEN")
    if request.requested_runtime_authority:
        reason_codes.append(REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN)
    if request.requested_deployment_activation:
        reason_codes.append(REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN)

    try:
        ingress = validate_optimization_proposal_governance_ingress_v1(request.ingress)
    except OptimizationProposalGovernanceIngressError as exc:
        return OptimizationProposalGovernanceAdmissionResultV1(
            admission_status=ADMISSION_DENIED,
            reason_codes=(*reason_codes, str(exc)),
            ingress_digest=None,
        )

    ingress_digest = str(ingress["ingress_digest"])
    productive_target = ingress.get("requested_productive_target")
    if productive_target:
        reason_codes.append("REQUESTED_PRODUCTIVE_TARGET_FORBIDDEN_AT_INGRESS")

    surface_id = str(ingress["optimization_surface_id"])
    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    if resolution.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        reason_codes.append(f"ENVELOPE_UNAUTHORIZED:{resolution.get('reason')}")

    risk_ref = str(ingress["governance_risk_constraints_ref"])
    param_ok, param_reason = _validate_parameter_delta_for_surface_v1(
        surface_id=surface_id,
        parameter_config_delta=dict(ingress["parameter_config_delta"]),
        risk_constraints_ref=risk_ref,
    )
    if not param_ok:
        reason_codes.append(param_reason)

    if ingress.get("envelope_identity") != resolution.get("envelope_identity"):
        reason_codes.append("ENVELOPE_IDENTITY_DRIFT")

    if reason_codes:
        return OptimizationProposalGovernanceAdmissionResultV1(
            admission_status=ADMISSION_DENIED,
            reason_codes=tuple(reason_codes),
            ingress_digest=ingress_digest,
        )

    manifest = project_optimization_ingress_to_config_patch_manifest_v1(ingress)

    return OptimizationProposalGovernanceAdmissionResultV1(
        admission_status=ADMISSION_ADMITTED,
        reason_codes=("ADMITTED_FOR_GOVERNANCE_REVIEW_ONLY",),
        ingress_digest=ingress_digest,
        config_patch_manifest_projection=manifest,
        fence_layer="PROPOSAL",
        promotion_authority=PROMOTION_AUTHORITY,
        productive_apply_authority=PRODUCTIVE_APPLY_AUTHORITY,
        economic_gate_authority_effect=ECONOMIC_GATE_AUTHORITY_EFFECT_NONE,
    )


def optimization_ingress_contract_fence_layer_v1() -> tuple[str, ...]:
    """WP-02 compatible layer — ingress stops before productive mutation layers."""
    return CONTRACT_LAYERS


def direct_productive_write_possible_v1() -> bool:
    """Static proof hook: optimization ingress path cannot write productive config."""
    return OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG
