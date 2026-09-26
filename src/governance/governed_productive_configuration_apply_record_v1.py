"""Governed productive configuration apply record v1 (decision artifact only; no apply)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

APPLY_RECORD_SCHEMA_VERSION: Final[str] = "governed_productive_configuration_apply_record/v1"
APPLY_RECORD_DOMAIN: Final[str] = (
    "peak_trade.governance.governed_productive_configuration_apply_record.v1"
)
APPLY_AUTHORITY_ID: Final[str] = "GOVERNED_PRODUCTIVE_CONFIGURATION_APPLY_AUTHORITY_V1"

APPLY_RECORD_FIELD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "apply_record_id",
    "apply_schema_version",
    "apply_authority_id",
    "decision_state",
    "promotion_authorization_id",
    "authorized_promotion_record_digest",
    "candidate_id",
    "surface_id",
    "target_id",
    "authorized_candidate_parameter_value_digest",
    "evidence_lineage_digest",
    "governance_risk_authorization_ref",
    "productive_parameter_seam_ref",
    "productive_consumer_ref",
    "source_configuration_id",
    "source_configuration_digest",
    "materialization_target_configuration_schema_version",
    "materialization_target_configuration_id",
    "materialization_contract_disposition",
    "repository_provenance_digest",
    "reason_codes",
    "external_effect_authorized",
    "runtime_apply_started",
    "runtime_materialization_performed",
    "apply_record_digest",
)


class ProductiveConfigurationApplyDecisionStateV1(str, Enum):
    APPLY_ELIGIBLE = "APPLY_ELIGIBLE"
    APPLY_DENIED = "APPLY_DENIED"
    APPLY_AUTHORIZED = "APPLY_AUTHORIZED"
    APPLIED = "APPLIED"


class GovernedProductiveConfigurationApplyRecordError(ValueError):
    """Fail-closed apply record error."""


@dataclass(frozen=True, slots=True)
class GovernedProductiveConfigurationApplyRecordV1:
    apply_record: MappingProxyType[str, Any]
    apply_record_digest: str
    decision_state: ProductiveConfigurationApplyDecisionStateV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_record": dict(self.apply_record),
            "apply_record_digest": self.apply_record_digest,
            "decision_state": self.decision_state.value,
        }


def compute_evidence_lineage_digest_ref_v1(
    *,
    lineage_digest: str,
    ingress_digest: str,
    explicit_authorization_digest: str,
    owner_authorization_record_digest: str,
) -> str:
    body = {
        "lineage_digest": lineage_digest,
        "ingress_digest": ingress_digest,
        "explicit_authorization_digest": explicit_authorization_digest,
        "owner_authorization_record_digest": owner_authorization_record_digest,
    }
    return compute_content_sha256(body)


def compute_repository_provenance_digest_v1(*, configuration_record: Mapping[str, Any]) -> str:
    provenance = configuration_record.get("optimization_provenance")
    plane_identity = configuration_record.get("plane_identity")
    body = {
        "optimization_provenance": dict(provenance) if isinstance(provenance, Mapping) else {},
        "plane_identity": plane_identity,
        "experiment_id": configuration_record.get("experiment_id"),
    }
    return compute_content_sha256(body)


def compute_apply_record_digest_v1(record_body: Mapping[str, Any]) -> str:
    sealed = {
        key: record_body[key]
        for key in APPLY_RECORD_FIELD_KEYS
        if key != "apply_record_digest" and key in record_body
    }
    return compute_content_sha256(sealed)


def verify_apply_record_digest_v1(record: Mapping[str, Any]) -> bool:
    stored = record.get("apply_record_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    return compute_apply_record_digest_v1(record) == stored


def build_apply_record_body_v1(
    *,
    decision_state: ProductiveConfigurationApplyDecisionStateV1,
    promotion_authorization_id: str,
    authorized_promotion_record_digest: str,
    candidate_id: str,
    surface_id: str,
    target_id: str,
    authorized_candidate_parameter_value_digest: str,
    evidence_lineage_digest: str,
    governance_risk_authorization_ref: str,
    productive_parameter_seam_ref: str,
    productive_consumer_ref: str,
    source_configuration_id: str,
    source_configuration_digest: str,
    materialization_target_configuration_schema_version: str,
    materialization_target_configuration_id: str,
    repository_provenance_digest: str,
    reason_codes: tuple[str, ...],
) -> MappingProxyType[str, Any]:
    if decision_state == ProductiveConfigurationApplyDecisionStateV1.APPLIED:
        raise GovernedProductiveConfigurationApplyRecordError("APPLIED_STATE_NOT_REACHABLE_IN_WP")

    apply_record_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"governed-apply-record:{authorized_promotion_record_digest}:{decision_state.value}",
        )
    )
    body: dict[str, Any] = {
        "schema_version": APPLY_RECORD_SCHEMA_VERSION,
        "apply_record_id": apply_record_id,
        "apply_schema_version": APPLY_RECORD_SCHEMA_VERSION,
        "apply_authority_id": APPLY_AUTHORITY_ID,
        "decision_state": decision_state.value,
        "promotion_authorization_id": promotion_authorization_id,
        "authorized_promotion_record_digest": authorized_promotion_record_digest,
        "candidate_id": candidate_id,
        "surface_id": surface_id,
        "target_id": target_id,
        "authorized_candidate_parameter_value_digest": (
            authorized_candidate_parameter_value_digest
        ),
        "evidence_lineage_digest": evidence_lineage_digest,
        "governance_risk_authorization_ref": governance_risk_authorization_ref,
        "productive_parameter_seam_ref": productive_parameter_seam_ref,
        "productive_consumer_ref": productive_consumer_ref,
        "source_configuration_id": source_configuration_id,
        "source_configuration_digest": source_configuration_digest,
        "materialization_target_configuration_schema_version": (
            materialization_target_configuration_schema_version
        ),
        "materialization_target_configuration_id": materialization_target_configuration_id,
        "materialization_contract_disposition": "APPLY_DECISION_ONLY_NO_RUNTIME_MUTATION",
        "repository_provenance_digest": repository_provenance_digest,
        "reason_codes": list(reason_codes),
        "external_effect_authorized": False,
        "runtime_apply_started": False,
        "runtime_materialization_performed": False,
    }
    body["apply_record_digest"] = compute_apply_record_digest_v1(body)
    return MappingProxyType(body)


__all__ = [
    "APPLY_AUTHORITY_ID",
    "APPLY_RECORD_DOMAIN",
    "APPLY_RECORD_FIELD_KEYS",
    "APPLY_RECORD_SCHEMA_VERSION",
    "GovernedProductiveConfigurationApplyRecordError",
    "GovernedProductiveConfigurationApplyRecordV1",
    "ProductiveConfigurationApplyDecisionStateV1",
    "build_apply_record_body_v1",
    "compute_apply_record_digest_v1",
    "compute_evidence_lineage_digest_ref_v1",
    "compute_repository_provenance_digest_v1",
    "verify_apply_record_digest_v1",
]
