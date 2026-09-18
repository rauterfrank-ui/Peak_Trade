"""Occupied-lane MV2/DP decision-state addressing: resolve, seam bind, invoke, in-memory carry.

Deterministic occupied-lane → IsolatedLaneSlotV1.lane_state_root mapping,
bound to the pre-cycle consumption seam, then lane-isolated invocation of
the existing N=1 MV2+DP cycle. S5 keeps each lane's outgoing cursor in the
existing invocation record and passes that same object as the next cycle's
incoming cursor. Does not persist, load, restore from disk, bind Cap61, or
join a host.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    CURSOR_BUNDLE_TYPE,
    CURSOR_FILENAME,
    CURSOR_OWNER_CHANGE_REQUIRED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    FAILURE_ALIASED_LANE_STATE,
    FAILURE_AUTHORITY,
    FAILURE_BOUND_TYPE,
    FAILURE_CURSOR_ADDRESS_ALIAS,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_INCOMING_CURSOR_FORBIDDEN,
    FAILURE_INVALID_STORE_ROOT,
    FAILURE_MISSING_LANE_STATE,
    FAILURE_MISSING_STORE_ROOT,
    FAILURE_MISMATCHED_LANE_STATE,
    FAILURE_N1_GLOBAL_CURSOR_STORE,
    FAILURE_OCCUPANCY,
    FAILURE_PAIR_TYPE,
    FAILURE_PRIOR_INVOCATION_TYPE,
    FAILURE_SEAM_STORE_ROOT_MISMATCH,
    FAILURE_SHARED_G17_PRODUCER,
    FAILURE_SHARED_STORE_ROOT,
    FAILURE_SLOT_TYPE,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    GLOBAL_N1_CURSOR_REJECTED,
    HOST_JOIN,
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
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK,
    MAY_PERSIST_CURSOR,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    OCCUPIED_LANES_ONLY,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    S2_IMPLEMENTED,
    S3_IMPLEMENTED,
    S4_IMPLEMENTED,
    S5_IMPLEMENTED,
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    THIS_SLICE_MAY_RESTORE_CURSOR,
    UNIQUE_MUTABLE_ROOTS_ENFORCED,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    CurrentProductiveMasterV2CycleResultV1,
    ExistingPositionSide,
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class OccupiedLaneMv2DpDecisionStateConsumerInvocationV1:
    lane_id: str
    bound_instrument: BoundInstrumentV1
    store_root: str
    cursor_address: str
    incoming_cursor: object | None
    persist_enabled: bool
    cap61_state_root_bound: bool
    cycle_result: CurrentProductiveMasterV2CycleResultV1


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        not S2_IMPLEMENTED
        or not S3_IMPLEMENTED
        or not S4_IMPLEMENTED
        or not S5_IMPLEMENTED
        or not OCCUPIED_LANES_ONLY
        or not UNIQUE_MUTABLE_ROOTS_ENFORCED
        or not GLOBAL_N1_CURSOR_REJECTED
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
        or CURSOR_OWNER_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or MAY_PERSIST_CURSOR
        or MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK
        or MAY_BIND_CAP61_STATE_ROOT
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


def _is_n1_global_cursor_path(path: str) -> bool:
    relpath = N1_GLOBAL_CURSOR_STORE_RELPATH
    stripped = str(path).strip()
    if stripped == relpath:
        return True
    posix = Path(path).expanduser().resolve().as_posix()
    if posix == lane_state_root_key(relpath):
        return True
    return posix.endswith("/" + relpath)


def _n1_global_cursor_store_forbidden(root: str) -> bool:
    if _is_n1_global_cursor_path(root):
        return True
    return _is_n1_global_cursor_path(str(Path(lane_state_root_key(root)).parent))


def _unpack_pair(lane_id: str, value: object) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    if not isinstance(value, tuple) or len(value) != 2:
        _fail(FAILURE_PAIR_TYPE, lane_id)
    slot, bound = value
    if not isinstance(slot, IsolatedLaneSlotV1):
        _fail(FAILURE_SLOT_TYPE, lane_id)
    if not isinstance(bound, BoundInstrumentV1):
        _fail(FAILURE_BOUND_TYPE, lane_id)
    return slot, bound


def resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> dict[str, str]:
    """Map occupied pair-map lanes onto existing per-lane lane_state_root strings."""
    _assert_non_authority()
    unknown = sorted(set(composed_pairs) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))

    resolved: dict[str, str] = {}
    seen_roots: dict[str, str] = {}
    for lane_id in LANE_IDS:
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        slot, bound = _unpack_pair(lane_id, pair)
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
        if slot.lane_id != lane_id:
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        _require_identity_match(lane_id=lane_id, slot=slot, bound=bound)
        raw_root = str(slot.lane_state_root or "").strip()
        if not raw_root:
            _fail(FAILURE_MISSING_STORE_ROOT, lane_id)
        if _n1_global_cursor_store_forbidden(raw_root):
            _fail(FAILURE_N1_GLOBAL_CURSOR_STORE, lane_id)
        expected_root = lane_state_root_for(
            topology_state_root_base=Path(raw_root).parent,
            lane_id=lane_id,
        )
        actual_root = lane_state_root_key(raw_root)
        if actual_root != expected_root:
            _fail(FAILURE_INVALID_STORE_ROOT, lane_id)
        prior_lane = seen_roots.get(actual_root)
        if prior_lane is not None:
            _fail(FAILURE_SHARED_STORE_ROOT, f"{prior_lane},{lane_id}")
        seen_roots[actual_root] = lane_id
        resolved[lane_id] = actual_root
    return resolved


def bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> dict[str, tuple[BoundInstrumentV1, str, str]]:
    """Bind resolver output to the pre-cycle seam. Does not invoke the consumer."""
    _assert_non_authority()
    resolved_roots = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(composed_pairs)
    bound_seam: dict[str, tuple[BoundInstrumentV1, str, str]] = {}
    seen_cursor_addresses: dict[str, str] = {}
    for lane_id in LANE_IDS:
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        slot, bound = _unpack_pair(lane_id, pair)
        store_root = resolved_roots.get(lane_id)
        if store_root is None:
            _fail(FAILURE_MISSING_STORE_ROOT, lane_id)
        if store_root != lane_state_root_key(slot.lane_state_root):
            _fail(FAILURE_SEAM_STORE_ROOT_MISMATCH, lane_id)
        if _n1_global_cursor_store_forbidden(store_root):
            _fail(FAILURE_N1_GLOBAL_CURSOR_STORE, lane_id)
        cursor_address = lane_state_root_key(Path(store_root) / CURSOR_FILENAME)
        if _is_n1_global_cursor_path(cursor_address):
            _fail(FAILURE_N1_GLOBAL_CURSOR_STORE, lane_id)
        prior_lane = seen_cursor_addresses.get(cursor_address)
        if prior_lane is not None:
            _fail(FAILURE_CURSOR_ADDRESS_ALIAS, f"{prior_lane},{lane_id}")
        seen_cursor_addresses[cursor_address] = lane_id
        bound_seam[lane_id] = (bound, store_root, cursor_address)
    unresolved = sorted(set(resolved_roots) - set(bound_seam))
    extra = sorted(set(bound_seam) - set(resolved_roots))
    if unresolved or extra:
        _fail(FAILURE_SEAM_STORE_ROOT_MISMATCH, ",".join(unresolved + extra))
    return bound_seam


def _resolve_lane_g17_producers(
    occupied_lane_ids: Sequence[str],
    producers: Mapping[str, object] | None,
) -> dict[str, object | None]:
    if producers is None:
        return {lane_id: None for lane_id in occupied_lane_ids}
    unknown = sorted(set(producers) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    if set(producers) != set(occupied_lane_ids):
        _fail(
            FAILURE_MISMATCHED_LANE_STATE,
            ",".join(sorted(set(producers) ^ set(occupied_lane_ids))),
        )
    resolved: dict[str, object | None] = {}
    seen_ids: dict[int, str] = {}
    for lane_id in occupied_lane_ids:
        producer = producers[lane_id]
        if producer is None:
            _fail(FAILURE_MISMATCHED_LANE_STATE, lane_id)
        prior_lane = seen_ids.get(id(producer))
        if prior_lane is not None:
            _fail(FAILURE_SHARED_G17_PRODUCER, f"{prior_lane},{lane_id}")
        seen_ids[id(producer)] = lane_id
        resolved[lane_id] = producer
    return resolved


def _cursor_from_prior_invocation(
    *,
    lane_id: str,
    bound: BoundInstrumentV1,
    store_root: str,
    prior: object,
) -> object:
    if not isinstance(prior, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1):
        _fail(FAILURE_PRIOR_INVOCATION_TYPE, lane_id)
    if prior.lane_id != lane_id or prior.store_root != store_root:
        _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
    prior_bound = prior.bound_instrument
    if (
        prior_bound.instrument_id != bound.instrument_id
        or prior_bound.venue_native_id != bound.venue_native_id
        or prior_bound.universe_snapshot_id != bound.universe_snapshot_id
        or prior_bound.ranking_snapshot_id != bound.ranking_snapshot_id
        or prior_bound.ranking_integrity_digest != bound.ranking_integrity_digest
    ):
        _fail(FAILURE_MISMATCHED_LANE_STATE, lane_id)
    cursor = prior.cycle_result.outgoing_cursor
    if cursor is None:
        _fail(FAILURE_MISSING_LANE_STATE, lane_id)
    if isinstance(cursor, Mapping) or type(cursor).__name__ != CURSOR_BUNDLE_TYPE:
        _fail(FAILURE_MISMATCHED_LANE_STATE, lane_id)
    cursor_fields = getattr(type(cursor), "__dataclass_fields__", {})
    if "lane_id" in cursor_fields or "lane_state_root" in cursor_fields:
        _fail(FAILURE_AUTHORITY, "cursor_schema")
    if (
        getattr(cursor, "instrument_id", None) != bound.instrument_id
        or getattr(cursor, "venue_native_id", None) != bound.venue_native_id
    ):
        _fail(FAILURE_MISMATCHED_LANE_STATE, lane_id)
    return cursor


def invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    *,
    cycle_id_prefix: str,
    observed_unix: float,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    incoming_cursor: object | None = None,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
) -> dict[str, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1]:
    """Lane-isolated bounded harness invoke of the existing N=1 MV2+DP cycle.

    Addressing is the S3 seam (`IsolatedLaneSlotV1.lane_state_root`). The cycle
    does not take `store_root`. Incoming cursor must be absent. Persist is not
    performed. This is not a productive MF or host join.
    """
    _assert_non_authority()
    if not THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER:
        _fail(FAILURE_AUTHORITY, OWNER)
    if incoming_cursor is not None:
        _fail(FAILURE_INCOMING_CURSOR_FORBIDDEN, OWNER)
    prefix = str(cycle_id_prefix or "").strip()
    if not prefix:
        _fail(FAILURE_AUTHORITY, "cycle_id_prefix")
    bound_seam = bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(composed_pairs)
    producers = _resolve_lane_g17_producers(tuple(bound_seam), g17_typed_vol_producers)
    invoked: dict[str, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1] = {}
    for lane_id in LANE_IDS:
        item = bound_seam.get(lane_id)
        if item is None:
            continue
        bound, store_root, cursor_address = item
        cycle_result = run_current_productive_master_v2_runtime_cycle_v1(
            bound_instrument=bound,
            cycle_id=f"{prefix}:{lane_id}",
            observed_unix=observed_unix,
            mark_px=mark_px,
            index_px=index_px,
            bid_px=bid_px,
            ask_px=ask_px,
            volume=volume,
            open_interest=open_interest,
            funding_rate=funding_rate,
            finalized_closes=finalized_closes,
            last_finalized_event_ts_unix=last_finalized_event_ts_unix,
            venue_flat=venue_flat,
            existing_position_side=existing_position_side,
            incoming_cursor=None,
            g17_typed_vol_producer=producers[lane_id],
        )
        invoked[lane_id] = OccupiedLaneMv2DpDecisionStateConsumerInvocationV1(
            lane_id=lane_id,
            bound_instrument=bound,
            store_root=store_root,
            cursor_address=cursor_address,
            incoming_cursor=None,
            persist_enabled=False,
            cap61_state_root_bound=False,
            cycle_result=cycle_result,
        )
    return invoked


def carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    prior_invocations: Mapping[str, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1],
    *,
    cycle_id_prefix: str,
    observed_unix: float,
    mark_px: float,
    index_px: float,
    bid_px: float,
    ask_px: float,
    volume: float,
    open_interest: float,
    funding_rate: float,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    g17_typed_vol_producers: Mapping[str, object] | None = None,
) -> dict[str, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1]:
    """Pass each occupied lane's prior outgoing cursor as the next incoming cursor.

    The in-memory holder is the existing invocation record's outgoing cursor.
    Lane state roots stay external addressing and are not passed into the cycle.
    """
    _assert_non_authority()
    if not THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER:
        _fail(FAILURE_AUTHORITY, OWNER)
    prefix = str(cycle_id_prefix or "").strip()
    if not prefix:
        _fail(FAILURE_AUTHORITY, "cycle_id_prefix")
    unknown_prior = sorted(set(prior_invocations) - set(LANE_IDS))
    if unknown_prior:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown_prior))
    bound_seam = bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(composed_pairs)
    if set(prior_invocations) != set(bound_seam):
        missing = sorted(set(bound_seam) - set(prior_invocations))
        extra = sorted(set(prior_invocations) - set(bound_seam))
        if missing:
            _fail(FAILURE_MISSING_LANE_STATE, ",".join(missing))
        _fail(FAILURE_MISMATCHED_LANE_STATE, ",".join(extra))
    lane_cursors: dict[str, object] = {}
    seen_cursor_ids: dict[int, str] = {}
    for lane_id in LANE_IDS:
        item = bound_seam.get(lane_id)
        if item is None:
            continue
        bound, store_root, _cursor_address = item
        cursor = _cursor_from_prior_invocation(
            lane_id=lane_id,
            bound=bound,
            store_root=store_root,
            prior=prior_invocations[lane_id],
        )
        prior_lane = seen_cursor_ids.get(id(cursor))
        if prior_lane is not None:
            _fail(FAILURE_ALIASED_LANE_STATE, f"{prior_lane},{lane_id}")
        seen_cursor_ids[id(cursor)] = lane_id
        lane_cursors[lane_id] = cursor
    producers = _resolve_lane_g17_producers(tuple(bound_seam), g17_typed_vol_producers)
    carried: dict[str, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1] = {}
    for lane_id in LANE_IDS:
        item = bound_seam.get(lane_id)
        if item is None:
            continue
        bound, store_root, cursor_address = item
        lane_cursor = lane_cursors[lane_id]
        cycle_result = run_current_productive_master_v2_runtime_cycle_v1(
            bound_instrument=bound,
            cycle_id=f"{prefix}:{lane_id}",
            observed_unix=observed_unix,
            mark_px=mark_px,
            index_px=index_px,
            bid_px=bid_px,
            ask_px=ask_px,
            volume=volume,
            open_interest=open_interest,
            funding_rate=funding_rate,
            finalized_closes=finalized_closes,
            last_finalized_event_ts_unix=last_finalized_event_ts_unix,
            venue_flat=venue_flat,
            existing_position_side=existing_position_side,
            incoming_cursor=lane_cursor,
            g17_typed_vol_producer=producers[lane_id],
        )
        carried[lane_id] = OccupiedLaneMv2DpDecisionStateConsumerInvocationV1(
            lane_id=lane_id,
            bound_instrument=bound,
            store_root=store_root,
            cursor_address=cursor_address,
            incoming_cursor=lane_cursor,
            persist_enabled=False,
            cap61_state_root_bound=False,
            cycle_result=cycle_result,
        )
    return carried
