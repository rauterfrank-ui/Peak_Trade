"""Typed input slots for the delayed G12 conjunction evaluator. Offline only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ObservationSlotV1:
    """One first-party GET observation. Not a completeness certificate."""

    endpoint: str
    observation_identity: str
    request_time_utc: str
    payload: Mapping[str, Any]
    query: Mapping[str, str] | None = None
    body_sha256: str | None = None
    http_status: int | None = None
    venue_code: str | None = None


@dataclass(frozen=True)
class FlattenLineageSlotV1:
    """Historical authorized flatten lineage. Not current position state."""

    authorized: bool
    reduce_only: bool
    ord_type: str
    side: str
    sz: str
    px: str
    cl_ord_id: str
    instrument_id: str
    venue_accepted: bool
    submit_time_utc: str
    submit_http_status: int | None
    pre_observation: ObservationSlotV1
    fill_cl_ord_id: str | None = None
    fill_instrument_id: str | None = None
    fill_side: str | None = None
    fill_sz: str | None = None
    fill_px: str | None = None
    fill_time_utc: str | None = None
    immediate_post_action_identity: str | None = None
    proven_pos_id: str | None = None


@dataclass(frozen=True)
class DelayedG12ConjunctionInputV1:
    """Separate slots. Do not collapse delayed zero, pending, and related."""

    instrument_id: str
    flatten_lineage: FlattenLineageSlotV1 | None
    delayed_target_zero: ObservationSlotV1 | None
    pending_orders: ObservationSlotV1 | None
    related_positions: ObservationSlotV1 | None
    forensic_local_treated_as_canonical: bool = False
