"""F1/M9 Owner Threshold Value Authorization record v1 (digest-sealed, separate from Apply)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.f1_m9_owner_apply_authorization_record_v1 import F1_M9_SCOPE_PAIR_ID
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_owner_threshold_value_authorization_record/v1"
RECORD_DOMAIN: Final[str] = "peak_trade.governance.f1_m9_owner_threshold_value_authorization.v1"
DEFAULT_OWNER_THRESHOLD_AUTHORIZATION_ID: Final[str] = (
    "f1_m9_owner_threshold_value_authorization/v1"
)

OWNER_THRESHOLD_RECORD_FIELD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_threshold_authorization_id",
    "authorizer_identity",
    "scoped_join_pair_id",
    "registry_digest",
    "ingress_digest",
    "per_ingress_binding_digest",
    "owner_authorization_record_digest",
    "authorization_id",
    "authorization_digest",
    "configuration_id",
    "configuration_digest",
    "candidate_parameter_value_digest",
    "productive_target_id",
    "productive_target_version",
    "productive_target_contract_digest",
    "ratified_threshold_capability_id",
    "ratified_threshold_capability_version",
    "owner_apply_authorization_record_digest",
    "productive_apply_authorization_digest",
    "threshold_numeric_max_age_seconds",
    "not_before",
    "expires_at",
    "threshold_value_authorization_record_digest",
)


class OwnerThresholdValueAuthorizationRecordError(ValueError):
    """Fail-closed Owner Threshold Value record error."""


@dataclass(frozen=True, slots=True)
class OwnerThresholdValueAuthorizationInputV1:
    owner_threshold_authorization_record: Mapping[str, Any]
    owner_threshold_authorization_record_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_threshold_authorization_record": dict(self.owner_threshold_authorization_record),
            "owner_threshold_authorization_record_digest": (
                self.owner_threshold_authorization_record_digest
            ),
        }


def parse_aware_utc_datetime_v1(raw: Any, *, field_name: str) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise OwnerThresholdValueAuthorizationRecordError(f"{field_name}_MISSING")
    text = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise OwnerThresholdValueAuthorizationRecordError(f"{field_name}_INVALID") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_aware_utc_datetime_v1(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_owner_threshold_value_authorization_record_digest_v1(
    record_body: Mapping[str, Any],
) -> str:
    sealed = {
        key: record_body[key]
        for key in OWNER_THRESHOLD_RECORD_FIELD_KEYS
        if key != "threshold_value_authorization_record_digest" and key in record_body
    }
    return compute_content_sha256(sealed)


def verify_owner_threshold_value_authorization_record_digest_v1(
    record: Mapping[str, Any],
) -> bool:
    stored = record.get("threshold_value_authorization_record_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    return compute_owner_threshold_value_authorization_record_digest_v1(record) == stored


def build_owner_threshold_value_authorization_record_body_v1(
    *,
    registry_digest: str,
    ingress_digest: str,
    per_ingress_binding_digest: str,
    owner_authorization_record_digest: str,
    authorization_id: str,
    authorization_digest: str,
    configuration_id: str,
    configuration_digest: str,
    candidate_parameter_value_digest: str,
    productive_target_id: str,
    productive_target_version: str,
    productive_target_contract_digest: str,
    ratified_threshold_capability_id: str,
    ratified_threshold_capability_version: str,
    owner_apply_authorization_record_digest: str,
    productive_apply_authorization_digest: str,
    threshold_numeric_max_age_seconds: float,
    not_before: str,
    expires_at: str,
    owner_threshold_authorization_id: str = DEFAULT_OWNER_THRESHOLD_AUTHORIZATION_ID,
    authorizer_identity: str = "OWNER_F1_M9_THRESHOLD_VALUE_AUTHORIZATION",
    scoped_join_pair_id: str = F1_M9_SCOPE_PAIR_ID,
) -> MappingProxyType[str, Any]:
    body = {
        "schema_version": SCHEMA_VERSION,
        "owner_threshold_authorization_id": owner_threshold_authorization_id,
        "authorizer_identity": authorizer_identity,
        "scoped_join_pair_id": scoped_join_pair_id,
        "registry_digest": registry_digest,
        "ingress_digest": ingress_digest,
        "per_ingress_binding_digest": per_ingress_binding_digest,
        "owner_authorization_record_digest": owner_authorization_record_digest,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "configuration_id": configuration_id,
        "configuration_digest": configuration_digest,
        "candidate_parameter_value_digest": candidate_parameter_value_digest,
        "productive_target_id": productive_target_id,
        "productive_target_version": productive_target_version,
        "productive_target_contract_digest": productive_target_contract_digest,
        "ratified_threshold_capability_id": ratified_threshold_capability_id,
        "ratified_threshold_capability_version": ratified_threshold_capability_version,
        "owner_apply_authorization_record_digest": owner_apply_authorization_record_digest,
        "productive_apply_authorization_digest": productive_apply_authorization_digest,
        "threshold_numeric_max_age_seconds": float(threshold_numeric_max_age_seconds),
        "not_before": not_before,
        "expires_at": expires_at,
    }
    missing = [
        key
        for key in OWNER_THRESHOLD_RECORD_FIELD_KEYS
        if key != "threshold_value_authorization_record_digest" and key not in body
    ]
    if missing:
        raise OwnerThresholdValueAuthorizationRecordError(
            f"RECORD_BODY_INCOMPLETE:{','.join(missing)}"
        )
    if productive_apply_authorization_digest != owner_apply_authorization_record_digest:
        raise OwnerThresholdValueAuthorizationRecordError(
            "PRODUCTIVE_APPLY_DIGEST_MUST_MATCH_OWNER_APPLY_DIGEST"
        )
    digest = compute_owner_threshold_value_authorization_record_digest_v1(body)
    body["threshold_value_authorization_record_digest"] = digest
    return MappingProxyType(body)


def build_owner_threshold_value_authorization_input_v1(
    *,
    registry_digest: str,
    ingress_digest: str,
    per_ingress_binding_digest: str,
    owner_authorization_record_digest: str,
    authorization_id: str,
    authorization_digest: str,
    configuration_id: str,
    configuration_digest: str,
    candidate_parameter_value_digest: str,
    productive_target_id: str,
    productive_target_version: str,
    productive_target_contract_digest: str,
    ratified_threshold_capability_id: str,
    ratified_threshold_capability_version: str,
    owner_apply_authorization_record_digest: str,
    productive_apply_authorization_digest: str,
    threshold_numeric_max_age_seconds: float,
    not_before: str,
    expires_at: str,
) -> OwnerThresholdValueAuthorizationInputV1:
    record = dict(
        build_owner_threshold_value_authorization_record_body_v1(
            registry_digest=registry_digest,
            ingress_digest=ingress_digest,
            per_ingress_binding_digest=per_ingress_binding_digest,
            owner_authorization_record_digest=owner_authorization_record_digest,
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            configuration_id=configuration_id,
            configuration_digest=configuration_digest,
            candidate_parameter_value_digest=candidate_parameter_value_digest,
            productive_target_id=productive_target_id,
            productive_target_version=productive_target_version,
            productive_target_contract_digest=productive_target_contract_digest,
            ratified_threshold_capability_id=ratified_threshold_capability_id,
            ratified_threshold_capability_version=ratified_threshold_capability_version,
            owner_apply_authorization_record_digest=owner_apply_authorization_record_digest,
            productive_apply_authorization_digest=productive_apply_authorization_digest,
            threshold_numeric_max_age_seconds=threshold_numeric_max_age_seconds,
            not_before=not_before,
            expires_at=expires_at,
        )
    )
    digest = str(record["threshold_value_authorization_record_digest"])
    return OwnerThresholdValueAuthorizationInputV1(
        owner_threshold_authorization_record=record,
        owner_threshold_authorization_record_digest=digest,
    )


__all__ = [
    "DEFAULT_OWNER_THRESHOLD_AUTHORIZATION_ID",
    "OWNER_THRESHOLD_RECORD_FIELD_KEYS",
    "OwnerThresholdValueAuthorizationInputV1",
    "OwnerThresholdValueAuthorizationRecordError",
    "RECORD_DOMAIN",
    "SCHEMA_VERSION",
    "build_owner_threshold_value_authorization_input_v1",
    "build_owner_threshold_value_authorization_record_body_v1",
    "compute_owner_threshold_value_authorization_record_digest_v1",
    "format_aware_utc_datetime_v1",
    "parse_aware_utc_datetime_v1",
    "verify_owner_threshold_value_authorization_record_digest_v1",
]
