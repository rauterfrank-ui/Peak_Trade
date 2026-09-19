"""Explicit productive authorization v1 (M10 Slice A).

Fail-closed edge from governance review admission to typed productive authorization
only. Does not materialize productive configuration, ratify threshold values,
mutate policy, or apply candidates.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
    PRODUCTIVE_TARGET_OWNER,
    PRODUCTIVE_TARGET_VERSION,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
    build_productive_target_contract_v1,
    validate_productive_target_id_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
    build_ratified_threshold_capability_identity_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    DISPOSITION_PROPOSAL_ONLY,
    OptimizationProposalGovernanceAdmissionResultV1,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "explicit_productive_authorization_v1"
AUTHORIZATION_DOMAIN: Final[str] = "peak_trade.governance.explicit_productive_authorization.v1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/EXPLICIT_PRODUCTIVE_AUTHORIZATION_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = (
    "config/governance/explicit_productive_authorization_v1_decision_v1.json"
)
OWNER_BOUNDARY_CONFIG: Final[str] = (
    "config/governance/explicit_productive_authorization_v1_owner_boundary_v1.json"
)

OWNER_INPUT_SCHEMA_VERSION: Final[str] = "explicit_productive_authorization_owner_input/v1"
DEFAULT_OWNER_AUTHORIZATION_ID: Final[str] = "explicit_productive_authorization_m9_owner_input/v1"

DISPOSITION_AUTHORIZATION_ONLY: Final[str] = "AUTHORIZATION_ONLY"
STATUS_AUTHORIZED_BOUNDARY: Final[str] = "AUTHORIZED_FOR_PRODUCTIVE_CONFIGURATION_BOUNDARY"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

GOVERNED_PRODUCTIVE_CONFIGURATION_AUTHORITY: Final[str] = "NONE"
THRESHOLD_VALUE_RATIFICATION_AUTHORITY: Final[str] = "NONE"
POLICY_MUTATION_AUTHORITY: Final[str] = "NONE"
ENFORCEMENT_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PROMOTION_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_APPLY_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
AUTHORIZED_FOR_PRODUCTIVE_APPLY: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]

_OWNER_RECORD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_authorization_id",
    "owner_authorization_version",
    "authorizer_identity",
    "bound_ingress_digest",
    "bound_admission_status",
    "bound_disposition",
    "bound_optimization_surface_id",
    "bound_productive_target_id",
    "bound_productive_target_version",
    "bound_source_candidate_parameter",
    "bound_target_policy_parameter",
    "bound_target_unit",
    "bound_experiment_id",
    "bound_candidate_ref",
    "bound_candidate_parameter_value_digest",
    "bound_optimization_evidence_content_hash",
    "bound_optimization_evidence_reproducibility_digest",
    "bound_learning_evidence_digest",
    "bound_risk_constraints_ref",
    "bound_governance_risk_constraints_ref",
    "bound_ratified_threshold_capability_id",
)


class ExplicitProductiveAuthorizationError(ValueError):
    """Fail-closed explicit productive authorization error."""


@dataclass(frozen=True)
class OwnerExplicitProductiveAuthorizationInputV1:
    """Explicit Owner-ratified authorization input (not inferable from admission)."""

    owner_authorization_record: Mapping[str, Any]
    owner_authorization_record_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_authorization_record": dict(self.owner_authorization_record),
            "owner_authorization_record_digest": self.owner_authorization_record_digest,
        }


@dataclass(frozen=True)
class ExplicitProductiveAuthorizationEvaluateRequestV1:
    ingress: Mapping[str, Any]
    admission: OptimizationProposalGovernanceAdmissionResultV1
    productive_target_id: str
    owner_authorization_input: OwnerExplicitProductiveAuthorizationInputV1 | None = None


@dataclass(frozen=True)
class ExplicitProductiveAuthorizationResultV1:
    authorization_status: str
    reason_codes: tuple[str, ...]
    authorization_disposition: str
    authorized_for_productive_configuration_boundary: bool
    authorization_digest: str | None
    authorization_record: MappingProxyType[str, Any] | None
    ingress_digest: str | None
    governed_productive_configuration_authority: str = GOVERNED_PRODUCTIVE_CONFIGURATION_AUTHORITY
    threshold_value_ratification_authority: str = THRESHOLD_VALUE_RATIFICATION_AUTHORITY
    policy_mutation_authority: str = POLICY_MUTATION_AUTHORITY
    enforcement_authority: str = ENFORCEMENT_AUTHORITY
    optimization_promotion_authority: str = OPTIMIZATION_PROMOTION_AUTHORITY
    optimization_apply_authority: str = OPTIMIZATION_APPLY_AUTHORITY
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ExplicitProductiveAuthorizationError(f"config_not_mapping:{relative_path}")
    return payload


def load_owner_boundary_v1() -> MappingProxyType[str, Any]:
    payload = _load_json(OWNER_BOUNDARY_CONFIG)
    allowed_targets = payload.get("allowed_productive_target_ids")
    if not isinstance(allowed_targets, list) or PRODUCTIVE_TARGET_ID not in allowed_targets:
        raise ExplicitProductiveAuthorizationError("OWNER_BOUNDARY_TARGET_ALLOWLIST_INVALID")
    return MappingProxyType(payload)


def compute_candidate_parameter_value_digest_v1(
    parameter_config_delta: Mapping[str, Any],
) -> str:
    return compute_content_sha256(
        {
            "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
            "parameter_config_delta": dict(parameter_config_delta),
        }
    )


def build_owner_explicit_productive_authorization_record_v1(
    *,
    ingress: Mapping[str, Any],
    productive_target_id: str,
    owner_authorization_id: str = DEFAULT_OWNER_AUTHORIZATION_ID,
    owner_authorization_version: str = OWNER_INPUT_SCHEMA_VERSION,
    authorizer_identity: str = "OWNER_EXPLICIT_PRODUCTIVE_AUTHORIZATION",
) -> MappingProxyType[str, Any]:
    """Canonical Owner record body (digest computed separately)."""
    validated = validate_optimization_proposal_governance_ingress_v1(ingress)
    delta = dict(validated["parameter_config_delta"])
    record = {
        "schema_version": OWNER_INPUT_SCHEMA_VERSION,
        "owner_authorization_id": owner_authorization_id,
        "owner_authorization_version": owner_authorization_version,
        "authorizer_identity": authorizer_identity,
        "bound_ingress_digest": str(validated["ingress_digest"]),
        "bound_admission_status": ADMISSION_ADMITTED,
        "bound_disposition": DISPOSITION_PROPOSAL_ONLY,
        "bound_optimization_surface_id": str(validated["optimization_surface_id"]),
        "bound_productive_target_id": productive_target_id,
        "bound_productive_target_version": PRODUCTIVE_TARGET_VERSION,
        "bound_source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
        "bound_target_policy_parameter": TARGET_POLICY_PARAMETER,
        "bound_target_unit": TARGET_UNIT,
        "bound_experiment_id": str(validated["experiment_id"]),
        "bound_candidate_ref": str(validated["candidate_ref"]),
        "bound_candidate_parameter_value_digest": compute_candidate_parameter_value_digest_v1(
            delta
        ),
        "bound_optimization_evidence_content_hash": str(
            validated["optimization_evidence_content_hash"]
        ),
        "bound_optimization_evidence_reproducibility_digest": str(
            validated["optimization_evidence_reproducibility_digest"]
        ),
        "bound_learning_evidence_digest": str(validated["learning_evidence_digest"]),
        "bound_risk_constraints_ref": str(validated["risk_constraints_ref"]),
        "bound_governance_risk_constraints_ref": str(validated["governance_risk_constraints_ref"]),
        "bound_ratified_threshold_capability_id": RATIFIED_THRESHOLD_CAPABILITY_ID,
    }
    missing = [key for key in _OWNER_RECORD_KEYS if key not in record]
    if missing:
        raise ExplicitProductiveAuthorizationError(f"OWNER_RECORD_INCOMPLETE:{','.join(missing)}")
    return MappingProxyType(record)


def compute_owner_authorization_record_digest_v1(
    owner_authorization_record: Mapping[str, Any],
) -> str:
    body = {key: owner_authorization_record[key] for key in _OWNER_RECORD_KEYS}
    return compute_content_sha256(body)


def build_owner_explicit_productive_authorization_input_v1(
    *,
    ingress: Mapping[str, Any],
    productive_target_id: str,
    owner_authorization_id: str = DEFAULT_OWNER_AUTHORIZATION_ID,
    authorizer_identity: str = "OWNER_EXPLICIT_PRODUCTIVE_AUTHORIZATION",
) -> OwnerExplicitProductiveAuthorizationInputV1:
    record = build_owner_explicit_productive_authorization_record_v1(
        ingress=ingress,
        productive_target_id=productive_target_id,
        owner_authorization_id=owner_authorization_id,
        authorizer_identity=authorizer_identity,
    )
    digest = compute_owner_authorization_record_digest_v1(record)
    return OwnerExplicitProductiveAuthorizationInputV1(
        owner_authorization_record=record,
        owner_authorization_record_digest=digest,
    )


def _validate_m9_parameter_mapping_v1(delta: Mapping[str, Any]) -> tuple[bool, str]:
    if set(delta.keys()) != {SOURCE_CANDIDATE_PARAMETER}:
        return False, "CANDIDATE_PARAMETER_MAPPING_MISMATCH"
    return True, "CANDIDATE_PARAMETER_MAPPING_OK"


def _validate_risk_refs_v1(
    *,
    surface_id: str,
    risk_constraints_ref: str,
) -> tuple[bool, str]:
    risk_doc = _load_json(risk_constraints_ref)
    if str(risk_doc.get("surface_id") or "") != surface_id:
        return False, "RISK_CONSTRAINT_SURFACE_MISMATCH"
    if risk_doc.get("threshold_selection_forbidden") is not True:
        return False, "THRESHOLD_SELECTION_NOT_FORBIDDEN_IN_RISK"
    return True, "RISK_REFS_OK"


def evaluate_explicit_productive_authorization_v1(
    request: ExplicitProductiveAuthorizationEvaluateRequestV1,
) -> ExplicitProductiveAuthorizationResultV1:
    """Fail-closed evaluator; admission alone never authorizes."""
    reason_codes: list[str] = []
    ingress_digest: str | None = None

    try:
        ingress = validate_optimization_proposal_governance_ingress_v1(request.ingress)
    except Exception as exc:
        return ExplicitProductiveAuthorizationResultV1(
            authorization_status=STATUS_DENIED,
            reason_codes=(str(exc),),
            authorization_disposition=DISPOSITION_AUTHORIZATION_ONLY,
            authorized_for_productive_configuration_boundary=False,
            authorization_digest=None,
            authorization_record=None,
            ingress_digest=None,
        )

    ingress_digest = str(ingress["ingress_digest"])

    if request.admission.admission_status != ADMISSION_ADMITTED:
        reason_codes.append("GOVERNANCE_REVIEW_ADMISSION_NOT_ADMITTED")
    if request.admission.ingress_digest != ingress_digest:
        reason_codes.append("ADMISSION_INGRESS_DIGEST_MISMATCH")
    if ingress.get("disposition") != DISPOSITION_PROPOSAL_ONLY:
        reason_codes.append("DISPOSITION_NOT_PROPOSAL_ONLY")

    surface_id = str(ingress["optimization_surface_id"])
    if surface_id != OPTIMIZATION_SURFACE_ID:
        reason_codes.append("OPTIMIZATION_SURFACE_NOT_M9")

    target_ok, target_reason = validate_productive_target_id_v1(request.productive_target_id)
    if not target_ok:
        reason_codes.append(target_reason)
    if request.productive_target_id != PRODUCTIVE_TARGET_ID:
        reason_codes.append("PRODUCTIVE_TARGET_ID_NOT_EXACT_M9")

    delta = dict(ingress["parameter_config_delta"])
    map_ok, map_reason = _validate_m9_parameter_mapping_v1(delta)
    if not map_ok:
        reason_codes.append(map_reason)
    if TARGET_UNIT != "SECONDS":
        reason_codes.append("TARGET_UNIT_INVALID")

    threshold_identity = build_ratified_threshold_capability_identity_v1()
    if threshold_identity.get("capability_id") != RATIFIED_THRESHOLD_CAPABILITY_ID:
        reason_codes.append("RATIFIED_THRESHOLD_CAPABILITY_MISSING")

    risk_ok, risk_reason = _validate_risk_refs_v1(
        surface_id=surface_id,
        risk_constraints_ref=str(ingress["risk_constraints_ref"]),
    )
    if not risk_ok:
        reason_codes.append(risk_reason)
    if ingress.get("governance_risk_constraints_ref") != ingress.get("risk_constraints_ref"):
        reason_codes.append("GOVERNANCE_RISK_REF_MISMATCH")

    provenance = ingress.get("optimization_provenance")
    if not isinstance(provenance, Mapping) or not provenance:
        reason_codes.append("OPTIMIZATION_PROVENANCE_MISSING")

    if request.owner_authorization_input is None:
        reason_codes.append("OWNER_AUTHORIZATION_INPUT_REQUIRED")
    else:
        owner_input = request.owner_authorization_input
        record = owner_input.owner_authorization_record
        if not isinstance(record, Mapping):
            reason_codes.append("OWNER_AUTHORIZATION_RECORD_INVALID")
        else:
            expected_digest = compute_owner_authorization_record_digest_v1(record)
            if owner_input.owner_authorization_record_digest != expected_digest:
                reason_codes.append("OWNER_AUTHORIZATION_RECORD_DIGEST_MISMATCH")
            if not is_valid_sha256_hex(owner_input.owner_authorization_record_digest):
                reason_codes.append("OWNER_AUTHORIZATION_RECORD_DIGEST_MALFORMED")

            boundary = load_owner_boundary_v1()
            allowed_ids = boundary.get("allowed_owner_authorization_ids") or []
            owner_auth_id = str(record.get("owner_authorization_id") or "")
            if owner_auth_id not in allowed_ids:
                reason_codes.append("OWNER_AUTHORIZATION_ID_NOT_ALLOWED")

            bindings: tuple[tuple[str, Any, Any], ...] = (
                ("bound_ingress_digest", record.get("bound_ingress_digest"), ingress_digest),
                (
                    "bound_admission_status",
                    record.get("bound_admission_status"),
                    ADMISSION_ADMITTED,
                ),
                ("bound_disposition", record.get("bound_disposition"), DISPOSITION_PROPOSAL_ONLY),
                (
                    "bound_optimization_surface_id",
                    record.get("bound_optimization_surface_id"),
                    surface_id,
                ),
                (
                    "bound_productive_target_id",
                    record.get("bound_productive_target_id"),
                    request.productive_target_id,
                ),
                (
                    "bound_productive_target_version",
                    record.get("bound_productive_target_version"),
                    PRODUCTIVE_TARGET_VERSION,
                ),
                (
                    "bound_source_candidate_parameter",
                    record.get("bound_source_candidate_parameter"),
                    SOURCE_CANDIDATE_PARAMETER,
                ),
                (
                    "bound_target_policy_parameter",
                    record.get("bound_target_policy_parameter"),
                    TARGET_POLICY_PARAMETER,
                ),
                ("bound_target_unit", record.get("bound_target_unit"), TARGET_UNIT),
                (
                    "bound_experiment_id",
                    record.get("bound_experiment_id"),
                    str(ingress["experiment_id"]),
                ),
                (
                    "bound_candidate_ref",
                    record.get("bound_candidate_ref"),
                    str(ingress["candidate_ref"]),
                ),
                (
                    "bound_candidate_parameter_value_digest",
                    record.get("bound_candidate_parameter_value_digest"),
                    compute_candidate_parameter_value_digest_v1(delta),
                ),
                (
                    "bound_optimization_evidence_content_hash",
                    record.get("bound_optimization_evidence_content_hash"),
                    str(ingress["optimization_evidence_content_hash"]),
                ),
                (
                    "bound_optimization_evidence_reproducibility_digest",
                    record.get("bound_optimization_evidence_reproducibility_digest"),
                    str(ingress["optimization_evidence_reproducibility_digest"]),
                ),
                (
                    "bound_learning_evidence_digest",
                    record.get("bound_learning_evidence_digest"),
                    str(ingress["learning_evidence_digest"]),
                ),
                (
                    "bound_risk_constraints_ref",
                    record.get("bound_risk_constraints_ref"),
                    str(ingress["risk_constraints_ref"]),
                ),
                (
                    "bound_governance_risk_constraints_ref",
                    record.get("bound_governance_risk_constraints_ref"),
                    str(ingress["governance_risk_constraints_ref"]),
                ),
                (
                    "bound_ratified_threshold_capability_id",
                    record.get("bound_ratified_threshold_capability_id"),
                    RATIFIED_THRESHOLD_CAPABILITY_ID,
                ),
            )
            for field, actual, expected in bindings:
                if actual != expected:
                    reason_codes.append(f"OWNER_BINDING_MISMATCH:{field}")

    if reason_codes:
        return ExplicitProductiveAuthorizationResultV1(
            authorization_status=STATUS_DENIED,
            reason_codes=tuple(reason_codes),
            authorization_disposition=DISPOSITION_AUTHORIZATION_ONLY,
            authorized_for_productive_configuration_boundary=False,
            authorization_digest=None,
            authorization_record=None,
            ingress_digest=ingress_digest,
        )

    target_contract = build_productive_target_contract_v1()
    candidate_value_digest = compute_candidate_parameter_value_digest_v1(delta)
    authorization_id = str(uuid.uuid5(uuid.NAMESPACE_URL, ingress_digest))

    record_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": AUTHORIZATION_DOMAIN,
        "authorization_id": authorization_id,
        "authorization_disposition": DISPOSITION_AUTHORIZATION_ONLY,
        "authorization_status": STATUS_AUTHORIZED_BOUNDARY,
        "authorized_for_productive_configuration_boundary": True,
        "admission_status": ADMISSION_ADMITTED,
        "ingress_digest": ingress_digest,
        "experiment_id": str(ingress["experiment_id"]),
        "candidate_ref": str(ingress["candidate_ref"]),
        "optimization_surface_id": surface_id,
        "disposition": DISPOSITION_PROPOSAL_ONLY,
        "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
        "target_policy_parameter": TARGET_POLICY_PARAMETER,
        "target_unit": TARGET_UNIT,
        "candidate_parameter_value_digest": candidate_value_digest,
        "parameter_config_delta": delta,
        "productive_target_id": request.productive_target_id,
        "productive_target_version": PRODUCTIVE_TARGET_VERSION,
        "productive_target_owner": PRODUCTIVE_TARGET_OWNER,
        "productive_target_contract_digest": target_contract["contract_digest"],
        "optimization_evidence_record_id": ingress["optimization_evidence_record_id"],
        "optimization_evidence_content_hash": ingress["optimization_evidence_content_hash"],
        "optimization_evidence_reproducibility_digest": ingress[
            "optimization_evidence_reproducibility_digest"
        ],
        "learning_evidence_digest": ingress["learning_evidence_digest"],
        "plane_identity": ingress["plane_identity"],
        "plane_result_digest": ingress["plane_result_digest"],
        "envelope_identity": ingress["envelope_identity"],
        "risk_constraints_ref": ingress["risk_constraints_ref"],
        "governance_risk_constraints_ref": ingress["governance_risk_constraints_ref"],
        "optimization_provenance": dict(ingress["optimization_provenance"]),
        "ratified_threshold_capability_id": RATIFIED_THRESHOLD_CAPABILITY_ID,
        "ratified_threshold_capability_version": RATIFIED_THRESHOLD_CAPABILITY_VERSION,
        "owner_authorization_id": str(
            request.owner_authorization_input.owner_authorization_record.get(
                "owner_authorization_id"
            )
        ),
        "owner_authorization_record_digest": (
            request.owner_authorization_input.owner_authorization_record_digest
        ),
        "governed_productive_configuration_authority": GOVERNED_PRODUCTIVE_CONFIGURATION_AUTHORITY,
        "threshold_value_ratification_authority": THRESHOLD_VALUE_RATIFICATION_AUTHORITY,
        "policy_mutation_authority": POLICY_MUTATION_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "optimization_apply_authority": OPTIMIZATION_APPLY_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "threshold_value_ratified": False,
        "candidate_value_applied": False,
        "enforcement_enabled": False,
    }
    authorization_digest = compute_content_sha256(record_body)
    record_body["authorization_digest"] = authorization_digest

    return ExplicitProductiveAuthorizationResultV1(
        authorization_status=STATUS_AUTHORIZED_BOUNDARY,
        reason_codes=("AUTHORIZED_FOR_PRODUCTIVE_CONFIGURATION_BOUNDARY_ONLY",),
        authorization_disposition=DISPOSITION_AUTHORIZATION_ONLY,
        authorized_for_productive_configuration_boundary=True,
        authorization_digest=authorization_digest,
        authorization_record=MappingProxyType(record_body),
        ingress_digest=ingress_digest,
    )


def verify_authorization_record_digest_v1(authorization_record: Mapping[str, Any]) -> bool:
    stored = authorization_record.get("authorization_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    body = {
        key: value
        for key, value in dict(authorization_record).items()
        if key != "authorization_digest"
    }
    return compute_content_sha256(body) == stored


def governed_productive_configuration_write_possible_v1() -> bool:
    return False


def policy_mutation_possible_v1() -> bool:
    return False


def direct_productive_write_possible_v1() -> bool:
    return False
