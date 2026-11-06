"""Position ↔ lane ownership index (D3)."""

from __future__ import annotations

from typing import Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_BINDING_MISMATCH,
    FAILURE_DUPLICATE_INSTRUMENT_OWNERSHIP,
    FAILURE_DUPLICATE_LANE_OWNERSHIP,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    LaneOwnershipIndexV1,
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class LaneOwnershipError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def build_identities_from_composed_pairs_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> dict[str, OccupiedLaneRuntimeInstrumentIdentityV1]:
    identities: dict[str, OccupiedLaneRuntimeInstrumentIdentityV1] = {}
    for lane_id, pair in sorted(composed_pairs.items()):
        slot, bound = pair
        if str(slot.canonical_instrument_id or "").strip() != str(bound.instrument_id):
            raise LaneOwnershipError(FAILURE_BINDING_MISMATCH, lane_id)
        identities[lane_id] = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
            lane_id=lane_id, bound=bound
        )
    return identities


def assert_lane_ownership_index_v1(
    identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
) -> LaneOwnershipIndexV1:
    seen_lanes: set[str] = set()
    seen_instruments: dict[str, str] = {}
    for lane_id, ident in sorted(identities.items()):
        if lane_id in seen_lanes:
            raise LaneOwnershipError(FAILURE_DUPLICATE_LANE_OWNERSHIP, lane_id)
        seen_lanes.add(lane_id)
        inst = ident.canonical_instrument_id
        prior = seen_instruments.get(inst)
        if prior is not None:
            raise LaneOwnershipError(
                FAILURE_DUPLICATE_INSTRUMENT_OWNERSHIP,
                f"{prior},{lane_id}:{inst}",
            )
        seen_instruments[inst] = lane_id
    return LaneOwnershipIndexV1.build(dict(identities))
