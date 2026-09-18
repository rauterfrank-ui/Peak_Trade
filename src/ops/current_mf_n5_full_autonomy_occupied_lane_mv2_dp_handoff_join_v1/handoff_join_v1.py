"""Compose admitted BoundInstrumentV1 values onto existing occupied-lane slots.

Identity-preserving per-lane pair map. Does not trade, rebind, rank, or join a host.
"""

from __future__ import annotations

from typing import Mapping, NoReturn

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    FAILURE_AUTHORITY,
    FAILURE_BOUND_TYPE,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_OCCUPANCY,
    FAILURE_STATE_ROOT_MISMATCH,
    FAILURE_TOPOLOGY_TYPE,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    HOST_JOIN,
    IDENTITY_PRESERVING_HANDOFF,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    PICK_ONE_AMONG_PREPARED_BOUNDS,
    S2_IMPLEMENTED,
    THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT,
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    THIS_SLICE_MAY_RESTORE_CURSOR,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    IsolatedLaneTopologyV1,
    lane_state_root_for,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class FullAutonomyOccupiedLaneMv2DpHandoffJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneMv2DpHandoffJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        not S2_IMPLEMENTED
        or not IDENTITY_PRESERVING_HANDOFF
        or PICK_ONE_AMONG_PREPARED_BOUNDS
        or JOIN_SELECTION_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_RUNTIME_ACTIVATION_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or JOIN_RANKING_AUTHORITY
        or JOIN_MEMBERSHIP_AUTHORITY
        or JOIN_MAPPING_AUTHORITY
        or JOIN_PERSISTENCE_AUTHORITY
        or JOIN_FULL_AUTONOMY_HOST_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or FULL_AUTONOMY_HOST_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT
        or THIS_SLICE_MAY_RESTORE_CURSOR
        or not UNIVERSE_ISOLATION_ENFORCED
    ):
        _fail(FAILURE_AUTHORITY, OWNER)
    if (
        CROSS_UNIVERSE_SELECTION
        or CROSS_UNIVERSE_PIN
        or CROSS_UNIVERSE_REPLACEMENT
        or CROSS_UNIVERSE_FALLBACK
        or CROSS_UNIVERSE_CANDIDATE_BORROWING
        or CROSS_UNIVERSE_RERANKING
        or MULTI_UNIVERSE_MERGE
        or INSTRUMENT_ID_ALONE_SUFFICIENT
    ):
        _fail(FAILURE_AUTHORITY, "constant_violation")


def _require_identity_match(
    *,
    lane_id: str,
    slot: IsolatedLaneSlotV1,
    bound: BoundInstrumentV1,
) -> None:
    if (
        slot.canonical_instrument_id != bound.instrument_id
        or slot.universe_snapshot_id != bound.universe_snapshot_id
        or slot.ranking_snapshot_id != bound.ranking_snapshot_id
        or slot.ranking_integrity_digest != bound.ranking_integrity_digest
    ):
        _fail(FAILURE_IDENTITY_MISMATCH, lane_id)


def compose_occupied_lane_mv2_dp_handoff_v1(
    admitted_by_lane: Mapping[str, BoundInstrumentV1],
    topology: IsolatedLaneTopologyV1,
) -> dict[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]]:
    """Compose admitted bounds onto occupied slots. Stop at the pair map."""
    _assert_non_authority()
    if not isinstance(topology, IsolatedLaneTopologyV1):
        _fail(FAILURE_TOPOLOGY_TYPE)
    unknown = sorted(set(admitted_by_lane) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    slots_by_id = {slot.lane_id: slot for slot in topology.slots}
    extra_slots = sorted(set(slots_by_id) - set(LANE_IDS))
    if extra_slots:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(extra_slots))

    composed: dict[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]] = {}
    for lane_id in LANE_IDS:
        bound = admitted_by_lane.get(lane_id)
        if bound is None:
            continue
        if not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_BOUND_TYPE, lane_id)
        slot = slots_by_id.get(lane_id)
        if slot is None or slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
        if slot.lane_id != lane_id:
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        expected_root = lane_state_root_for(
            topology_state_root_base=topology.topology_state_root_base,
            lane_id=lane_id,
        )
        if slot.lane_state_root != expected_root:
            _fail(FAILURE_STATE_ROOT_MISMATCH, lane_id)
        _require_identity_match(lane_id=lane_id, slot=slot, bound=bound)
        composed[lane_id] = (slot, bound)
    return composed
