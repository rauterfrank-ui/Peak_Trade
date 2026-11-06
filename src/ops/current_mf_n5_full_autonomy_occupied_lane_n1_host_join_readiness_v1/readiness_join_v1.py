"""N=1 occupied-lane host-join readiness: address, do not join.

Consumes the existing N1 governed-cycle consumer, projects lane-local
host-join path params onto the canonical host owner, and stops before
ensure_host_activation_binding_v1. HOST_JOIN and cardinality stay unjoined.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    OccupiedLaneGovernedCycleN1ConsumerResultV1,
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    CANONICAL_HOST_JOIN_OWNER,
    CANONICAL_HOST_JOIN_SYMBOL,
    CANONICAL_PRODUCTIVE_HOST_ENTRY,
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CROSS_UNIVERSE_CANDIDATE_BORROWING,
    CROSS_UNIVERSE_FALLBACK,
    CROSS_UNIVERSE_PIN,
    CROSS_UNIVERSE_REPLACEMENT,
    CROSS_UNIVERSE_RERANKING,
    CROSS_UNIVERSE_SELECTION,
    CURSOR_OWNER_CHANGE_REQUIRED,
    CURSOR_SINGLE_WRITER,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_AUTHORITY,
    FAILURE_EXTERNAL_EFFECT,
    FAILURE_FORBIDDEN_KWARG,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_LANE_STATE_ROOT,
    FAILURE_NATIVE_ID_MISSING,
    FAILURE_OCCUPANCY,
    FAILURE_ORIGIN_MAIN_SHA,
    FAILURE_OWNER_BOUNDARY,
    FAILURE_PAIR_TYPE,
    FAILURE_RESULT_MISSING,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_COMPOSE_KWARGS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    GLOBAL_N1_CURSOR_REJECTED,
    HOST_JOIN,
    HOST_JOIN_ADDRESSED,
    HOST_JOIN_INVOKED,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_IMPLEMENTED,
    JOIN_MAPPING_AUTHORITY,
    JOIN_MEMBERSHIP_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_CROSS_FIRST_TRUE_OWNER_BOUNDARY,
    MAY_ENABLE_HOST,
    MAY_INVOKE_HOST_JOIN,
    MAY_INVOKE_PRODUCTIVE_HOST_ENTRY,
    MAY_JOIN_CAP72_LIVE_EXECUTION_PORT,
    MAY_MINT_PERMIT,
    MAY_POST,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MULTI_UNIVERSE_MERGE,
    N1_CONSUMER_CHANGE_REQUIRED,
    N1_CONSUMER_CONSUMED,
    N1_CONSUMER_JOIN_READY,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    NEW_CURSOR_WRITER,
    NEW_HOST_OWNER_CREATED,
    OCCUPIED_LANES_ONLY,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    UNIQUE_MUTABLE_ROOTS_ENFORCED,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_COMPLETED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

_SUCCESS_DISPOSITIONS = frozenset(
    {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
        DISPOSITION_COMPLETED,
    }
)


class FullAutonomyOccupiedLaneN1HostJoinReadinessError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class OccupiedLaneN1HostJoinReadinessProjectionV1:
    lane_id: str
    bound_instrument: BoundInstrumentV1
    native_id: str
    instrument_id: str
    lane_state_root: str
    cursor_store_root: str
    lock_root: str
    evidence_root: str
    origin_main_sha: str
    writer_session_id: str
    host_join_owner: str
    host_join_symbol: str
    productive_host_entry: str
    n1_consumer_result: OccupiedLaneGovernedCycleN1ConsumerResultV1
    disposition: str
    post_count: int
    permit_created: bool
    external_effect_count: int
    cap61_state_root_bound: bool
    host_join_addressed: bool
    host_join_invoked: bool
    host_enabled: bool
    selected_future_present: bool
    instrument_binding_valid: bool
    n1_consumer_join_ready: bool


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneN1HostJoinReadinessError(code, detail)


def occupied_lane_n1_host_join_readiness_census_v1() -> dict[str, str]:
    """Minimal reuse census for the existing host/runtime/cursor/lock owners."""
    return {
        "CANONICAL_HOST_JOIN_OWNER": CANONICAL_HOST_JOIN_OWNER,
        "CANONICAL_HOST_JOIN_SYMBOL": CANONICAL_HOST_JOIN_SYMBOL,
        "CANONICAL_PRODUCTIVE_HOST_ENTRY": CANONICAL_PRODUCTIVE_HOST_ENTRY,
        "N1_CONSUMER_JOIN_SYMBOL": "invoke_occupied_lane_governed_cycle_n1_consumer_v1",
        "CURSOR_OWNER": (
            "ops.full_core_live_path_composition_root_v1."
            "current_productive_sidestate_confirmation_cursor_v1"
        ),
        "LOCKING_MODEL": "AuthorizationLifecycleLockV1.CYCLE_EXCLUSION_LOCK",
        "PRODUCTIVE_RUNTIME_CARDINALITY": PRODUCTIVE_RUNTIME_CARDINALITY,
        "ATLAS_AUTHORITY": ATLAS_AUTHORITY,
        "FIRST_TRUE_OWNER_BOUNDARY": (
            "INVOKE_ENSURE_HOST_ACTIVATION_BINDING_OR_FLIP_HOST_JOIN_"
            "OR_MF_PRODUCTIVE_JOIN_OR_CARDINALITY_1_JOINED"
        ),
    }


def _assert_non_authority() -> None:
    if (
        not JOIN_IMPLEMENTED
        or not N1_CONSUMER_CONSUMED
        or not N1_CONSUMER_JOIN_READY
        or not HOST_JOIN_ADDRESSED
        or HOST_JOIN_INVOKED
        or MAY_INVOKE_HOST_JOIN
        or MAY_ENABLE_HOST
        or MAY_JOIN_CAP72_LIVE_EXECUTION_PORT
        or MAY_INVOKE_PRODUCTIVE_HOST_ENTRY
        or MAY_CROSS_FIRST_TRUE_OWNER_BOUNDARY
        or MAY_MINT_PERMIT
        or MAY_POST
        or EXTERNAL_EFFECT_AUTHORIZED
        or not OCCUPIED_LANES_ONLY
        or not UNIQUE_MUTABLE_ROOTS_ENFORCED
        or not GLOBAL_N1_CURSOR_REJECTED
        or not CURSOR_SINGLE_WRITER
        or NEW_CURSOR_WRITER
        or NEW_HOST_OWNER_CREATED
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
        or N1_CONSUMER_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or EXECUTION_CONCURRENCY_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or MAY_BIND_CAP61_STATE_ROOT
        or PRODUCTIVE_RUNTIME_CARDINALITY != "1_UNJOINED"
        or not UNIVERSE_ISOLATION_ENFORCED
        or ATLAS_AUTHORITY != "NONE"
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


def _reject_n1_global_root(path: str, lane_id: str) -> None:
    stripped = str(path).strip()
    if stripped == N1_GLOBAL_CURSOR_STORE_RELPATH:
        _fail(FAILURE_LANE_STATE_ROOT, lane_id)
    if stripped.endswith("/" + N1_GLOBAL_CURSOR_STORE_RELPATH):
        _fail(FAILURE_LANE_STATE_ROOT, lane_id)


def address_occupied_lane_n1_consumer_to_host_join_seam_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    consumer_results: Mapping[str, OccupiedLaneGovernedCycleN1ConsumerResultV1],
    *,
    origin_main_sha: str,
    cycle_id_prefix: str,
) -> dict[str, OccupiedLaneN1HostJoinReadinessProjectionV1]:
    """Project N1 consumer results onto host-join path params. Does not join."""
    _assert_non_authority()
    sha = str(origin_main_sha or "").strip()
    if not sha:
        _fail(FAILURE_ORIGIN_MAIN_SHA, OWNER)
    prefix = str(cycle_id_prefix or "").strip()
    if not prefix:
        _fail(FAILURE_AUTHORITY, "cycle_id_prefix")
    unknown = sorted(set(composed_pairs) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    extra_results = sorted(set(consumer_results) - set(composed_pairs))
    if extra_results:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(extra_results))
    projections: dict[str, OccupiedLaneN1HostJoinReadinessProjectionV1] = {}
    seen_roots: dict[str, str] = {}
    for lane_id in LANE_IDS:
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        if not isinstance(pair, tuple) or len(pair) != 2:
            _fail(FAILURE_PAIR_TYPE, lane_id)
        slot, bound = pair
        if not isinstance(slot, IsolatedLaneSlotV1) or not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_PAIR_TYPE, lane_id)
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
        record = consumer_results.get(lane_id)
        if record is None:
            _fail(FAILURE_RESULT_MISSING, lane_id)
        native_id = str(bound.venue_native_id or "").strip()
        if not native_id:
            _fail(FAILURE_NATIVE_ID_MISSING, lane_id)
        if str(record.native_id or "").strip() != native_id:
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        if str(record.bound_instrument.venue_native_id or "").strip() != native_id:
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        if str(slot.canonical_instrument_id or "").strip() != str(bound.instrument_id):
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        lane_state_root = lane_state_root_key(slot.lane_state_root)
        if not lane_state_root:
            _fail(FAILURE_LANE_STATE_ROOT, lane_id)
        if lane_state_root_key(record.cursor_store_root) != lane_state_root:
            _fail(FAILURE_LANE_STATE_ROOT, lane_id)
        _reject_n1_global_root(lane_state_root, lane_id)
        _reject_n1_global_root(record.cursor_store_root, lane_id)
        _reject_n1_global_root(record.lock_root, lane_id)
        _reject_n1_global_root(record.evidence_root, lane_id)
        for role, root in (
            ("cursor", record.cursor_store_root),
            ("lock", record.lock_root),
            ("evidence", record.evidence_root),
        ):
            prior = seen_roots.get(root)
            if prior is not None:
                _fail(FAILURE_LANE_STATE_ROOT, f"{prior},{lane_id}:{role}")
            seen_roots[root] = f"{lane_id}:{role}"
        cycle = record.governed_cycle_result
        if int(cycle.post_count) != 0 or cycle.permit_created is not False:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if int(cycle.external_effect_count) != 0:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if record.cap61_state_root_bound is not False:
            _fail(FAILURE_AUTHORITY, "cap61_bound")
        if HOST_JOIN or MAY_INVOKE_HOST_JOIN or MAY_ENABLE_HOST:
            _fail(FAILURE_OWNER_BOUNDARY, lane_id)
        projections[lane_id] = OccupiedLaneN1HostJoinReadinessProjectionV1(
            lane_id=lane_id,
            bound_instrument=bound,
            native_id=native_id,
            instrument_id=str(bound.instrument_id),
            lane_state_root=lane_state_root,
            cursor_store_root=record.cursor_store_root,
            lock_root=record.lock_root,
            evidence_root=record.evidence_root,
            origin_main_sha=sha,
            writer_session_id=f"{prefix}:{lane_id}",
            host_join_owner=CANONICAL_HOST_JOIN_OWNER,
            host_join_symbol=CANONICAL_HOST_JOIN_SYMBOL,
            productive_host_entry=CANONICAL_PRODUCTIVE_HOST_ENTRY,
            n1_consumer_result=record,
            disposition=str(cycle.disposition),
            post_count=int(cycle.post_count),
            permit_created=bool(cycle.permit_created),
            external_effect_count=int(cycle.external_effect_count),
            cap61_state_root_bound=False,
            host_join_addressed=True,
            host_join_invoked=False,
            host_enabled=False,
            selected_future_present=True,
            instrument_binding_valid=True,
            n1_consumer_join_ready=True,
        )
    return projections


def compose_occupied_lane_n1_host_join_readiness_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    **kwargs: Any,
) -> dict[str, OccupiedLaneN1HostJoinReadinessProjectionV1]:
    """Invoke N1 consumer then address host-join params. Stops before host join."""
    _assert_non_authority()
    forbidden = sorted(set(kwargs) & FORBIDDEN_COMPOSE_KWARGS)
    if forbidden:
        _fail(FAILURE_FORBIDDEN_KWARG, ",".join(forbidden))
    origin_main_sha = str(kwargs.get("origin_main_sha") or "").strip()
    cycle_id_prefix = str(kwargs.get("cycle_id_prefix") or "").strip()
    consumer_results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        composed_pairs,
        **kwargs,
    )
    return address_occupied_lane_n1_consumer_to_host_join_seam_v1(
        composed_pairs,
        consumer_results,
        origin_main_sha=origin_main_sha,
        cycle_id_prefix=cycle_id_prefix,
    )


def assert_readiness_stops_before_owner_boundary_v1(
    projections: Mapping[str, OccupiedLaneN1HostJoinReadinessProjectionV1],
) -> None:
    """Fail closed if a projection would cross the first true owner boundary."""
    _assert_non_authority()
    for lane_id, projection in projections.items():
        if (
            projection.host_join_invoked
            or projection.host_enabled
            or not projection.host_join_addressed
            or not projection.n1_consumer_join_ready
            or projection.post_count != 0
            or projection.permit_created
            or projection.external_effect_count != 0
            or projection.host_join_owner != CANONICAL_HOST_JOIN_OWNER
            or projection.host_join_symbol != CANONICAL_HOST_JOIN_SYMBOL
            or projection.disposition not in _SUCCESS_DISPOSITIONS
        ):
            _fail(FAILURE_OWNER_BOUNDARY, lane_id)
        if HOST_JOIN or MF_PRODUCTIVE_JOIN or PRODUCTIVE_RUNTIME_CARDINALITY != "1_UNJOINED":
            _fail(FAILURE_OWNER_BOUNDARY, lane_id)
