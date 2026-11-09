"""Per-lane position truth via extract_position_truth_v1 (D2)."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_POSITION_PAYLOAD_INVALID,
    FAILURE_POSITION_SHARED_FORBIDDEN,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
    PerLanePositionQuantityObservationV1,
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
    if "POSITIONS" in occupancy_payloads:
        return occupancy_payloads["POSITIONS"]
    return occupancy_payloads


def _validate_positions_payload_v1(payload: Any) -> None:
    if (
        not isinstance(payload, Mapping)
        or str(payload.get("code", "0")) != "0"
        or not isinstance(payload.get("data"), list)
    ):
        raise PerLanePositionTruthError(FAILURE_POSITION_PAYLOAD_INVALID, "response")
    for row in payload["data"]:
        if not isinstance(row, Mapping) or not str(row.get("instId") or "").strip():
            raise PerLanePositionTruthError(FAILURE_POSITION_PAYLOAD_INVALID, "row_identity")
        try:
            quantity = Decimal(str(row.get("pos")))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise PerLanePositionTruthError(FAILURE_POSITION_PAYLOAD_INVALID, "quantity") from exc
        if isinstance(row.get("pos"), bool) or not quantity.is_finite():
            raise PerLanePositionTruthError(FAILURE_POSITION_PAYLOAD_INVALID, "quantity")


def resolve_per_lane_position_truth_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    occupancy_payloads: Mapping[str, Any],
    global_venue_flat: bool | None = None,
    global_existing_side: ExistingPositionSide | None = None,
    allow_global_fallback: bool,
) -> PerLanePositionTruthV1:
    # A supplied positions response is authoritative for this handoff even for
    # one occupied lane. Never hide it behind a default global FLAT value.
    has_position_response = any(key in occupancy_payloads for key in ("POSITIONS", "data", "code"))
    if allow_global_fallback and not has_position_response:
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
    _validate_positions_payload_v1(payload)
    status, venue_flat, side = extract_position_truth_v1(
        payload, native_id=identity.venue_native_id
    )
    quantity_observation = None
    if status == "BOUND_INSTRUMENT_OPEN":
        matched = [
            row
            for row in payload["data"]
            if str(row.get("instId") or "").strip() == identity.venue_native_id
            and Decimal(str(row["pos"])) != 0
        ]
        if len(matched) == 1:
            quantity_observation = PerLanePositionQuantityObservationV1(
                lane_id=identity.lane_id,
                canonical_instrument_id=identity.canonical_instrument_id,
                venue_native_id=identity.venue_native_id,
                instrument_epoch=identity.lane_identity.instrument_epoch,
                quantity=Decimal(str(matched[0]["pos"])).copy_abs(),
                position_side=side,
                snapshot_digest=hashlib.sha256(
                    json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
                ).hexdigest(),
            )
    return PerLanePositionTruthV1(
        status=str(status),
        venue_flat=bool(venue_flat),
        existing_position_side=side,
        position_status_source="extract_position_truth_v1",
        quantity_observation=quantity_observation,
    )


def resolve_all_lane_position_truths_v1(
    *,
    identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
    occupancy_payloads: Mapping[str, Any],
    global_venue_flat: bool,
    global_existing_position_side: ExistingPositionSide,
    multi_lane: bool,
    isolate_known_lane_positions: bool = False,
) -> dict[str, PerLanePositionTruthV1]:
    allow_global = not multi_lane
    if multi_lane:
        native_ids = {identities[l].venue_native_id for l in identities}
        if len(native_ids) == 1:
            allow_global = True
    out: dict[str, PerLanePositionTruthV1] = {}
    lane_payloads = None
    if (
        isolate_known_lane_positions
        and multi_lane
        and len({identities[l].venue_native_id for l in identities}) > 1
    ):
        payload = _positions_payload(occupancy_payloads)
        _validate_positions_payload_v1(payload)
        known_native_ids = {identity.venue_native_id for identity in identities.values()}
        if any(
            Decimal(str(row["pos"])) != 0 and str(row["instId"]).strip() not in known_native_ids
            for row in payload["data"]
        ):
            raise PerLanePositionTruthError(
                FAILURE_POSITION_SHARED_FORBIDDEN, "unowned_open_position"
            )
        lane_payloads = {
            lane: {
                "POSITIONS": {
                    **payload,
                    "data": [
                        row
                        for row in payload["data"]
                        if str(row["instId"]).strip() == identity.venue_native_id
                    ],
                }
            }
            for lane, identity in identities.items()
        }
    for lane_id, identity in sorted(identities.items()):
        out[lane_id] = resolve_per_lane_position_truth_v1(
            identity=identity,
            occupancy_payloads=(
                lane_payloads[lane_id] if lane_payloads is not None else occupancy_payloads
            ),
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
