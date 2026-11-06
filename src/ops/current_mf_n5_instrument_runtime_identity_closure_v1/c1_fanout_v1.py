"""Per-lane C1 resolution and instrument binding validation (D1)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_C1_FANOUT_SHARED_FORBIDDEN,
    FAILURE_C1_INSTRUMENT_MISMATCH,
    FAILURE_C1_LANE_MISSING,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)


class C1FanoutError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _payload_native_tag(payload: Mapping[str, Any]) -> str | None:
    tagged = payload.get("instId")
    if tagged is None:
        return None
    return str(tagged).strip() or None


def validate_candles_payload_for_native_id_v1(
    payload: Mapping[str, Any],
    *,
    venue_native_id: str,
    canonical_instrument_id: str,
) -> None:
    tagged = _payload_native_tag(payload)
    if tagged is not None and tagged != str(venue_native_id).strip():
        raise C1FanoutError(
            FAILURE_C1_INSTRUMENT_MISMATCH,
            f"native:{venue_native_id},tag:{tagged},inst:{canonical_instrument_id}",
        )


def resolve_per_lane_c1_payloads_v1(
    *,
    identities: Mapping[str, OccupiedLaneRuntimeInstrumentIdentityV1],
    candles_payload: Mapping[str, Any] | None,
    candles_payload_by_lane: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Mapping[str, Any]]:
    occupied = sorted(identities.keys())
    if not occupied:
        return {}
    if candles_payload_by_lane is not None:
        resolved: dict[str, Mapping[str, Any]] = {}
        for lane_id in occupied:
            payload = candles_payload_by_lane.get(lane_id)
            if payload is None:
                raise C1FanoutError(FAILURE_C1_LANE_MISSING, lane_id)
            ident = identities[lane_id]
            validate_candles_payload_for_native_id_v1(
                payload,
                venue_native_id=ident.venue_native_id,
                canonical_instrument_id=ident.canonical_instrument_id,
            )
            resolved[lane_id] = payload
        return resolved
    if candles_payload is None:
        raise C1FanoutError(FAILURE_C1_LANE_MISSING, "candles_required")
    native_ids = {identities[l].venue_native_id for l in occupied}
    if len(occupied) > 1 and len(native_ids) > 1:
        raise C1FanoutError(
            FAILURE_C1_FANOUT_SHARED_FORBIDDEN,
            f"lanes={len(occupied)},natives={len(native_ids)}",
        )
    ident0 = identities[occupied[0]]
    validate_candles_payload_for_native_id_v1(
        candles_payload,
        venue_native_id=ident0.venue_native_id,
        canonical_instrument_id=ident0.canonical_instrument_id,
    )
    return {lane_id: candles_payload for lane_id in occupied}


def extract_lane_closes_v1(
    payload: Mapping[str, Any],
) -> tuple[tuple[float, ...], float | None]:
    return extract_finalized_candle_closes_v1(payload)
