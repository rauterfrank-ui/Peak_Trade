"""EG-I82-JOIN U-I82-R3 — dormant join-record primitive over the R1 contract.

Aggregates explicit per-plane contributions into a CrossLaneIdentityJoinV1.
Canonical join key is Package-N SHA256 only. No lane attachment, no persistence,
no runtime registration, no second identity semantics.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.experiments.cross_lane_identity_join_v1 import (
    CONTRACT_ID as JOIN_CONTRACT_ID,
    CONTRACT_VERSION,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    JOIN_PLANES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PLANE_VALUE_FIELDS,
    PlanePresence,
    RUNTIME_AUTHORITY_IMPACT,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinError,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
    validate_cross_lane_identity_join_v1,
)

CONTRACT_ID = "cross_lane_identity_join_record_v1"

_CONTRIBUTION_KEYS = frozenset({"plane", "presence", "join_key", "value"})
_FORBIDDEN_CONTRIBUTION_KEYS = frozenset(
    {
        "orders",
        "credentials",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
    }
)


class CrossLaneIdentityJoinRecordError(ValueError):
    """Fail-closed join-record primitive error."""


def _reject(message: str) -> None:
    raise CrossLaneIdentityJoinRecordError(message)


def _presence_value(raw: object) -> str:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        _reject("plane presence status is missing")
    if isinstance(raw, PlanePresence):
        return raw.value
    if not isinstance(raw, str):
        _reject("plane presence status is missing")
    if raw not in {PlanePresence.PRESENT.value, PlanePresence.ABSENT_DECLARED.value}:
        _reject(f"unknown plane presence status: {raw!r}")
    return raw


def _plane_name(raw: object) -> str:
    if not isinstance(raw, str) or not raw.strip():
        _reject("join contribution plane is missing")
    if raw not in JOIN_PLANES:
        _reject(f"unknown join plane rejected: {raw}")
    return raw


def _optional_str(raw: object, *, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        _reject(f"{field} must be a string when present")
    if not raw.strip() or raw != raw.strip():
        _reject(f"{field} is present but empty or whitespace-padded")
    return raw


@dataclass(frozen=True)
class JoinPlaneContributionV1:
    plane: str
    presence: str
    join_key: str | None
    value: str | None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> JoinPlaneContributionV1:
        if not isinstance(payload, Mapping):
            _reject("join contribution must be an object")
        forbidden = sorted(
            str(key) for key in payload.keys() if str(key) in _FORBIDDEN_CONTRIBUTION_KEYS
        )
        if forbidden:
            _reject(f"forbidden join contribution key: {forbidden[0]}")
        extra = sorted(str(key) for key in payload.keys() if str(key) not in _CONTRIBUTION_KEYS)
        if extra:
            _reject(f"unknown join contribution field: {extra[0]}")
        plane = _plane_name(payload.get("plane"))
        presence = _presence_value(payload.get("presence"))
        join_key = (
            _optional_str(payload.get("join_key"), field="join_key")
            if "join_key" in payload
            else None
        )
        value = _optional_str(payload.get("value"), field="value") if "value" in payload else None
        return cls(plane=plane, presence=presence, join_key=join_key, value=value)


def _normalize_contributions(
    contributions: Sequence[JoinPlaneContributionV1 | Mapping[str, Any]],
) -> list[JoinPlaneContributionV1]:
    if not isinstance(contributions, Sequence) or isinstance(contributions, (str, bytes)):
        _reject("join contributions must be a sequence")
    normalized: list[JoinPlaneContributionV1] = []
    for item in contributions:
        if isinstance(item, JoinPlaneContributionV1):
            normalized.append(item)
        elif isinstance(item, Mapping):
            normalized.append(JoinPlaneContributionV1.from_mapping(item))
        else:
            _reject("join contribution must be an object")
    return normalized


def _proven_package_n_id(
    *,
    package_n_identity_id: str | None,
    package_n_manifest: Mapping[str, Any] | None,
) -> str | None:
    manifest_id: str | None = None
    if package_n_manifest is not None:
        if not isinstance(package_n_manifest, Mapping):
            _reject("package_n_manifest must be an object")
        raw = package_n_manifest.get("experiment_identity_id")
        if not is_package_n_sha256_canonical_id(raw):
            _reject("package_n_manifest.experiment_identity_id must be Package-N SHA256")
        manifest_id = str(raw)
    if package_n_identity_id is not None:
        if not is_package_n_sha256_canonical_id(package_n_identity_id):
            _reject("package_n_identity_id must be Package-N SHA256")
        if manifest_id is not None and package_n_identity_id != manifest_id:
            _reject("conflicting Package-N SHA256 identities")
        return package_n_identity_id
    return manifest_id


def _require_join_key(join_key: str | None, *, plane: str) -> str:
    if join_key is None:
        _reject(f"PRESENT plane {plane} is missing Package-N SHA256 join_key")
    if not is_package_n_sha256_canonical_id(join_key):
        _reject("join_key must be a Package-N SHA256 canonical id")
    return join_key


def build_cross_lane_identity_join_record_v1(
    contributions: Sequence[JoinPlaneContributionV1 | Mapping[str, Any]],
    *,
    package_n_identity_id: str | None = None,
    package_n_manifest: Mapping[str, Any] | None = None,
    historical_provenance: Mapping[str, Any] | None = None,
) -> CrossLaneIdentityJoinV1:
    """Build a dormant R1 join record from explicit plane contributions. Does not mutate inputs."""
    if historical_provenance is not None and not isinstance(historical_provenance, Mapping):
        _reject("historical_provenance must be an object")
    source_contributions = _normalize_contributions(contributions)
    proven_id = _proven_package_n_id(
        package_n_identity_id=package_n_identity_id,
        package_n_manifest=package_n_manifest,
    )
    provenance_copy: dict[str, Any] = (
        copy.deepcopy(dict(historical_provenance)) if historical_provenance is not None else {}
    )

    by_plane: dict[str, JoinPlaneContributionV1] = {}
    for item in source_contributions:
        if item.plane in by_plane:
            _reject(f"duplicate plane contribution rejected: {item.plane}")
        by_plane[item.plane] = item

    missing = [plane for plane in JOIN_PLANES if plane not in by_plane]
    if missing:
        _reject(f"incomplete join record: missing plane {missing[0]}")

    agreed_join_key = proven_id
    plane_presence: dict[str, str] = {}
    values: dict[str, str | None] = {field: None for field in PLANE_VALUE_FIELDS.values()}

    for plane in JOIN_PLANES:
        item = by_plane[plane]
        plane_presence[plane] = item.presence
        if item.presence == PlanePresence.ABSENT_DECLARED.value:
            if item.join_key is not None or item.value is not None:
                _reject(
                    f"ABSENT_DECLARED plane {plane} must not carry join_key or value "
                    "(synthetic identity forbidden)"
                )
            continue
        join_key = _require_join_key(item.join_key, plane=plane)
        if item.value is None:
            _reject(f"PRESENT plane {plane} is missing value")
        if agreed_join_key is None:
            agreed_join_key = join_key
        elif join_key != agreed_join_key:
            _reject("conflicting Package-N SHA256 identities")
        if plane == "IDENTITY":
            if item.value != join_key:
                _reject("IDENTITY value must equal Package-N SHA256 join_key")
            if not is_package_n_sha256_canonical_id(item.value):
                _reject("IDENTITY value must be a Package-N SHA256 canonical id")
        values[PLANE_VALUE_FIELDS[plane]] = item.value

    present_planes = [
        plane for plane, status in plane_presence.items() if status == PlanePresence.PRESENT.value
    ]
    if present_planes and agreed_join_key is None:
        _reject("PRESENT contribution is missing Package-N SHA256 join_key")
    if present_planes and plane_presence["IDENTITY"] != PlanePresence.PRESENT.value:
        _reject("PRESENT planes require IDENTITY PRESENT with the same Package-N SHA256")
    if plane_presence["IDENTITY"] == PlanePresence.PRESENT.value and agreed_join_key is None:
        _reject("IDENTITY PRESENT requires Package-N SHA256 join_key")

    payload: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_id": JOIN_CONTRACT_ID,
        "plane_presence": plane_presence,
        "safety": {
            "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
            "evidence_does_not_authorize_runtime": True,
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "SECOND_EXECUTION_AUTHORITY_AUTHORIZED": SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
            "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS": (
                CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS
            ),
        },
    }
    if provenance_copy:
        payload["historical_provenance"] = provenance_copy
    for plane, field in PLANE_VALUE_FIELDS.items():
        if plane_presence[plane] == PlanePresence.PRESENT.value:
            payload[field] = values[field]

    try:
        return validate_cross_lane_identity_join_v1(payload)
    except CrossLaneIdentityJoinError as exc:
        raise CrossLaneIdentityJoinRecordError(
            f"R1 join contract rejected join record: {exc}"
        ) from exc


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "CrossLaneIdentityJoinRecordError",
    "JoinPlaneContributionV1",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "build_cross_lane_identity_join_record_v1",
]
