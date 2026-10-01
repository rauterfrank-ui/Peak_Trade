"""DTOs for per-lane instrument runtime identity (carry-only, no selection authority)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


@dataclass(frozen=True)
class OccupiedLaneRuntimeInstrumentIdentityV1:
    """Immutable identity for one occupied lane assignment generation."""

    lane_id: str
    canonical_instrument_id: str
    venue_native_id: str
    lane_identity: BoundInstrumentLaneIdentityV1
    selection_id: str
    selection_integrity_digest: str
    ranking_snapshot_id: str
    ranking_integrity_digest: str

    @staticmethod
    def from_bound(
        *, lane_id: str, bound: BoundInstrumentV1
    ) -> OccupiedLaneRuntimeInstrumentIdentityV1:
        lane_identity = BoundInstrumentLaneIdentityV1.from_bound_instrument(
            lane_id=lane_id, bound=bound
        )
        return OccupiedLaneRuntimeInstrumentIdentityV1(
            lane_id=str(lane_id),
            canonical_instrument_id=str(bound.instrument_id),
            venue_native_id=str(bound.venue_native_id or "").strip(),
            lane_identity=lane_identity,
            selection_id=str(bound.selection_id or ""),
            selection_integrity_digest=str(bound.selection_integrity_digest or ""),
            ranking_snapshot_id=str(bound.ranking_snapshot_id or ""),
            ranking_integrity_digest=str(bound.ranking_integrity_digest or ""),
        )

    def to_manifest_dict(self) -> dict[str, str]:
        return {
            "lane_id": self.lane_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_native_id": self.venue_native_id,
            "bound_instrument_identity": self.lane_identity.bound_instrument_identity,
            "instrument_epoch": self.lane_identity.instrument_epoch,
            "selection_id": self.selection_id,
            "selection_integrity_digest": self.selection_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "ranking_integrity_digest": self.ranking_integrity_digest,
        }


@dataclass(frozen=True)
class PerLanePositionTruthV1:
    status: str
    venue_flat: bool
    existing_position_side: ExistingPositionSide
    position_status_source: str


@dataclass(frozen=True)
class PerLaneReconciliationAdmissionV1:
    admitted: bool
    reason_code: str
    instrument_reconciled: bool
    global_portfolio_healthy: bool


@dataclass(frozen=True)
class PerLaneGovernedIngressV1:
    identity: OccupiedLaneRuntimeInstrumentIdentityV1
    candles_payload: Mapping[str, Any]
    finalized_closes: tuple[float, ...]
    last_finalized_event_ts_unix: float
    position: PerLanePositionTruthV1
    reconciliation: PerLaneReconciliationAdmissionV1


@dataclass(frozen=True)
class LaneOwnershipIndexV1:
    lane_to_instrument: tuple[tuple[str, str], ...]
    instrument_to_lane: tuple[tuple[str, str], ...]

    @staticmethod
    def build(
        identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
    ) -> LaneOwnershipIndexV1:
        l2i: dict[str, str] = {}
        i2l: dict[str, str] = {}
        for lane_id, ident in sorted(identities.items()):
            inst = ident.canonical_instrument_id
            l2i[lane_id] = inst
            prior = i2l.get(inst)
            if prior is not None and prior != lane_id:
                raise ValueError(f"duplicate_instrument:{inst}")
            i2l[inst] = lane_id
        return LaneOwnershipIndexV1(
            lane_to_instrument=tuple(sorted(l2i.items())),
            instrument_to_lane=tuple(sorted(i2l.items())),
        )
