"""Admit already-bound occupied-lane instruments into Full Autonomy ingest.

Identity-preserving map consume. Does not rebind, rank, select, or trade.
"""

from __future__ import annotations

from typing import Mapping, NoReturn

from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.constants_v1 import (
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
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    HOST_JOIN,
    IDENTITY_PRESERVING_INGEST,
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
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class FullAutonomyOccupiedLaneBoundIngestJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise FullAutonomyOccupiedLaneBoundIngestJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        not S2_IMPLEMENTED
        or not IDENTITY_PRESERVING_INGEST
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


def admit_occupied_lane_bound_instruments_v1(
    bound_by_lane: Mapping[str, BoundInstrumentV1],
) -> dict[str, BoundInstrumentV1]:
    """Admit the #6598 bound map. Stop at identity-preserving admitted dict."""
    _assert_non_authority()
    unknown = sorted(set(bound_by_lane) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))

    admitted: dict[str, BoundInstrumentV1] = {}
    for lane_id in LANE_IDS:
        bound = bound_by_lane.get(lane_id)
        if bound is None:
            continue
        if not isinstance(bound, BoundInstrumentV1):
            _fail(FAILURE_BOUND_TYPE, lane_id)
        admitted[lane_id] = bound
    return admitted
