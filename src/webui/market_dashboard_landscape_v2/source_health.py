"""Unified Source Health aggregation for Market Dashboard Landscape V2.

Aggregation-only: never invents per-slot truth, never upgrades MISSING to
AVAILABLE, never recomputes domain decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .availability import Availability
from .contracts import SCHEMA_FAMILY, SCHEMA_VERSION, ProjectionSnapshot, _ProjectionBase
from .owner_registry import REQUIRED_PROJECTION_SLOTS
from .provenance import FreshnessV1, SnapshotProvenanceV1

SOURCE_HEALTH_SCHEMA_ID = f"{SCHEMA_FAMILY}.source_health.{SCHEMA_VERSION}"


@dataclass(frozen=True)
class DashboardSourceHealthSnapshotV1:
    """Complete availability map across required Landscape projection slots."""

    schema_id: str
    schema_version: str
    provenance: SnapshotProvenanceV1
    freshness: FreshnessV1
    availability: Availability
    slot_availability: Mapping[str, Availability]
    incomplete_slots: tuple[str, ...]
    generated_at: datetime

    def __post_init__(self) -> None:
        if self.schema_id != SOURCE_HEALTH_SCHEMA_ID:
            raise ValueError(f"schema_id must be {SOURCE_HEALTH_SCHEMA_ID!r}")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}")
        if not isinstance(self.provenance, SnapshotProvenanceV1):
            raise TypeError("provenance required")
        if not isinstance(self.freshness, FreshnessV1):
            raise TypeError("freshness required")
        if not isinstance(self.availability, Availability):
            raise TypeError("availability required")
        if self.availability != self.provenance.availability:
            raise ValueError("availability must match provenance.availability")
        normalized = {str(k): v for k, v in self.slot_availability.items()}
        for slot in REQUIRED_PROJECTION_SLOTS:
            if slot == "source_health":
                continue
            if slot not in normalized:
                raise ValueError(f"missing required slot in source health: {slot}")
            if not isinstance(normalized[slot], Availability):
                raise TypeError(f"slot {slot} availability must be Availability")
        unexpected = set(normalized) - (set(REQUIRED_PROJECTION_SLOTS) - {"source_health"})
        if unexpected:
            raise ValueError(f"unexpected source-health slots: {sorted(unexpected)}")
        object.__setattr__(self, "slot_availability", dict(normalized))
        object.__setattr__(self, "incomplete_slots", tuple(self.incomplete_slots))

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "availability": self.availability.value,
            "provenance": self.provenance.to_json_dict(),
            "freshness": self.freshness.to_json_dict(),
            "slot_availability": {
                slot: state.value for slot, state in sorted(self.slot_availability.items())
            },
            "incomplete_slots": list(self.incomplete_slots),
            "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
        }


def _aggregate_availability(states: Mapping[str, Availability]) -> Availability:
    values = list(states.values())
    if any(state is Availability.INVALID for state in values):
        return Availability.INVALID
    if any(state is Availability.MISSING_SOURCE for state in values):
        return Availability.MISSING_SOURCE
    if any(state is Availability.STALE for state in values):
        return Availability.STALE
    if any(state is Availability.NOT_BOUND for state in values):
        return Availability.NOT_BOUND
    if values and all(state is Availability.AVAILABLE for state in values):
        return Availability.AVAILABLE
    # Empty map is invalid — callers must supply complete slot maps.
    raise ValueError("cannot aggregate empty availability map")


def build_source_health_from_snapshots(
    snapshots: Mapping[str, _ProjectionBase | ProjectionSnapshot],
    *,
    generated_at: datetime,
    producer_module: str = "webui.market_dashboard_landscape_v2.source_health",
    git_sha: str | None = None,
) -> DashboardSourceHealthSnapshotV1:
    """Build Source Health from explicit projection snapshots.

    Fail-closed: every required slot except source_health itself must be present.
    """
    if generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    slot_availability: dict[str, Availability] = {}
    for slot in REQUIRED_PROJECTION_SLOTS:
        if slot == "source_health":
            continue
        if slot not in snapshots:
            raise ValueError(f"MISSING_SOURCE: required snapshot slot absent: {slot}")
        snap = snapshots[slot]
        if not isinstance(snap, _ProjectionBase):
            raise TypeError(f"snapshot for {slot} must be a Landscape projection")
        slot_availability[slot] = snap.availability

    incomplete = tuple(
        sorted(
            slot for slot, state in slot_availability.items() if state is not Availability.AVAILABLE
        )
    )
    aggregate = _aggregate_availability(slot_availability)
    provenance = SnapshotProvenanceV1(
        schema_id=SOURCE_HEALTH_SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        producer_module=producer_module,
        generated_at=generated_at,
        effective_at=generated_at,
        source_kind="source_health_aggregation",
        source_reference="slot_availability_map",
        evidence_digest=None,
        git_sha=git_sha,
        availability=aggregate,
    )
    freshness = FreshnessV1(
        observed_at=generated_at,
        max_age_seconds=None,
        is_stale=aggregate is Availability.STALE,
        stale_reason="AGGREGATE_CONTAINS_STALE_SLOT" if aggregate is Availability.STALE else None,
    )
    return DashboardSourceHealthSnapshotV1(
        schema_id=SOURCE_HEALTH_SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        provenance=provenance,
        freshness=freshness,
        availability=aggregate,
        slot_availability=slot_availability,
        incomplete_slots=incomplete,
        generated_at=generated_at,
    )
