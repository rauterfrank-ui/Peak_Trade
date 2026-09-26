"""Governed runtime apply materialization record v1 (seam-bound evidence; no productive apply)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

MATERIALIZATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "governed_runtime_apply_materialization_record/v1"
)
MATERIALIZATION_RECORD_DOMAIN: Final[str] = (
    "peak_trade.governance.governed_runtime_apply_materialization_record.v1"
)
MATERIALIZATION_AUTHORITY_ID: Final[str] = "GOVERNED_RUNTIME_APPLY_MATERIALIZATION_V1"

MATERIALIZATION_RECORD_FIELD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "materialization_record_id",
    "materialization_authority_id",
    "decision_state",
    "p4_l6_seam_result_digest",
    "p3_binding_result_digest",
    "component_a_adjudication_digest",
    "optimization_envelope_content_hash",
    "lineage_chain_digest",
    "configuration_materialized",
    "configuration_applied",
    "productive_activation_authorized",
    "runtime_apply_started",
    "real_runtime_materialization_performed",
    "materialization_contract_disposition",
    "runtime_consumer_boundary",
    "reason_codes",
    "external_effect_authorized",
    "materialization_record_digest",
)


class RuntimeApplyMaterializationDecisionStateV1(str, Enum):
    MATERIALIZATION_ELIGIBLE = "MATERIALIZATION_ELIGIBLE"
    MATERIALIZATION_DENIED = "MATERIALIZATION_DENIED"
    MATERIALIZATION_AUTHORIZED = "MATERIALIZATION_AUTHORIZED"
    MATERIALIZATION_APPLIED = "MATERIALIZATION_APPLIED"


class GovernedRuntimeApplyMaterializationRecordError(ValueError):
    """Fail-closed runtime apply materialization record error."""


@dataclass(frozen=True, slots=True)
class GovernedRuntimeApplyMaterializationRecordV1:
    materialization_record: MappingProxyType[str, Any]
    materialization_record_digest: str
    decision_state: RuntimeApplyMaterializationDecisionStateV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_state": self.decision_state.value,
            "materialization_record": dict(self.materialization_record),
            "materialization_record_digest": self.materialization_record_digest,
        }


def compute_lineage_chain_digest_v1(*, lineage_chain: tuple[str, ...]) -> str:
    return compute_content_sha256({"lineage_chain": list(lineage_chain)})


def compute_materialization_record_digest_v1(record_body: Mapping[str, Any]) -> str:
    sealed = {
        key: record_body[key]
        for key in MATERIALIZATION_RECORD_FIELD_KEYS
        if key != "materialization_record_digest" and key in record_body
    }
    return compute_content_sha256(sealed)


def verify_materialization_record_digest_v1(record: Mapping[str, Any]) -> bool:
    stored = record.get("materialization_record_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    return compute_materialization_record_digest_v1(record) == stored


def build_materialization_record_body_v1(
    *,
    decision_state: RuntimeApplyMaterializationDecisionStateV1,
    p4_l6_seam_result_digest: str,
    p3_binding_result_digest: str,
    component_a_adjudication_digest: str,
    optimization_envelope_content_hash: str,
    lineage_chain_digest: str,
    reason_codes: tuple[str, ...],
    real_runtime_materialization_performed: bool,
) -> MappingProxyType[str, Any]:
    if decision_state == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_APPLIED:
        raise GovernedRuntimeApplyMaterializationRecordError(
            "MATERIALIZATION_APPLIED_NOT_REACHABLE_IN_WP"
        )
    if not all(
        is_valid_sha256_hex(value)
        for value in (
            p4_l6_seam_result_digest,
            p3_binding_result_digest,
            component_a_adjudication_digest,
            optimization_envelope_content_hash,
            lineage_chain_digest,
        )
    ):
        raise GovernedRuntimeApplyMaterializationRecordError("MATERIALIZATION_DIGEST_INVALID")

    materialization_record_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"runtime-apply-materialization:{p4_l6_seam_result_digest}:{decision_state.value}",
        )
    )
    configuration_materialized = decision_state in (
        RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_ELIGIBLE,
        RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_AUTHORIZED,
    )
    body: dict[str, Any] = {
        "schema_version": MATERIALIZATION_RECORD_SCHEMA_VERSION,
        "materialization_record_id": materialization_record_id,
        "materialization_authority_id": MATERIALIZATION_AUTHORITY_ID,
        "decision_state": decision_state.value,
        "p4_l6_seam_result_digest": p4_l6_seam_result_digest,
        "p3_binding_result_digest": p3_binding_result_digest,
        "component_a_adjudication_digest": component_a_adjudication_digest,
        "optimization_envelope_content_hash": optimization_envelope_content_hash,
        "lineage_chain_digest": lineage_chain_digest,
        "configuration_materialized": configuration_materialized,
        "configuration_applied": False,
        "productive_activation_authorized": False,
        "runtime_apply_started": False,
        "real_runtime_materialization_performed": real_runtime_materialization_performed,
        "materialization_contract_disposition": (
            "SEAM_SCOPED_L6_TYPED_MATERIALIZATION_ONLY_NO_PRODUCTIVE_APPLY"
        ),
        "runtime_consumer_boundary": "STOP_BEFORE_COMPONENT_B_AND_PRODUCTIVE_ACTIVATION",
        "reason_codes": list(reason_codes),
        "external_effect_authorized": False,
    }
    body["materialization_record_digest"] = compute_materialization_record_digest_v1(body)
    return MappingProxyType(body)


__all__ = [
    "MATERIALIZATION_AUTHORITY_ID",
    "MATERIALIZATION_RECORD_DOMAIN",
    "MATERIALIZATION_RECORD_FIELD_KEYS",
    "MATERIALIZATION_RECORD_SCHEMA_VERSION",
    "GovernedRuntimeApplyMaterializationRecordError",
    "GovernedRuntimeApplyMaterializationRecordV1",
    "RuntimeApplyMaterializationDecisionStateV1",
    "build_materialization_record_body_v1",
    "compute_lineage_chain_digest_v1",
    "compute_materialization_record_digest_v1",
    "verify_materialization_record_digest_v1",
]
