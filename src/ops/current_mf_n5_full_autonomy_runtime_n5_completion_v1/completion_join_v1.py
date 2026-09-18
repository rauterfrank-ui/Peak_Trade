"""CURRENT MF N=5 Full-Autonomy runtime completion.

Consumes occupied-lane N1 host-join readiness, invokes canonical
ensure_host_activation_binding_v1 per occupied lane under lane-local Cap 7.2
activation roots, and rolls productive cardinality 1_JOINED→5_JOINED.
Does not mint permits, POST, join the live execution port, or rewrite
Cap23/Cap24/MV2/Double Play.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.readiness_join_v1 import (
    OccupiedLaneN1HostJoinReadinessProjectionV1,
    compose_occupied_lane_n1_host_join_readiness_v1,
)
from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    ATOMICITY_CLAIMED_SATISFIED,
    AUTHORITY_WORK_REMAINING,
    CANONICAL_HOST_JOIN_OWNER,
    CANONICAL_HOST_JOIN_SYMBOL,
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
    EXECUTION_SCHEDULE,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_AUTHORITY,
    FAILURE_CARDINALITY,
    FAILURE_EXTERNAL_EFFECT,
    FAILURE_FORBIDDEN_KWARG,
    FAILURE_HOST_JOIN,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_LANE_STATE_ROOT,
    FAILURE_LIVE_PORT,
    FAILURE_NATIVE_ID_MISSING,
    FAILURE_OCCUPANCY,
    FAILURE_ORIGIN_MAIN_SHA,
    FAILURE_RESULT_MISSING,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_COMPOSE_KWARGS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    FULL_AUTONOMY_TRADING_DECISION_AUTHORITY,
    GLOBAL_N1_CURSOR_REJECTED,
    HOST_ACTIVATION_DIRNAME,
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
    MAX_POSITIONS_EFFECTIVE,
    MAX_PRODUCTIVE_OCCUPIED_LANES,
    MAY_BIND_CAP61_STATE_ROOT,
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
    N1_CONSUMER_JOIN_READY,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    N5_MODEL,
    NEW_CURSOR_WRITER,
    NEW_HOST_OWNER_CREATED,
    OCCUPIED_LANES_ONLY,
    OWNER,
    PARALLEL_AUTHORITY_CREATED,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    READINESS_CHANGE_REQUIRED,
    RUNTIME_N5_ARCHITECTURE_COMPLETE,
    TECHNICAL_WORK_REMAINING,
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
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
    ensure_host_activation_binding_v1,
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


class FullAutonomyRuntimeN5CompletionError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class OccupiedLaneN5JoinedHostV1:
    lane_id: str
    bound_instrument: BoundInstrumentV1
    native_id: str
    instrument_id: str
    lane_state_root: str
    host_activation_root: str
    cursor_store_root: str
    lock_root: str
    evidence_root: str
    origin_main_sha: str
    writer_session_id: str
    host_join_owner: str
    host_join_symbol: str
    disposition: str
    post_count: int
    permit_created: bool
    external_effect_count: int
    cap61_state_root_bound: bool
    host_join_addressed: bool
    host_join_invoked: bool
    host_enabled: bool
    host_gate_ok: bool
    host_alpha_blocked: bool
    host_live_execution_port_present: bool
    selected_future_present: bool
    instrument_binding_valid: bool


@dataclass(frozen=True)
class OccupiedLaneRuntimeN5CompletionResultV1:
    joined_lanes: dict[str, OccupiedLaneN5JoinedHostV1]
    occupied_count: int
    productive_runtime_cardinality: str
    host_join: bool
    mf_productive_join: bool
    max_positions_effective: int
    multi_future_runtime_authorized: bool
    execution_concurrency_authorized: bool
    execution_schedule: str
    external_effect_authorized: bool
    post_count: int
    permit_created: bool
    runtime_n5_architecture_complete: bool


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyRuntimeN5CompletionError(code, detail)


def cardinality_joined_token_v1(occupied_count: int) -> str:
    if occupied_count < 1 or occupied_count > MAX_PRODUCTIVE_OCCUPIED_LANES:
        _fail(FAILURE_CARDINALITY, str(occupied_count))
    return f"{int(occupied_count)}_JOINED"


def lane_host_activation_root_v1(lane_state_root: str) -> str:
    root = lane_state_root_key(lane_state_root)
    if not root:
        _fail(FAILURE_LANE_STATE_ROOT, "empty")
    return str(Path(root) / HOST_ACTIVATION_DIRNAME)


def occupied_lane_runtime_n5_completion_census_v1() -> dict[str, str]:
    """Reuse census for host/runtime/cursor/lock owners and N=5 target."""
    return {
        "CANONICAL_HOST_JOIN_OWNER": CANONICAL_HOST_JOIN_OWNER,
        "CANONICAL_HOST_JOIN_SYMBOL": CANONICAL_HOST_JOIN_SYMBOL,
        "CANONICAL_RUNTIME_OWNER": "ops.single_future_stateful_no_order_runtime_activation_v1",
        "READINESS_JOIN_SYMBOL": "compose_occupied_lane_n1_host_join_readiness_v1",
        "CURSOR_OWNER": (
            "ops.full_core_live_path_composition_root_v1."
            "current_productive_sidestate_confirmation_cursor_v1"
        ),
        "LOCKING_MODEL": "AuthorizationLifecycleLockV1.CYCLE_EXCLUSION_LOCK",
        "EXECUTION_SCHEDULE": EXECUTION_SCHEDULE,
        "PRODUCTIVE_RUNTIME_CARDINALITY": PRODUCTIVE_RUNTIME_CARDINALITY,
        "N5_MODEL": N5_MODEL,
        "ATLAS_AUTHORITY": ATLAS_AUTHORITY,
        "FIRST_UNAUTHORIZED_REMAINING_BOUNDARY": ("EXTERNAL_EFFECT_LIVE_TRADING_OWNER_GO"),
        "AUTHORITY_WORK_REMAINING": AUTHORITY_WORK_REMAINING,
        "TECHNICAL_WORK_REMAINING": TECHNICAL_WORK_REMAINING,
    }


def _assert_completion_authority() -> None:
    if (
        not JOIN_IMPLEMENTED
        or not N1_CONSUMER_JOIN_READY
        or not HOST_JOIN_ADDRESSED
        or not HOST_JOIN_INVOKED
        or not MAY_INVOKE_HOST_JOIN
        or not MAY_ENABLE_HOST
        or MAY_JOIN_CAP72_LIVE_EXECUTION_PORT
        or MAY_INVOKE_PRODUCTIVE_HOST_ENTRY
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
        or FULL_AUTONOMY_TRADING_DECISION_AUTHORITY
        or not HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or FULL_AUTONOMY_HOST_CHANGE_REQUIRED
        or CURSOR_OWNER_CHANGE_REQUIRED
        or N1_CONSUMER_CHANGE_REQUIRED
        or READINESS_CHANGE_REQUIRED
        or not MF_PRODUCTIVE_JOIN
        or not FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or EXECUTION_CONCURRENCY_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
        or THIS_SLICE_MAY_REINVOKE_CAP23
        or THIS_SLICE_MAY_REINVOKE_CAP24
        or MAY_BIND_CAP61_STATE_ROOT
        or PRODUCTIVE_RUNTIME_CARDINALITY != "5_JOINED"
        or MAX_POSITIONS_EFFECTIVE != 1
        or not UNIVERSE_ISOLATION_ENFORCED
        or not RUNTIME_N5_ARCHITECTURE_COMPLETE
        or TECHNICAL_WORK_REMAINING != "NONE"
        or ATOMICITY_CLAIMED_SATISFIED
        or ATLAS_AUTHORITY != "NONE"
        or N5_MODEL != "FIVE_ISOLATED_N1_LANES"
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


def join_occupied_lane_host_activation_v1(
    projections: Mapping[str, OccupiedLaneN1HostJoinReadinessProjectionV1],
) -> dict[str, OccupiedLaneN5JoinedHostV1]:
    """Invoke canonical host join per occupied-lane readiness projection.

    Sequential in LANE_IDS order. Does not join the live execution port.
    """
    _assert_completion_authority()
    unknown = sorted(set(projections) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    joined: dict[str, OccupiedLaneN5JoinedHostV1] = {}
    seen_roots: dict[str, str] = {}
    for lane_id in LANE_IDS:
        projection = projections.get(lane_id)
        if projection is None:
            continue
        if not isinstance(projection, OccupiedLaneN1HostJoinReadinessProjectionV1):
            _fail(FAILURE_RESULT_MISSING, lane_id)
        native_id = str(projection.native_id or "").strip()
        if not native_id:
            _fail(FAILURE_NATIVE_ID_MISSING, lane_id)
        bound = projection.bound_instrument
        if not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        if str(bound.venue_native_id or "").strip() != native_id:
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        if str(projection.instrument_id or "").strip() != str(bound.instrument_id):
            _fail(FAILURE_IDENTITY_MISMATCH, lane_id)
        if projection.host_join_owner != CANONICAL_HOST_JOIN_OWNER:
            _fail(FAILURE_AUTHORITY, lane_id)
        if projection.host_join_symbol != CANONICAL_HOST_JOIN_SYMBOL:
            _fail(FAILURE_AUTHORITY, lane_id)
        if not projection.host_join_addressed or not projection.n1_consumer_join_ready:
            _fail(FAILURE_AUTHORITY, lane_id)
        if int(projection.post_count) != 0 or projection.permit_created is not False:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if int(projection.external_effect_count) != 0:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if projection.cap61_state_root_bound is not False:
            _fail(FAILURE_AUTHORITY, "cap61_bound")
        if projection.disposition not in _SUCCESS_DISPOSITIONS:
            _fail(FAILURE_AUTHORITY, projection.disposition)
        lane_state_root = lane_state_root_key(projection.lane_state_root)
        if not lane_state_root:
            _fail(FAILURE_LANE_STATE_ROOT, lane_id)
        _reject_n1_global_root(lane_state_root, lane_id)
        _reject_n1_global_root(projection.cursor_store_root, lane_id)
        _reject_n1_global_root(projection.lock_root, lane_id)
        _reject_n1_global_root(projection.evidence_root, lane_id)
        activation_root = lane_host_activation_root_v1(lane_state_root)
        _reject_n1_global_root(activation_root, lane_id)
        for role, root in (
            ("cursor", projection.cursor_store_root),
            ("lock", projection.lock_root),
            ("evidence", projection.evidence_root),
            ("activation", activation_root),
        ):
            prior = seen_roots.get(root)
            if prior is not None:
                _fail(FAILURE_LANE_STATE_ROOT, f"{prior},{lane_id}:{role}")
            seen_roots[root] = f"{lane_id}:{role}"
        sha = str(projection.origin_main_sha or "").strip()
        if not sha:
            _fail(FAILURE_ORIGIN_MAIN_SHA, lane_id)
        binding = HostActivationBindingV1(enabled=True)
        if binding.live_execution_port is not None:
            _fail(FAILURE_LIVE_PORT, lane_id)
        gate = ensure_host_activation_binding_v1(
            binding,
            instrument_id=str(bound.instrument_id),
            repository_sha=sha,
            state_root=Path(activation_root),
            writer_session_id=str(projection.writer_session_id),
            selected_future_present=bool(projection.selected_future_present),
            instrument_binding_valid=bool(projection.instrument_binding_valid),
            persist=True,
        )
        if binding.live_execution_port is not None:
            _fail(FAILURE_LIVE_PORT, lane_id)
        if not gate.ok or gate.alpha_blocked:
            blockers = ",".join(str(item) for item in gate.blockers) or "host_join_not_ok"
            _fail(FAILURE_HOST_JOIN, f"{lane_id}:{blockers}")
        joined[lane_id] = OccupiedLaneN5JoinedHostV1(
            lane_id=lane_id,
            bound_instrument=bound,
            native_id=native_id,
            instrument_id=str(bound.instrument_id),
            lane_state_root=lane_state_root,
            host_activation_root=activation_root,
            cursor_store_root=projection.cursor_store_root,
            lock_root=projection.lock_root,
            evidence_root=projection.evidence_root,
            origin_main_sha=sha,
            writer_session_id=str(projection.writer_session_id),
            host_join_owner=CANONICAL_HOST_JOIN_OWNER,
            host_join_symbol=CANONICAL_HOST_JOIN_SYMBOL,
            disposition=str(projection.disposition),
            post_count=int(projection.post_count),
            permit_created=bool(projection.permit_created),
            external_effect_count=int(projection.external_effect_count),
            cap61_state_root_bound=False,
            host_join_addressed=True,
            host_join_invoked=True,
            host_enabled=True,
            host_gate_ok=True,
            host_alpha_blocked=bool(gate.alpha_blocked),
            host_live_execution_port_present=binding.live_execution_port is not None,
            selected_future_present=True,
            instrument_binding_valid=True,
        )
    return joined


def run_occupied_lane_runtime_n5_completion_v1(
    composed_pairs: Mapping[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
    *,
    target_cardinality: int,
    **kwargs: Any,
) -> OccupiedLaneRuntimeN5CompletionResultV1:
    """Readiness compose + canonical host join for exactly target_cardinality lanes."""
    _assert_completion_authority()
    forbidden = sorted(set(kwargs) & FORBIDDEN_COMPOSE_KWARGS)
    if forbidden:
        _fail(FAILURE_FORBIDDEN_KWARG, ",".join(forbidden))
    target = int(target_cardinality)
    if target < 1 or target > MAX_PRODUCTIVE_OCCUPIED_LANES:
        _fail(FAILURE_CARDINALITY, str(target))
    unknown = sorted(set(composed_pairs) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))
    occupied_ids: list[str] = []
    for lane_id in LANE_IDS:
        pair = composed_pairs.get(lane_id)
        if pair is None:
            continue
        if not isinstance(pair, tuple) or len(pair) != 2:
            _fail(FAILURE_OCCUPANCY, lane_id)
        slot, bound = pair
        if not isinstance(slot, IsolatedLaneSlotV1) or not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_OCCUPANCY, lane_id)
        if slot.occupancy != OCCUPANCY_OCCUPIED:
            _fail(FAILURE_OCCUPANCY, lane_id)
        occupied_ids.append(lane_id)
    if len(occupied_ids) != target:
        _fail(FAILURE_CARDINALITY, f"{len(occupied_ids)}!={target}")
    origin_main_sha = str(kwargs.get("origin_main_sha") or "").strip()
    if not origin_main_sha:
        _fail(FAILURE_ORIGIN_MAIN_SHA, OWNER)
    projections = compose_occupied_lane_n1_host_join_readiness_v1(composed_pairs, **kwargs)
    if set(projections) != set(occupied_ids):
        _fail(FAILURE_CARDINALITY, ",".join(sorted(projections)))
    joined = join_occupied_lane_host_activation_v1(projections)
    if set(joined) != set(occupied_ids):
        _fail(FAILURE_CARDINALITY, ",".join(sorted(joined)))
    post_count = 0
    permit_created = False
    for lane_id in occupied_ids:
        record = joined[lane_id]
        post_count += int(record.post_count)
        permit_created = permit_created or bool(record.permit_created)
        if int(record.external_effect_count) != 0:
            _fail(FAILURE_EXTERNAL_EFFECT, lane_id)
        if record.host_live_execution_port_present:
            _fail(FAILURE_LIVE_PORT, lane_id)
    if post_count != 0 or permit_created:
        _fail(FAILURE_EXTERNAL_EFFECT, OWNER)
    return OccupiedLaneRuntimeN5CompletionResultV1(
        joined_lanes=joined,
        occupied_count=target,
        productive_runtime_cardinality=cardinality_joined_token_v1(target),
        host_join=True,
        mf_productive_join=True,
        max_positions_effective=int(MAX_POSITIONS_EFFECTIVE),
        multi_future_runtime_authorized=False,
        execution_concurrency_authorized=False,
        execution_schedule=EXECUTION_SCHEDULE,
        external_effect_authorized=False,
        post_count=0,
        permit_created=False,
        runtime_n5_architecture_complete=bool(target == MAX_PRODUCTIVE_OCCUPIED_LANES),
    )
