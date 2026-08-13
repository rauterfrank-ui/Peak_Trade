"""EG-I82-JOIN U-I82-R11 — dormant fail-closed cross-lane join verifier.

Proof surface only. Compares named-lane join records against Package-N SHA256.
Does not register I17/I52/I56/I61/I65 live contracts, does not activate
Cap 7.2 or src.execution, and does not persist, migrate, or backfill.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from src.experiments.cross_lane_identity_join_v1 import (
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

CONTRACT_ID = "eg_i82_join_verifier_v1"
EG_I82_CROSS_LANE_VERIFIER_REGISTERED = True

NAMED_JOIN_LANES: tuple[str, ...] = ("I16", "I17", "I52", "I56", "I61", "I65")
LANE_DORMANT_CONTRACT_IDS: Mapping[str, str] = MappingProxyType(
    {
        "I16": "i16_package_n_join_emission_v1",
        "I17": "i17_paper_shadow_join_attachment_v1",
        "I52": "i52_levelup_join_attachment_v1",
        "I56": "i56_ingress_join_attachment_v1",
        "I61": "live_session_eval_identity_envelope_v1",
        "I65": "i65_explorer_join_attachment_v1",
    }
)

_NONCANONICAL_IDENTITY_KEYS = frozenset(
    {
        "run_id",
        "experiment_id",
        "campaign_id",
        "session_id",
        "evidence_id",
        "evidence_ref",
        "alias",
        "legacy_alias_md5_12",
        "legacy_experiment_id",
        "package_n_sha256",
        "canonical_id",
        "canonical_identity_id",
        "identity_id",
        "ref_id",
        "content_sha256",
    }
)
_NON_IDENTITY_PLANES = tuple(plane for plane in JOIN_PLANES if plane != "IDENTITY")


class EgI82JoinVerifierError(ValueError):
    """Fail-closed EG-I82 cross-lane join verifier error."""


def _reject(message: str) -> None:
    raise EgI82JoinVerifierError(message)


def is_eg_i82_cross_lane_verifier_registered() -> bool:
    """True iff the dormant cross-lane verifier is registered and reachable."""
    return EG_I82_CROSS_LANE_VERIFIER_REGISTERED is True


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


def _snapshot_lane_payload(raw: object, *, lane: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: named lane {lane} is missing")
    if isinstance(raw, CrossLaneIdentityJoinV1):
        return raw.to_canonical_mapping()
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, Mapping)):
        if not raw:
            _reject(f"implicit absence rejected: named lane {lane} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: named lane {lane} has multiple Package-N assignments"
            )
        return _snapshot_lane_payload(raw[0], lane=lane)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: named lane {lane} is not an object")
    return copy.deepcopy(dict(raw))


def _reject_noncanonical_lane_payload(payload: Mapping[str, Any], *, lane: str) -> None:
    if "plane_presence" in payload:
        return
    substitutes = sorted(key for key in payload.keys() if str(key) in _NONCANONICAL_IDENTITY_KEYS)
    if substitutes:
        _reject(
            f"noncanonical ID substitution rejected: named lane {lane} uses {substitutes[0]} "
            "as Package-N identity"
        )
    _reject(f"implicit absence rejected: named lane {lane} has no declared plane_presence")


def _classify_r1_error(exc: CrossLaneIdentityJoinError, *, lane: str) -> None:
    message = str(exc)
    lowered = message.lower()
    if (
        "canonical package-n sha256 id missing" in lowered
        or "is required when" in lowered
        or "status is missing" in lowered
        or "missing required plane status" in lowered
    ):
        _reject(f"implicit absence rejected: named lane {lane}: {exc}")
    if (
        "uuid/run_id" in lowered
        or "md5 alias" in lowered
        or "not a package-n" in lowered
        or "extra identity claim" in lowered
    ):
        _reject(f"noncanonical ID substitution rejected: named lane {lane}: {exc}")
    if "conflicting" in lowered:
        _reject(f"conflicting identity rejected: named lane {lane}: {exc}")
    if "unknown" in lowered or "must be" in lowered or "malformed" in lowered:
        _reject(f"malformed plane data rejected: named lane {lane}: {exc}")
    _reject(f"malformed plane data rejected: named lane {lane}: {exc}")


def _validate_lane_record(payload: Mapping[str, Any], *, lane: str) -> CrossLaneIdentityJoinV1:
    _reject_noncanonical_lane_payload(payload, lane=lane)
    try:
        return validate_cross_lane_identity_join_v1(payload)
    except CrossLaneIdentityJoinError as exc:
        _classify_r1_error(exc, lane=lane)
        raise AssertionError("unreachable") from exc


def _plane_value(record: CrossLaneIdentityJoinV1, plane: str) -> str | None:
    return getattr(record, PLANE_VALUE_FIELDS[plane])


def _reject_cross_plane_substitution(records: Mapping[str, CrossLaneIdentityJoinV1]) -> None:
    for lane, record in records.items():
        identity = record.experiment_identity_id
        if identity is None:
            continue
        if not is_package_n_sha256_canonical_id(identity):
            _reject(f"noncanonical ID substitution rejected: named lane {lane}")
        for plane in _NON_IDENTITY_PLANES:
            other = _plane_value(record, plane)
            if other is not None and other == identity:
                _reject(
                    f"cross-plane substitution rejected: named lane {lane} IDENTITY equals {plane}"
                )


def _reject_cross_lane_substitution(records: Mapping[str, CrossLaneIdentityJoinV1]) -> None:
    for lane, record in records.items():
        identity = record.experiment_identity_id
        if identity is None:
            continue
        for other_lane, other_record in records.items():
            if other_lane == lane:
                continue
            for plane in _NON_IDENTITY_PLANES:
                other = _plane_value(other_record, plane)
                if other is not None and other == identity:
                    _reject(
                        "cross-lane substitution rejected: "
                        f"{lane} IDENTITY equals {other_lane} {plane}"
                    )


@dataclass(frozen=True)
class EgI82CrossLaneJoinVerificationV1:
    schema_version: str
    contract_version: str
    contract_id: str
    verifier_registered: bool
    package_n_sha256: str | None
    lane_identity_presence: Mapping[str, str]
    named_lanes: tuple[str, ...]
    safety: Mapping[str, Any]

    def to_canonical_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "contract_id": self.contract_id,
            "verifier_registered": self.verifier_registered,
            "package_n_sha256": self.package_n_sha256,
            "lane_identity_presence": {
                lane: self.lane_identity_presence[lane] for lane in NAMED_JOIN_LANES
            },
            "named_lanes": list(self.named_lanes),
            "safety": copy.deepcopy(dict(self.safety)),
        }


def _mapping_snapshot(raw: Mapping[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            snapshot[str(key)] = _mapping_snapshot(value)
        elif isinstance(value, list):
            snapshot[str(key)] = [
                _mapping_snapshot(item) if isinstance(item, Mapping) else copy.deepcopy(item)
                for item in value
            ]
        else:
            snapshot[str(key)] = copy.deepcopy(value)
    return snapshot


def verify_eg_i82_cross_lane_join_v1(
    lanes: Mapping[str, Any],
) -> EgI82CrossLaneJoinVerificationV1:
    """Verify join consistency across named lanes. Does not mutate inputs or persist."""
    if not isinstance(lanes, Mapping):
        _reject("malformed plane data rejected: lanes root must be an object")
    extra = sorted(str(key) for key in lanes.keys() if str(key) not in NAMED_JOIN_LANES)
    if extra:
        if extra[0] in _NONCANONICAL_IDENTITY_KEYS:
            _reject(f"noncanonical ID substitution rejected: context key {extra[0]}")
        _reject(f"malformed plane data rejected: unknown join lane {extra[0]}")

    missing = [lane for lane in NAMED_JOIN_LANES if lane not in lanes]
    if missing:
        _reject(f"implicit absence rejected: named lane {missing[0]} is missing")

    records: dict[str, CrossLaneIdentityJoinV1] = {}
    mapping_snapshots: dict[str, dict[str, Any]] = {}
    for lane in NAMED_JOIN_LANES:
        raw = lanes[lane]
        if isinstance(raw, Mapping) and not isinstance(raw, CrossLaneIdentityJoinV1):
            mapping_snapshots[lane] = _mapping_snapshot(raw)
        payload = _snapshot_lane_payload(raw, lane=lane)
        records[lane] = _validate_lane_record(payload, lane=lane)

    present_ids = [
        record.experiment_identity_id
        for record in records.values()
        if record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    ]
    if any(item is None for item in present_ids):
        _reject("implicit absence rejected: IDENTITY PRESENT without Package-N SHA256")
    _reject_cross_plane_substitution(records)
    _reject_cross_lane_substitution(records)
    distinct = {item for item in present_ids if item is not None}
    if len(distinct) > 1:
        _reject("conflicting identity rejected: Package-N SHA256 values disagree across lanes")
    agreed = next(iter(distinct)) if distinct else None
    if agreed is not None and not is_package_n_sha256_canonical_id(agreed):
        _reject("noncanonical ID substitution rejected: agreed identity is not Package-N SHA256")

    for lane, snap in mapping_snapshots.items():
        current = lanes[lane]
        if not isinstance(current, Mapping) or _mapping_snapshot(current) != snap:
            _reject("lanes input was mutated")

    return EgI82CrossLaneJoinVerificationV1(
        schema_version=CONTRACT_VERSION,
        contract_version=CONTRACT_VERSION,
        contract_id=CONTRACT_ID,
        verifier_registered=True,
        package_n_sha256=agreed,
        lane_identity_presence=MappingProxyType(
            {lane: records[lane].plane_presence["IDENTITY"] for lane in NAMED_JOIN_LANES}
        ),
        named_lanes=NAMED_JOIN_LANES,
        safety=_freeze_mapping(
            {
                "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
                "evidence_does_not_authorize_runtime": True,
                "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
                "SECOND_EXECUTION_AUTHORITY_AUTHORIZED": SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
                "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS": (
                    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS
                ),
            }
        ),
    )


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "EG_I82_CROSS_LANE_VERIFIER_REGISTERED",
    "EgI82CrossLaneJoinVerificationV1",
    "EgI82JoinVerifierError",
    "LANE_DORMANT_CONTRACT_IDS",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "NAMED_JOIN_LANES",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_eg_i82_cross_lane_verifier_registered",
    "verify_eg_i82_cross_lane_join_v1",
]
