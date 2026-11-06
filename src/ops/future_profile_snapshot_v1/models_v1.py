"""Versioned DTOs for B07 Future Profile Snapshot V1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.future_profile_snapshot_v1.constants_v1 import (
    AUTHORITY_ELIGIBILITY_SAFETY,
    AUTHORITY_PROFILE_ONLY,
    AUTHORITY_RANKING_INPUT,
    AUTHORITY_UNCLASSIFIED,
    AVAILABLE,
    CAPABILITY_ID,
    CALL_GRAPH,
    FIELD_AUTHORITY_CLASSES,
    FIELD_AVAILABILITY_STATES,
    MISSING,
    PRODUCER_VERSION,
    PROFILE_VERSION,
    SCHEMA_VERSION,
)


class FutureProfileSnapshotError(ValueError):
    """Fail-closed profile snapshot contract error."""


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FutureProfileFieldV1:
    """One auditable observed field, never a new decision authority."""

    group: str
    field_id: str
    authority_class: str
    availability_state: str
    value: Optional[Any]
    source: str
    canonical_producer: str
    unit_or_semantics: str
    observed_at_event_time: str
    captured_at: str
    provenance_ref: Mapping[str, Any] = field(default_factory=dict)
    missing_reason: str = ""
    valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_class": self.authority_class,
            "availability_state": self.availability_state,
            "canonical_producer": self.canonical_producer,
            "captured_at": self.captured_at,
            "field_id": self.field_id,
            "group": self.group,
            "missing_reason": self.missing_reason,
            "observed_at_event_time": self.observed_at_event_time,
            "provenance_ref": dict(sorted(self.provenance_ref.items())),
            "source": self.source,
            "unit_or_semantics": self.unit_or_semantics,
            "valid": bool(self.valid),
            "value": self.value,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "FutureProfileFieldV1":
        return FutureProfileFieldV1(
            group=str(payload["group"]),
            field_id=str(payload["field_id"]),
            authority_class=str(payload["authority_class"]),
            availability_state=str(payload["availability_state"]),
            value=payload.get("value"),
            source=str(payload["source"]),
            canonical_producer=str(payload["canonical_producer"]),
            unit_or_semantics=str(payload["unit_or_semantics"]),
            observed_at_event_time=str(payload["observed_at_event_time"]),
            captured_at=str(payload["captured_at"]),
            provenance_ref=dict(payload.get("provenance_ref") or {}),
            missing_reason=str(payload.get("missing_reason") or ""),
            valid=bool(payload.get("valid", True)),
        )


@dataclass(frozen=True)
class FutureProfileInstrumentSnapshotV1:
    canonical_instrument_id: str
    venue_native_id: str
    profile_state: str
    fields: tuple[FutureProfileFieldV1, ...]
    profile_field_count: int
    profile_only_field_count: int
    unclassified_field_count: int
    ranking_input_field_count: int
    eligibility_safety_field_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "eligibility_safety_field_count": int(self.eligibility_safety_field_count),
            "fields": [field.to_dict() for field in self.fields],
            "profile_field_count": int(self.profile_field_count),
            "profile_only_field_count": int(self.profile_only_field_count),
            "profile_state": self.profile_state,
            "ranking_input_field_count": int(self.ranking_input_field_count),
            "unclassified_field_count": int(self.unclassified_field_count),
            "venue_native_id": self.venue_native_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "FutureProfileInstrumentSnapshotV1":
        fields = tuple(FutureProfileFieldV1.from_dict(row) for row in (payload.get("fields") or ()))
        return FutureProfileInstrumentSnapshotV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_native_id=str(payload["venue_native_id"]),
            profile_state=str(payload["profile_state"]),
            fields=fields,
            profile_field_count=int(payload["profile_field_count"]),
            profile_only_field_count=int(payload["profile_only_field_count"]),
            unclassified_field_count=int(payload["unclassified_field_count"]),
            ranking_input_field_count=int(payload["ranking_input_field_count"]),
            eligibility_safety_field_count=int(payload["eligibility_safety_field_count"]),
        )


@dataclass(frozen=True)
class FutureProfileSnapshotV1:
    schema_version: str
    capability_id: str
    producer_version: str
    profile_version: str
    profile_snapshot_id: str
    repository_sha: str
    profile_event_time: str
    produced_at_wall_time: str
    source_references: Mapping[str, Any]
    instruments: tuple[FutureProfileInstrumentSnapshotV1, ...]
    selected_instrument_reference: Mapping[str, Any] = field(default_factory=dict)
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = CALL_GRAPH
    integrity_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": dict(sorted(self.authority.items())),
            "call_graph": list(self.call_graph),
            "capability_id": self.capability_id,
            "integrity_digest": self.integrity_digest,
            "instruments": [row.to_dict() for row in self.instruments],
            "producer_version": self.producer_version,
            "produced_at_wall_time": self.produced_at_wall_time,
            "profile_event_time": self.profile_event_time,
            "profile_snapshot_id": self.profile_snapshot_id,
            "profile_version": self.profile_version,
            "repository_sha": self.repository_sha,
            "schema_version": self.schema_version,
            "selected_instrument_reference": dict(
                sorted(self.selected_instrument_reference.items())
            ),
            "source_references": dict(sorted(self.source_references.items())),
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        payload.pop("produced_at_wall_time", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_integrity_digest(self) -> "FutureProfileSnapshotV1":
        return FutureProfileSnapshotV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            profile_version=self.profile_version,
            profile_snapshot_id=self.profile_snapshot_id,
            repository_sha=self.repository_sha,
            profile_event_time=self.profile_event_time,
            produced_at_wall_time=self.produced_at_wall_time,
            source_references=dict(self.source_references),
            instruments=self.instruments,
            selected_instrument_reference=dict(self.selected_instrument_reference),
            authority=dict(self.authority),
            call_graph=self.call_graph,
            integrity_digest=self.compute_integrity_digest(),
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "FutureProfileSnapshotV1":
        return FutureProfileSnapshotV1(
            schema_version=str(payload["schema_version"]),
            capability_id=str(payload["capability_id"]),
            producer_version=str(payload["producer_version"]),
            profile_version=str(payload["profile_version"]),
            profile_snapshot_id=str(payload["profile_snapshot_id"]),
            repository_sha=str(payload["repository_sha"]),
            profile_event_time=str(payload["profile_event_time"]),
            produced_at_wall_time=str(payload["produced_at_wall_time"]),
            source_references=dict(payload.get("source_references") or {}),
            instruments=tuple(
                FutureProfileInstrumentSnapshotV1.from_dict(row)
                for row in (payload.get("instruments") or ())
            ),
            selected_instrument_reference=dict(payload.get("selected_instrument_reference") or {}),
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            integrity_digest=str(payload.get("integrity_digest") or ""),
        )


def authority_block_v1() -> dict[str, Any]:
    return {
        "AUTHORITY_EFFECT": "OBSERVABILITY_ONLY",
        "B07_IMPLEMENTED": True,
        "BINDING_EFFECT": False,
        "CANONICAL_FEATURE_RECOMPUTATION_INTRODUCED": False,
        "CAP23_SOLE_SELECTION_OWNER": True,
        "CROSS_UNIVERSE_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY_ADDED": False,
        "LIVE_EXTERNAL_EFFECT_AUTHORIZED": False,
        "MAX_POSITIONS_EFFECTIVE": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "PROFILE_CAN_BIND": False,
        "PROFILE_CAN_RERANK": False,
        "PROFILE_CAN_SELECT": False,
        "PROFILE_ONLY_AFFECTS_RANKING": False,
        "RANKING_AUTHORITY_ADDED": False,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
        "SELECTION_AUTHORITY_CREATED": False,
        "SELECTION_EFFECT": False,
    }


def compute_profile_snapshot_id_v1(
    *,
    repository_sha: str,
    source_references: Mapping[str, Any],
    instrument_ids: tuple[str, ...],
) -> str:
    material = {
        "capability_id": CAPABILITY_ID,
        "instrument_ids": list(instrument_ids),
        "profile_version": PROFILE_VERSION,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "schema_version": SCHEMA_VERSION,
        "source_references": dict(sorted(source_references.items())),
    }
    return f"fps_{sha256_hex(canonical_json_dumps(material))[:24]}"


def validate_future_profile_snapshot_v1(snapshot: FutureProfileSnapshotV1) -> None:
    if snapshot.schema_version != SCHEMA_VERSION:
        raise FutureProfileSnapshotError("SCHEMA_VERSION_MISMATCH")
    if snapshot.capability_id != CAPABILITY_ID:
        raise FutureProfileSnapshotError("CAPABILITY_ID_MISMATCH")
    if snapshot.profile_version != PROFILE_VERSION:
        raise FutureProfileSnapshotError("PROFILE_VERSION_MISMATCH")
    if snapshot.integrity_digest != snapshot.compute_integrity_digest():
        raise FutureProfileSnapshotError("INTEGRITY_DIGEST_MISMATCH")
    auth = snapshot.authority or authority_block_v1()
    for key in ("PROFILE_CAN_RERANK", "PROFILE_CAN_SELECT", "PROFILE_CAN_BIND"):
        if auth.get(key):
            raise FutureProfileSnapshotError(f"{key}_FORBIDDEN")
    if auth.get("MAX_POSITIONS_EFFECTIVE") != 1:
        raise FutureProfileSnapshotError("MAX_POSITIONS_EFFECTIVE_DRIFT")
    if auth.get("MULTI_FUTURE_RUNTIME_AUTHORIZED"):
        raise FutureProfileSnapshotError("MULTI_FUTURE_AUTHORITY_FORBIDDEN")
    seen: set[str] = set()
    for instrument in snapshot.instruments:
        if instrument.canonical_instrument_id in seen:
            raise FutureProfileSnapshotError("DUPLICATE_PROFILE_INSTRUMENT")
        seen.add(instrument.canonical_instrument_id)
        if instrument.profile_field_count != len(instrument.fields):
            raise FutureProfileSnapshotError("PROFILE_FIELD_COUNT_MISMATCH")
        for row in instrument.fields:
            if row.authority_class not in FIELD_AUTHORITY_CLASSES:
                raise FutureProfileSnapshotError("FIELD_AUTHORITY_CLASS_INVALID", row.field_id)
            if row.availability_state not in FIELD_AVAILABILITY_STATES:
                raise FutureProfileSnapshotError("FIELD_AVAILABILITY_STATE_INVALID", row.field_id)
            if row.authority_class == AUTHORITY_PROFILE_ONLY and row.field_id in {
                "rank_position",
                "balanced_movement_score",
            }:
                raise FutureProfileSnapshotError("RANKING_FIELD_MARKED_PROFILE_ONLY")
            if row.availability_state == AVAILABLE and row.value is None:
                raise FutureProfileSnapshotError("AVAILABLE_FIELD_REQUIRES_VALUE", row.field_id)
            if row.availability_state == MISSING and not row.missing_reason:
                raise FutureProfileSnapshotError("MISSING_FIELD_REQUIRES_REASON", row.field_id)


def round_trip_future_profile_snapshot_v1(snapshot: FutureProfileSnapshotV1) -> None:
    serialized = canonical_json_dumps(snapshot.to_dict())
    restored = FutureProfileSnapshotV1.from_dict(json.loads(serialized))
    if canonical_json_dumps(restored.to_dict()) != serialized:
        raise FutureProfileSnapshotError("ROUND_TRIP_CANONICAL_JSON_MISMATCH")
    validate_future_profile_snapshot_v1(restored)


def profile_summary_counts_v1(snapshot: FutureProfileSnapshotV1) -> dict[str, int]:
    fields = [field for instrument in snapshot.instruments for field in instrument.fields]
    return {
        "profile_field_count": len(fields),
        "profile_only_field_count": sum(
            1 for field in fields if field.authority_class == AUTHORITY_PROFILE_ONLY
        ),
        "unclassified_field_count": sum(
            1 for field in fields if field.authority_class == AUTHORITY_UNCLASSIFIED
        ),
        "ranking_input_field_count": sum(
            1 for field in fields if field.authority_class == AUTHORITY_RANKING_INPUT
        ),
        "eligibility_safety_field_count": sum(
            1 for field in fields if field.authority_class == AUTHORITY_ELIGIBILITY_SAFETY
        ),
    }
