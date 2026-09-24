"""F1/M9 Owner Apply Authorization record v1 (digest-sealed, separate from explicit auth)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping

F1_M9_SCOPE_PAIR_ID: Final[str] = "F1-M9-VOLATILITY-MAX-AGE-SECONDS"
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_owner_apply_authorization_record/v1"
RECORD_DOMAIN: Final[str] = "peak_trade.governance.f1_m9_owner_apply_authorization.v1"
DEFAULT_OWNER_APPLY_AUTHORIZATION_ID: Final[str] = "f1_m9_owner_apply_authorization/v1"

OWNER_APPLY_RECORD_FIELD_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "owner_apply_authorization_id",
    "authorizer_identity",
    "scoped_join_pair_id",
    "registry_digest",
    "ingress_digest",
    "binding_digest",
    "owner_authorization_record_digest",
    "authorization_id",
    "authorization_digest",
    "configuration_id",
    "configuration_digest",
    "candidate_parameter_value_digest",
    "productive_target_id",
    "productive_target_version",
    "productive_target_contract_digest",
    "not_before",
    "expires_at",
    "owner_apply_authorization_record_digest",
)


class OwnerApplyAuthorizationRecordError(ValueError):
    """Fail-closed Owner Apply record error."""


@dataclass(frozen=True, slots=True)
class OwnerApplyAuthorizationInputV1:
    owner_apply_authorization_record: Mapping[str, Any]
    owner_apply_authorization_record_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_apply_authorization_record": dict(self.owner_apply_authorization_record),
            "owner_apply_authorization_record_digest": self.owner_apply_authorization_record_digest,
        }


def parse_aware_utc_datetime_v1(raw: Any, *, field_name: str) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise OwnerApplyAuthorizationRecordError(f"{field_name}_MISSING")
    text = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise OwnerApplyAuthorizationRecordError(f"{field_name}_INVALID") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_aware_utc_datetime_v1(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_owner_apply_authorization_record_digest_v1(
    record_body: Mapping[str, Any],
) -> str:
    sealed = {
        key: record_body[key]
        for key in OWNER_APPLY_RECORD_FIELD_KEYS
        if key != "owner_apply_authorization_record_digest" and key in record_body
    }
    return compute_content_sha256(sealed)


def verify_owner_apply_authorization_record_digest_v1(record: Mapping[str, Any]) -> bool:
    stored = record.get("owner_apply_authorization_record_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    return compute_owner_apply_authorization_record_digest_v1(record) == stored


def build_owner_apply_authorization_record_body_v1(
    *,
    registry_digest: str,
    ingress_digest: str,
    binding_digest: str,
    owner_authorization_record_digest: str,
    authorization_id: str,
    authorization_digest: str,
    configuration_id: str,
    configuration_digest: str,
    candidate_parameter_value_digest: str,
    productive_target_id: str,
    productive_target_version: str,
    productive_target_contract_digest: str,
    not_before: str,
    expires_at: str,
    owner_apply_authorization_id: str = DEFAULT_OWNER_APPLY_AUTHORIZATION_ID,
    authorizer_identity: str = "OWNER_F1_M9_PRODUCTIVE_APPLY",
    scoped_join_pair_id: str = F1_M9_SCOPE_PAIR_ID,
) -> MappingProxyType[str, Any]:
    body = {
        "schema_version": SCHEMA_VERSION,
        "owner_apply_authorization_id": owner_apply_authorization_id,
        "authorizer_identity": authorizer_identity,
        "scoped_join_pair_id": scoped_join_pair_id,
        "registry_digest": registry_digest,
        "ingress_digest": ingress_digest,
        "binding_digest": binding_digest,
        "owner_authorization_record_digest": owner_authorization_record_digest,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "configuration_id": configuration_id,
        "configuration_digest": configuration_digest,
        "candidate_parameter_value_digest": candidate_parameter_value_digest,
        "productive_target_id": productive_target_id,
        "productive_target_version": productive_target_version,
        "productive_target_contract_digest": productive_target_contract_digest,
        "not_before": not_before,
        "expires_at": expires_at,
    }
    missing = [
        key
        for key in OWNER_APPLY_RECORD_FIELD_KEYS
        if key != "owner_apply_authorization_record_digest" and key not in body
    ]
    if missing:
        raise OwnerApplyAuthorizationRecordError(f"RECORD_BODY_INCOMPLETE:{','.join(missing)}")
    digest = compute_owner_apply_authorization_record_digest_v1(body)
    body["owner_apply_authorization_record_digest"] = digest
    return MappingProxyType(body)


def build_owner_apply_authorization_input_v1(
    *,
    registry_digest: str,
    ingress_digest: str,
    binding_digest: str,
    owner_authorization_record_digest: str,
    authorization_id: str,
    authorization_digest: str,
    configuration_id: str,
    configuration_digest: str,
    candidate_parameter_value_digest: str,
    productive_target_id: str,
    productive_target_version: str,
    productive_target_contract_digest: str,
    not_before: str,
    expires_at: str,
) -> OwnerApplyAuthorizationInputV1:
    record = dict(
        build_owner_apply_authorization_record_body_v1(
            registry_digest=registry_digest,
            ingress_digest=ingress_digest,
            binding_digest=binding_digest,
            owner_authorization_record_digest=owner_authorization_record_digest,
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            configuration_id=configuration_id,
            configuration_digest=configuration_digest,
            candidate_parameter_value_digest=candidate_parameter_value_digest,
            productive_target_id=productive_target_id,
            productive_target_version=productive_target_version,
            productive_target_contract_digest=productive_target_contract_digest,
            not_before=not_before,
            expires_at=expires_at,
        )
    )
    digest = str(record["owner_apply_authorization_record_digest"])
    return OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=digest,
    )


__all__ = [
    "DEFAULT_OWNER_APPLY_AUTHORIZATION_ID",
    "OWNER_APPLY_RECORD_FIELD_KEYS",
    "OwnerApplyAuthorizationInputV1",
    "OwnerApplyAuthorizationRecordError",
    "RECORD_DOMAIN",
    "SCHEMA_VERSION",
    "build_owner_apply_authorization_input_v1",
    "build_owner_apply_authorization_record_body_v1",
    "compute_owner_apply_authorization_record_digest_v1",
    "format_aware_utc_datetime_v1",
    "parse_aware_utc_datetime_v1",
    "verify_owner_apply_authorization_record_digest_v1",
]
