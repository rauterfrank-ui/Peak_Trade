"""Governed productive runtime parameter seam join v1.

Transport-only boundary: validates an already-bound authorized productive
parameter seam record and supplies it to the CURRENT presence gate consumer.
Does not materialize configuration, authorize, or read optimization ingress.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    SEAM_DISPOSITION,
    SEAM_OWNER,
    STATUS_BOUND,
    verify_seam_record_digest_v1,
)
from src.governance.f1_m9_scoped_owner_apply_constants_v1 import (
    is_f1_m9_scoped_runtime_apply_authority_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
    PRODUCTIVE_TARGET_VERSION,
    validate_productive_target_id_v1,
)

SCHEMA_VERSION: Final[str] = "governed_productive_runtime_parameter_seam_join_v1"
JOIN_OWNER: Final[str] = "src.governance.governed_productive_runtime_parameter_seam_join_v1"
RUNTIME_JOIN_DISPOSITION: Final[str] = "GOVERNED_PRODUCTIVE_RUNTIME_PARAMETER_SEAM_TRANSPORT_ONLY"
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_productive_runtime_parameter_seam_join_v1_decision_v1.json"
)

STATUS_TRANSPORT_READY: Final[str] = "RUNTIME_SEAM_TRANSPORT_READY"
STATUS_TRANSPORT_DENIED: Final[str] = "RUNTIME_SEAM_TRANSPORT_DENIED_FAIL_CLOSED"

ENFORCEMENT_AUTHORITY: Final[str] = "NONE"
TRADING_DECISION_AUTHORITY: Final[str] = "MV2_DOUBLE_PLAY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
OPTIMIZATION_DIRECT_RUNTIME_WRITE: Final[str] = "NONE"


@dataclass(frozen=True)
class GovernedRuntimeSeamTransportResultV1:
    transport_status: str
    reason_codes: tuple[str, ...]
    seam_for_consumer: Mapping[str, Any] | None
    enforcement_authority: str = ENFORCEMENT_AUTHORITY
    trading_decision_authority: str = TRADING_DECISION_AUTHORITY
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def _deny(reason_codes: list[str]) -> GovernedRuntimeSeamTransportResultV1:
    return GovernedRuntimeSeamTransportResultV1(
        transport_status=STATUS_TRANSPORT_DENIED,
        reason_codes=tuple(reason_codes),
        seam_for_consumer=None,
    )


def resolve_governed_runtime_seam_for_presence_gate_v1(
    seam_record: Mapping[str, Any] | None,
) -> GovernedRuntimeSeamTransportResultV1:
    """Fail-closed transport: invalid/missing seam → None for consumer (unresolved path)."""
    if seam_record is None:
        return GovernedRuntimeSeamTransportResultV1(
            transport_status=STATUS_TRANSPORT_DENIED,
            reason_codes=("RUNTIME_SEAM_RECORD_MISSING",),
            seam_for_consumer=None,
        )

    reasons: list[str] = []

    if seam_record.get("optimization_ingress_digest"):
        reasons.append("OPTIMIZATION_INGRESS_DIGEST_FORBIDDEN")
    if seam_record.get("optimization_candidate_ref"):
        reasons.append("OPTIMIZATION_CANDIDATE_REF_FORBIDDEN")
    if seam_record.get("candidate_ref"):
        reasons.append("CANDIDATE_REF_FORBIDDEN")
    if seam_record.get("parameter_config_delta") is not None:
        reasons.append("CANDIDATE_PARAMETER_DELTA_FORBIDDEN")

    if not verify_seam_record_digest_v1(seam_record):
        reasons.append("SEAM_DIGEST_INVALID")
    if seam_record.get("seam_status") != STATUS_BOUND:
        reasons.append("SEAM_STATUS_NOT_BOUND")
    if seam_record.get("seam_disposition") != SEAM_DISPOSITION:
        reasons.append("SEAM_DISPOSITION_INVALID")
    if seam_record.get("seam_owner") != SEAM_OWNER:
        reasons.append("SEAM_OWNER_INVALID")

    target_id = str(seam_record.get("productive_target_id") or "")
    target_ok, target_reason = validate_productive_target_id_v1(target_id)
    if not target_ok:
        reasons.append(target_reason)
    if target_id != PRODUCTIVE_TARGET_ID:
        reasons.append("PRODUCTIVE_TARGET_ID_MISMATCH")
    if seam_record.get("productive_target_version") != PRODUCTIVE_TARGET_VERSION:
        reasons.append("PRODUCTIVE_TARGET_VERSION_MISMATCH")
    if seam_record.get("policy_consumer_module") != POLICY_CONSUMER_MODULE:
        reasons.append("POLICY_CONSUMER_MISMATCH")
    if seam_record.get("enforcement_enabled") is True:
        reasons.append("ENFORCEMENT_FORBIDDEN")
    if seam_record.get("external_effect_authorized") is True:
        reasons.append("EXTERNAL_EFFECT_FORBIDDEN")
    runtime_applied = seam_record.get("runtime_applied") is True
    runtime_apply_authority = str(seam_record.get("runtime_apply_authority") or "")
    if runtime_applied and not is_f1_m9_scoped_runtime_apply_authority_v1(runtime_apply_authority):
        reasons.append("RUNTIME_APPLY_CLAIM_FORBIDDEN_ON_RECORD")
    if runtime_applied and not seam_record.get("owner_apply_authorization_record_digest"):
        reasons.append("OWNER_APPLY_AUTHORIZATION_DIGEST_MISSING_ON_SEAM")

    numeric = seam_record.get("numeric_max_age_seconds")
    authorized_numeric = seam_record.get("authorized_candidate_max_age_seconds")
    if not isinstance(numeric, (int, float)) or isinstance(numeric, bool):
        reasons.append("NUMERIC_MAX_AGE_INVALID")
    elif float(numeric) != float(authorized_numeric):
        reasons.append("NUMERIC_VALUE_INTERNAL_MISMATCH")

    if reasons:
        return _deny(reasons)

    return GovernedRuntimeSeamTransportResultV1(
        transport_status=STATUS_TRANSPORT_READY,
        reason_codes=("RUNTIME_SEAM_TRANSPORT_READY",),
        seam_for_consumer=seam_record,
    )


def optimization_can_direct_write_runtime_seam_v1() -> bool:
    return False
