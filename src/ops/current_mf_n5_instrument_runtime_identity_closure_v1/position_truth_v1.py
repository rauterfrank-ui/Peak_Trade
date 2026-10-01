"""Per-lane position truth via extract_position_truth_v1 (D2)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_POSITION_SHARED_FORBIDDEN,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
    PerLanePositionTruthV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    extract_position_truth_v1,
)


class PerLanePositionTruthError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _positions_payload(occupancy_payloads: Mapping[str, Any]) -> Any:
    positions = occupancy_payloads.get("POSITIONS")
    if positions is not None:
        return positions
    return occupancy_payloads


def resolve_per_lane_position_truth_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    occupancy_payloads: Mapping[str, Any],
    global_venue_flat: bool | None = None,
    global_existing_side: ExistingPositionSide | None = None,
    allow_global_fallback: bool,
) -> PerLanePositionTruthV1:
    if allow_global_fallback:
        if global_venue_flat is None or global_existing_side is None:
            raise PerLanePositionTruthError(
                FAILURE_POSITION_SHARED_FORBIDDEN,
                "global_position_required",
            )
        return PerLanePositionTruthV1(
            status="GLOBAL_FALLBACK_N1",
            venue_flat=bool(global_venue_flat),
            existing_position_side=global_existing_side,
            position_status_source="global_kwarg",
        )
    payload = _positions_payload(occupancy_payloads)
    status, venue_flat, side = extract_position_truth_v1(
        payload, native_id=identity.venue_native_id
    )
    return PerLanePositionTruthV1(
        status=str(status),
        venue_flat=bool(venue_flat),
        existing_position_side=side,
        position_status_source="extract_position_truth_v1",
    )


def resolve_all_lane_position_truths_v1(
    *,
    identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
    occupancy_payloads: Mapping[str, Any],
    global_venue_flat: bool,
    global_existing_position_side: ExistingPositionSide,
    multi_lane: bool,
) -> dict[str, PerLanePositionTruthV1]:
    allow_global = not multi_lane
    if multi_lane:
        native_ids = {identities[l].venue_native_id for l in identities}
        if len(native_ids) == 1:
            allow_global = True
    out: dict[str, PerLanePositionTruthV1] = {}
    for lane_id, identity in sorted(identities.items()):
        out[lane_id] = resolve_per_lane_position_truth_v1(
            identity=identity,
            occupancy_payloads=occupancy_payloads,
            global_venue_flat=global_venue_flat,
            global_existing_side=global_existing_position_side,
            allow_global_fallback=allow_global,
        )
    if multi_lane and len({identities[l].venue_native_id for l in identities}) > 1:
        for lane_id in identities:
            if out[lane_id].position_status_source == "global_kwarg":
                raise PerLanePositionTruthError(
                    FAILURE_POSITION_SHARED_FORBIDDEN,
                    lane_id,
                )
    return out
