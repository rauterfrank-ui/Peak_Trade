"""Governed productive configuration v1 (M10 Slice B).

Materializes typed configuration artifacts only from valid explicit productive
authorization. Does not apply to runtime, mutate policy, or enable enforcement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    STATUS_AUTHORIZED_BOUNDARY,
    ExplicitProductiveAuthorizationResultV1,
    compute_candidate_parameter_value_digest_v1,
    verify_authorization_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
    PRODUCTIVE_TARGET_VERSION,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
    validate_productive_target_id_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    validate_numeric_max_age_seconds_domain_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    DISPOSITION_PROPOSAL_ONLY,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "governed_productive_configuration_v1"
CONFIGURATION_DOMAIN: Final[str] = "peak_trade.governance.governed_productive_configuration.v1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/GOVERNED_PRODUCTIVE_CONFIGURATION_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_productive_configuration_v1_decision_v1.json"
)

DISPOSITION_CONFIGURATION_ONLY: Final[str] = "CONFIGURATION_ONLY"
STATUS_MATERIALIZED: Final[str] = "MATERIALIZED_GOVERNED_PRODUCTIVE_CONFIGURATION"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

VALUE_AUTHORIZATION_SCOPE: Final[str] = "OWNER_EXPLICIT_RECORD_BOUND_CANDIDATE_VALUE_DIGEST"
GLOBAL_THRESHOLD_VALUE_RATIFIED: Final[bool] = False

CONFIGURATION_OWNER: Final[str] = "src.governance.governed_productive_configuration_v1"
RUNTIME_APPLY_AUTHORITY: Final[str] = "NONE"
POLICY_MUTATION_AUTHORITY: Final[str] = "NONE"
ENFORCEMENT_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_MATERIALIZATION_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False


class GovernedProductiveConfigurationError(ValueError):
    """Fail-closed governed productive configuration error."""


@dataclass(frozen=True)
class GovernedProductiveConfigurationMaterializeRequestV1:
    authorization: ExplicitProductiveAuthorizationResultV1
    ingress: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class GovernedProductiveConfigurationResultV1:
    configuration_status: str
    reason_codes: tuple[str, ...]
    configuration_disposition: str
    configuration_digest: str | None
    configuration_record: MappingProxyType[str, Any] | None
    runtime_apply_authority: str = RUNTIME_APPLY_AUTHORITY
    policy_mutation_authority: str = POLICY_MUTATION_AUTHORITY
    enforcement_authority: str = ENFORCEMENT_AUTHORITY
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def _extract_exact_candidate_numeric_value_v1(
    parameter_config_delta: Mapping[str, Any],
) -> tuple[float | None, str | None]:
    if set(parameter_config_delta.keys()) != {SOURCE_CANDIDATE_PARAMETER}:
        return None, "CANDIDATE_PARAMETER_MAPPING_MISMATCH"
    raw = parameter_config_delta.get(SOURCE_CANDIDATE_PARAMETER)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None, "CANDIDATE_NUMERIC_TYPE_INVALID"
    numeric = float(raw)
    if numeric != numeric or numeric <= 0.0:
        return None, "CANDIDATE_NUMERIC_NOT_POSITIVE_FINITE"
    if int(numeric) != numeric:
        return None, "CANDIDATE_NUMERIC_NOT_INTEGER_SECONDS"
    return numeric, None


def materialize_governed_productive_configuration_v1(
    request: GovernedProductiveConfigurationMaterializeRequestV1,
) -> GovernedProductiveConfigurationResultV1:
    """Fail-closed materialization from explicit productive authorization only."""
    reason_codes: list[str] = []
    authorization = request.authorization

    if authorization.authorization_status != STATUS_AUTHORIZED_BOUNDARY:
        reason_codes.append("AUTHORIZATION_NOT_AT_PRODUCTIVE_CONFIGURATION_BOUNDARY")
    if not authorization.authorized_for_productive_configuration_boundary:
        reason_codes.append("AUTHORIZATION_BOUNDARY_FLAG_FALSE")
    record = authorization.authorization_record
    if record is None:
        reason_codes.append("AUTHORIZATION_RECORD_MISSING")
        return _deny(reason_codes)

    if not verify_authorization_record_digest_v1(record):
        reason_codes.append("AUTHORIZATION_DIGEST_MISMATCH")

    if record.get("threshold_value_ratified") is True:
        reason_codes.append("GLOBAL_THRESHOLD_VALUE_RATIFICATION_NOT_IN_SCOPE")
    if record.get("candidate_value_applied") is True:
        reason_codes.append("CANDIDATE_VALUE_APPLY_FORBIDDEN")
    if record.get("enforcement_enabled") is True:
        reason_codes.append("ENFORCEMENT_FORBIDDEN")

    auth_digest = str(record.get("authorization_digest") or "")
    if not is_valid_sha256_hex(auth_digest):
        reason_codes.append("AUTHORIZATION_DIGEST_INVALID")

    owner_record_digest = str(record.get("owner_authorization_record_digest") or "")
    if not is_valid_sha256_hex(owner_record_digest):
        reason_codes.append("OWNER_AUTHORIZATION_RECORD_DIGEST_MISSING")

    target_id = str(record.get("productive_target_id") or "")
    target_ok, target_reason = validate_productive_target_id_v1(target_id)
    if not target_ok:
        reason_codes.append(target_reason)
    if target_id != PRODUCTIVE_TARGET_ID:
        reason_codes.append("PRODUCTIVE_TARGET_ID_NOT_EXACT_M9")

    if str(record.get("optimization_surface_id") or "") != OPTIMIZATION_SURFACE_ID:
        reason_codes.append("OPTIMIZATION_SURFACE_MISMATCH")
    if record.get("disposition") != DISPOSITION_PROPOSAL_ONLY:
        reason_codes.append("DISPOSITION_NOT_PROPOSAL_ONLY")
    if record.get("admission_status") != ADMISSION_ADMITTED:
        reason_codes.append("ADMISSION_STATUS_NOT_ADMITTED")
    if record.get("source_candidate_parameter") != SOURCE_CANDIDATE_PARAMETER:
        reason_codes.append("SOURCE_CANDIDATE_PARAMETER_MISMATCH")
    if record.get("target_policy_parameter") != TARGET_POLICY_PARAMETER:
        reason_codes.append("TARGET_POLICY_PARAMETER_MISMATCH")
    if record.get("target_unit") != TARGET_UNIT:
        reason_codes.append("TARGET_UNIT_MISMATCH")
    if record.get("ratified_threshold_capability_id") != RATIFIED_THRESHOLD_CAPABILITY_ID:
        reason_codes.append("RATIFIED_THRESHOLD_CAPABILITY_MISMATCH")

    delta = record.get("parameter_config_delta")
    if not isinstance(delta, Mapping):
        reason_codes.append("PARAMETER_CONFIG_DELTA_MISSING")
        return _deny(reason_codes)

    candidate_numeric, numeric_reason = _extract_exact_candidate_numeric_value_v1(delta)
    if candidate_numeric is None:
        reason_codes.append(numeric_reason or "CANDIDATE_NUMERIC_INVALID")

    expected_value_digest = str(record.get("candidate_parameter_value_digest") or "")
    recomputed_digest = compute_candidate_parameter_value_digest_v1(delta)
    if expected_value_digest != recomputed_digest:
        reason_codes.append("CANDIDATE_VALUE_DIGEST_MISMATCH")

    if candidate_numeric is not None:
        domain_ok, domain_reason = validate_numeric_max_age_seconds_domain_v1(candidate_numeric)
        if not domain_ok:
            reason_codes.append(domain_reason)

    ingress_digest = str(record.get("ingress_digest") or "")
    if request.ingress is not None:
        try:
            ingress = validate_optimization_proposal_governance_ingress_v1(request.ingress)
        except Exception as exc:
            reason_codes.append(str(exc))
            ingress = None
        if ingress is not None:
            if str(ingress.get("ingress_digest") or "") != ingress_digest:
                reason_codes.append("INGRESS_DIGEST_MISMATCH")
            ingress_delta = ingress.get("parameter_config_delta")
            if isinstance(ingress_delta, Mapping) and candidate_numeric is not None:
                ingress_numeric, ingress_numeric_reason = _extract_exact_candidate_numeric_value_v1(
                    ingress_delta
                )
                if ingress_numeric is None:
                    reason_codes.append(
                        ingress_numeric_reason or "INGRESS_CANDIDATE_NUMERIC_INVALID"
                    )
                elif ingress_numeric != candidate_numeric:
                    reason_codes.append("INGRESS_AUTHORIZATION_NUMERIC_MISMATCH")

    if reason_codes:
        return _deny(reason_codes)

    assert candidate_numeric is not None
    configuration_id = str(uuid.uuid5(uuid.NAMESPACE_URL, auth_digest))

    configuration_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": CONFIGURATION_DOMAIN,
        "configuration_id": configuration_id,
        "configuration_disposition": DISPOSITION_CONFIGURATION_ONLY,
        "configuration_status": STATUS_MATERIALIZED,
        "configuration_owner": CONFIGURATION_OWNER,
        "authorization_id": record.get("authorization_id"),
        "authorization_digest": auth_digest,
        "authorization_status": STATUS_AUTHORIZED_BOUNDARY,
        "owner_authorization_record_digest": owner_record_digest,
        "owner_authorization_id": record.get("owner_authorization_id"),
        "ingress_digest": ingress_digest,
        "admission_status": record.get("admission_status"),
        "disposition": record.get("disposition"),
        "experiment_id": record.get("experiment_id"),
        "candidate_ref": record.get("candidate_ref"),
        "optimization_surface_id": record.get("optimization_surface_id"),
        "optimization_evidence_record_id": record.get("optimization_evidence_record_id"),
        "optimization_evidence_content_hash": record.get("optimization_evidence_content_hash"),
        "optimization_evidence_reproducibility_digest": record.get(
            "optimization_evidence_reproducibility_digest"
        ),
        "learning_evidence_digest": record.get("learning_evidence_digest"),
        "plane_identity": record.get("plane_identity"),
        "plane_result_digest": record.get("plane_result_digest"),
        "envelope_identity": record.get("envelope_identity"),
        "optimization_provenance": dict(record.get("optimization_provenance") or {}),
        "productive_target_id": target_id,
        "productive_target_version": record.get("productive_target_version"),
        "productive_target_owner": record.get("productive_target_owner"),
        "productive_target_contract_digest": record.get("productive_target_contract_digest"),
        "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
        "target_policy_parameter": TARGET_POLICY_PARAMETER,
        "target_unit": TARGET_UNIT,
        "candidate_parameter_value_digest": expected_value_digest,
        "parameter_config_delta": dict(delta),
        "authorized_candidate_max_age_seconds": candidate_numeric,
        "numeric_max_age_seconds": candidate_numeric,
        "exact_value_preservation": True,
        "value_authorization_scope": VALUE_AUTHORIZATION_SCOPE,
        "global_threshold_value_ratified": GLOBAL_THRESHOLD_VALUE_RATIFIED,
        "threshold_capability_id": RATIFIED_THRESHOLD_CAPABILITY_ID,
        "threshold_capability_version": RATIFIED_THRESHOLD_CAPABILITY_VERSION,
        "threshold_capability_semantic_status": THRESHOLD_STATUS_RATIFIED_NUMERIC,
        "threshold_capability_classifies_configuration_value": True,
        "risk_constraints_ref": record.get("risk_constraints_ref"),
        "governance_risk_constraints_ref": record.get("governance_risk_constraints_ref"),
        "runtime_apply_authority": RUNTIME_APPLY_AUTHORITY,
        "policy_mutation_authority": POLICY_MUTATION_AUTHORITY,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "enforcement_enabled": False,
        "consumer_bound": False,
        "runtime_applied": False,
        "optimization_materialization_authority": OPTIMIZATION_MATERIALIZATION_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "lineage_chain": (
            "SURFACE",
            "CANDIDATE",
            "EVIDENCE",
            "INGRESS",
            "GOVERNANCE_REVIEW_ADMISSION",
            "OWNER_AUTHORIZATION",
            "EXPLICIT_PRODUCTIVE_AUTHORIZATION",
            "GOVERNED_PRODUCTIVE_CONFIGURATION",
        ),
    }
    configuration_digest = compute_content_sha256(configuration_body)
    configuration_body["configuration_digest"] = configuration_digest

    return GovernedProductiveConfigurationResultV1(
        configuration_status=STATUS_MATERIALIZED,
        reason_codes=("MATERIALIZED_GOVERNED_PRODUCTIVE_CONFIGURATION_ONLY",),
        configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
        configuration_digest=configuration_digest,
        configuration_record=MappingProxyType(configuration_body),
    )


def _deny(reason_codes: list[str]) -> GovernedProductiveConfigurationResultV1:
    return GovernedProductiveConfigurationResultV1(
        configuration_status=STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        configuration_disposition=DISPOSITION_CONFIGURATION_ONLY,
        configuration_digest=None,
        configuration_record=None,
    )


def runtime_apply_possible_v1() -> bool:
    return False


def policy_mutation_possible_v1() -> bool:
    return False


def optimization_can_materialize_configuration_v1() -> bool:
    return False


def verify_configuration_record_digest_v1(configuration_record: Mapping[str, Any]) -> bool:
    stored = configuration_record.get("configuration_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    body = {
        key: value
        for key, value in dict(configuration_record).items()
        if key != "configuration_digest"
    }
    return compute_content_sha256(body) == stored
