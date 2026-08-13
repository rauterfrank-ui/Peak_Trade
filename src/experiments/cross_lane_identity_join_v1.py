"""EG-I82-JOIN U-I82-R1 — dormant fail-closed cross-lane identity join contract.

Canonical join identity is Package-N SHA256 (64-char lowercase hex).
This module defines types and validation only. It does not attach lanes,
migrate historical records, activate runtime, or cut over emitters.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    is_valid_sha256_hex,
    is_valid_uuid,
)

CONTRACT_ID = "cross_lane_identity_join_v1"
CONTRACT_VERSION = SCHEMA_VERSION_V1
RUNTIME_AUTHORITY_IMPACT = "NONE"
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
SECOND_EXECUTION_AUTHORITY_AUTHORIZED = False
CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS = 1

_MD5_12_RE = re.compile(r"^[0-9a-f]{12}$", re.IGNORECASE)
_MD5_32_RE = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)

_PLANE_VALUE_FIELDS: dict[str, str] = {
    "IDENTITY": "experiment_identity_id",
    "ALIAS": "legacy_alias_md5_12",
    "RUN": "run_id",
    "CAMPAIGN": "campaign_id",
    "SESSION": "session_id",
    "EVIDENCE": "evidence_ref",
    "CONTENT_HASH": "content_sha256",
}

JOIN_PLANES: tuple[str, ...] = tuple(_PLANE_VALUE_FIELDS.keys())
PLANE_VALUE_FIELDS: Mapping[str, str] = MappingProxyType(dict(_PLANE_VALUE_FIELDS))

_KNOWN_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "contract_version",
        "contract_id",
        "plane_presence",
        "historical_provenance",
        "safety",
        *_PLANE_VALUE_FIELDS.values(),
    }
)

_FORBIDDEN_IDENTITY_CLAIM_KEYS = frozenset(
    {
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
    }
)

_IDENTITY_SUBSTITUTION_PLANES = ("RUN", "SESSION", "CAMPAIGN", "ALIAS")


class PlanePresence(str, Enum):
    PRESENT = "PRESENT"
    ABSENT_DECLARED = "ABSENT_DECLARED"


class JoinPlane(str, Enum):
    IDENTITY = "IDENTITY"
    ALIAS = "ALIAS"
    RUN = "RUN"
    CAMPAIGN = "CAMPAIGN"
    SESSION = "SESSION"
    EVIDENCE = "EVIDENCE"
    CONTENT_HASH = "CONTENT_HASH"


class CrossLaneIdentityJoinError(ValueError):
    """Fail-closed cross-lane identity join contract error."""


def is_package_n_sha256_canonical_id(value: object) -> bool:
    """True iff value is a Package-N canonical identity (64-char lowercase sha256 hex)."""
    if not isinstance(value, str):
        return False
    if is_valid_uuid(value):
        return False
    if _MD5_12_RE.fullmatch(value) is not None:
        return False
    if _MD5_32_RE.fullmatch(value) is not None:
        return False
    return is_valid_sha256_hex(value)


def _reject(message: str) -> None:
    raise CrossLaneIdentityJoinError(message)


def _is_absent_value(value: object) -> bool:
    return value is None


def _require_non_empty_str(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"{field} must be a non-empty string without surrounding whitespace")
    return value


def _freeze_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, Mapping):
            frozen[str(key)] = _freeze_mapping(value)
        elif isinstance(value, list):
            frozen[str(key)] = tuple(
                _freeze_mapping(item) if isinstance(item, Mapping) else copy.deepcopy(item)
                for item in value
            )
        else:
            frozen[str(key)] = copy.deepcopy(value)
    return MappingProxyType(frozen)


def read_historical_provenance(
    payload: Mapping[str, Any] | CrossLaneIdentityJoinV1,
) -> Mapping[str, Any]:
    """Return a read-only copy of historical provenance. Never rewrites source values."""
    if isinstance(payload, CrossLaneIdentityJoinV1):
        return payload.historical_provenance
    if not isinstance(payload, Mapping):
        _reject("historical provenance source must be an object")
    raw = payload.get("historical_provenance", {})
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        _reject("historical_provenance must be an object")
    return _freeze_mapping(raw)


def _validate_plane_presence(raw: object) -> dict[str, PlanePresence]:
    if not isinstance(raw, Mapping):
        _reject("plane_presence is required and must be an object")
    unknown = sorted(str(key) for key in raw.keys() if str(key) not in _PLANE_VALUE_FIELDS)
    if unknown:
        _reject(f"unknown join plane rejected: {unknown[0]}")
    missing = [plane for plane in JOIN_PLANES if plane not in raw]
    if missing:
        _reject(f"plane_presence missing required plane status: {missing[0]}")
    parsed: dict[str, PlanePresence] = {}
    for plane in JOIN_PLANES:
        status = raw[plane]
        if status is None or (isinstance(status, str) and not status.strip()):
            _reject(f"plane_presence.{plane} status is missing")
        if not isinstance(status, str):
            _reject(f"plane_presence.{plane} status is missing")
        if status not in {PlanePresence.PRESENT.value, PlanePresence.ABSENT_DECLARED.value}:
            _reject(f"plane_presence.{plane} must be PRESENT or ABSENT_DECLARED, got {status!r}")
        parsed[plane] = PlanePresence(status)
    return parsed


def _value_for_plane(payload: Mapping[str, Any], plane: str) -> object:
    return payload.get(_PLANE_VALUE_FIELDS[plane])


def _validate_alias(value: str) -> None:
    if _MD5_12_RE.fullmatch(value) is None:
        _reject("legacy_alias_md5_12 must be 12 hex chars when ALIAS is PRESENT")


def _validate_content_hash(value: str) -> None:
    if not is_valid_sha256_hex(value):
        _reject("content_sha256 must be 64-char lowercase sha256 hex when CONTENT_HASH is PRESENT")


def _reject_identity_substitutes(identity_id: str) -> None:
    if is_valid_uuid(identity_id):
        _reject("UUID/run_id is not a Package-N SHA256 canonical id")
    if (
        _MD5_12_RE.fullmatch(identity_id) is not None
        or _MD5_32_RE.fullmatch(identity_id) is not None
    ):
        _reject("MD5 alias is not a Package-N SHA256 canonical id")
    if not is_package_n_sha256_canonical_id(identity_id):
        _reject("experiment_identity_id must be a Package-N SHA256 canonical id")


def _reject_conflicting_identities(
    payload: Mapping[str, Any],
    *,
    identity_id: str | None,
    plane_presence: Mapping[str, PlanePresence],
) -> None:
    for key in _FORBIDDEN_IDENTITY_CLAIM_KEYS:
        if key in payload:
            other = payload[key]
            if identity_id is None or other != identity_id:
                _reject(f"conflicting identities rejected: extra identity claim {key}")
            _reject(f"conflicting identities rejected: extra identity claim {key}")
    if identity_id is None:
        return
    for plane in _IDENTITY_SUBSTITUTION_PLANES:
        if plane_presence[plane] is not PlanePresence.PRESENT:
            continue
        other = _value_for_plane(payload, plane)
        if other == identity_id:
            _reject(
                f"conflicting identities rejected: IDENTITY equals {plane} value "
                f"({_PLANE_VALUE_FIELDS[plane]})"
            )


def _validate_safety(raw: object) -> Mapping[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        _reject("safety must be an object")
    if (
        "runtime_authority_impact" in raw
        and raw.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT
    ):
        _reject("safety.runtime_authority_impact must be NONE")
    if (
        "evidence_does_not_authorize_runtime" in raw
        and raw.get("evidence_does_not_authorize_runtime") is not True
    ):
        _reject("safety.evidence_does_not_authorize_runtime must be true")
    if raw.get("MULTI_FUTURE_RUNTIME_AUTHORIZED") is True:
        _reject("MULTI_FUTURE_RUNTIME_AUTHORIZED must remain false")
    if raw.get("SECOND_EXECUTION_AUTHORITY_AUTHORIZED") is True:
        _reject("SECOND_EXECUTION_AUTHORITY_AUTHORIZED must remain false")
    unknown = sorted(
        str(key)
        for key in raw.keys()
        if str(key)
        not in {
            "runtime_authority_impact",
            "evidence_does_not_authorize_runtime",
            "MULTI_FUTURE_RUNTIME_AUTHORIZED",
            "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
            "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
        }
    )
    if unknown:
        _reject(f"unknown safety field rejected: {unknown[0]}")
    if (
        "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS" in raw
        and raw.get("CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS")
        != CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS
    ):
        _reject("CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS must remain 1")
    return _freeze_mapping(raw)


@dataclass(frozen=True)
class CrossLaneIdentityJoinV1:
    schema_version: str
    contract_version: str
    contract_id: str
    plane_presence: Mapping[str, str]
    experiment_identity_id: str | None
    legacy_alias_md5_12: str | None
    run_id: str | None
    campaign_id: str | None
    session_id: str | None
    evidence_ref: str | None
    content_sha256: str | None
    historical_provenance: Mapping[str, Any]
    safety: Mapping[str, Any] | None

    def to_canonical_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "contract_id": self.contract_id,
            "plane_presence": {plane: self.plane_presence[plane] for plane in JOIN_PLANES},
        }
        for plane, field in _PLANE_VALUE_FIELDS.items():
            if self.plane_presence[plane] == PlanePresence.PRESENT.value:
                payload[field] = getattr(self, field)
        if self.historical_provenance:
            payload["historical_provenance"] = copy.deepcopy(dict(self.historical_provenance))
        if self.safety is not None:
            payload["safety"] = copy.deepcopy(dict(self.safety))
        return payload


def validate_cross_lane_identity_join_v1(payload: Mapping[str, Any]) -> CrossLaneIdentityJoinV1:
    """Validate a dormant join contract record. Does not mutate payload or historical values."""
    if not isinstance(payload, Mapping):
        _reject("join record root must be an object")

    for key in _FORBIDDEN_IDENTITY_CLAIM_KEYS:
        if key in payload:
            _reject(f"conflicting identities rejected: extra identity claim {key}")

    extra = sorted(str(key) for key in payload.keys() if str(key) not in _KNOWN_TOP_LEVEL_KEYS)
    if extra:
        _reject(f"unknown join field rejected: {extra[0]}")

    schema_version = payload.get("schema_version")
    if schema_version != CONTRACT_VERSION:
        _reject("schema_version must equal 1.0")
    contract_version = payload.get("contract_version")
    if contract_version != CONTRACT_VERSION:
        _reject("contract_version must equal 1.0")
    contract_id = payload.get("contract_id")
    if contract_id != CONTRACT_ID:
        _reject("contract_id must equal cross_lane_identity_join_v1")

    plane_presence = _validate_plane_presence(payload.get("plane_presence"))
    values: dict[str, str | None] = {field: None for field in _PLANE_VALUE_FIELDS.values()}

    for plane, field in _PLANE_VALUE_FIELDS.items():
        status = plane_presence[plane]
        raw_value = payload.get(field)
        if status is PlanePresence.ABSENT_DECLARED:
            if field in payload and not _is_absent_value(raw_value):
                _reject(f"{field} must be absent or null when {plane} is ABSENT_DECLARED")
            continue
        if field not in payload or _is_absent_value(raw_value):
            if plane == "IDENTITY":
                _reject("canonical Package-N SHA256 id missing while IDENTITY is PRESENT")
            _reject(f"{field} is required when {plane} is PRESENT")
        text = _require_non_empty_str(raw_value, field=field)
        if plane == "IDENTITY":
            _reject_identity_substitutes(text)
        elif plane == "ALIAS":
            _validate_alias(text)
        elif plane == "CONTENT_HASH":
            _validate_content_hash(text)
        values[field] = text

    identity_id = values["experiment_identity_id"]
    _reject_conflicting_identities(payload, identity_id=identity_id, plane_presence=plane_presence)

    historical_provenance = read_historical_provenance(payload)
    if (
        plane_presence["IDENTITY"] is PlanePresence.PRESENT
        and identity_id is not None
        and "experiment_identity_id" in historical_provenance
        and historical_provenance["experiment_identity_id"] != identity_id
    ):
        _reject("conflicting identities rejected: historical provenance canonical id mismatch")

    safety = _validate_safety(payload.get("safety")) if "safety" in payload else None

    return CrossLaneIdentityJoinV1(
        schema_version=CONTRACT_VERSION,
        contract_version=CONTRACT_VERSION,
        contract_id=CONTRACT_ID,
        plane_presence=MappingProxyType(
            {plane: plane_presence[plane].value for plane in JOIN_PLANES}
        ),
        experiment_identity_id=values["experiment_identity_id"],
        legacy_alias_md5_12=values["legacy_alias_md5_12"],
        run_id=values["run_id"],
        campaign_id=values["campaign_id"],
        session_id=values["session_id"],
        evidence_ref=values["evidence_ref"],
        content_sha256=values["content_sha256"],
        historical_provenance=historical_provenance,
        safety=safety,
    )


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "CrossLaneIdentityJoinError",
    "CrossLaneIdentityJoinV1",
    "JOIN_PLANES",
    "JoinPlane",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "PLANE_VALUE_FIELDS",
    "PlanePresence",
    "RUNTIME_AUTHORITY_IMPACT",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_package_n_sha256_canonical_id",
    "read_historical_provenance",
    "validate_cross_lane_identity_join_v1",
]
