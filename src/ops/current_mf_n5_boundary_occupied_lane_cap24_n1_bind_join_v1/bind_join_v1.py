"""Boundary join from occupied-lane Cap23 SSF map to isolated Cap 2.4 N=1 bind.

Sequences existing Cap 2.4 once per occupied lane_state_root. Does not
reinvoke Cap 2.3, trade, or join a productive host. Does not own Cap 2.4
semantics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
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
    FAILURE_SELECTION_TYPE,
    FAILURE_UNKNOWN_LANE_ID,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    HOST_JOIN,
    INSTRUMENT_ID_ALONE_SUFFICIENT,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
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
    UNIVERSE_ISOLATION_ENFORCED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    lane_state_root_for,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    assert_handoff_invariants_v1,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class BoundaryOccupiedLaneCap24BindJoinError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: str, detail: str = "") -> NoReturn:
    raise BoundaryOccupiedLaneCap24BindJoinError(code, detail)


def _assert_non_authority() -> None:
    if (
        JOIN_SELECTION_AUTHORITY
        or JOIN_CAP23_SELECTION_AUTHORITY
        or JOIN_CAP24_BINDING_AUTHORITY
        or JOIN_TRADING_AUTHORITY
        or JOIN_RUNTIME_ACTIVATION_AUTHORITY
        or JOIN_EXECUTION_AUTHORITY
        or JOIN_RANKING_AUTHORITY
        or JOIN_MEMBERSHIP_AUTHORITY
        or JOIN_MAPPING_AUTHORITY
        or JOIN_PERSISTENCE_AUTHORITY
        or HOST_JOIN
        or CAP23_CHANGE_REQUIRED
        or CAP24_CHANGE_REQUIRED
        or MASTER_V2_CHANGE_REQUIRED
        or DOUBLE_PLAY_CHANGE_REQUIRED
        or MF_PRODUCTIVE_JOIN
        or FIVE_LANE_RUNTIME_CREATED
        or FIVE_LANE_CONTINUOUS_HOST_JOIN
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or PARALLEL_AUTHORITY_CREATED
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


def bind_occupied_lane_cap24_n1_instruments_v1(
    *,
    selections: Mapping[str, SingleSelectedFutureSelectionV1],
    topology_state_root_base: Path | str,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    observed_portfolio: PortfolioTruthSnapshotV1,
    mark_price_by_native_id: Mapping[str, Any],
    repository_sha: str,
    session_id: str,
    now_unix: float,
) -> dict[str, BoundInstrumentV1]:
    """Join occupied-lane Cap23 SSF map to isolated Cap 2.4 N=1 bind. Stop there."""
    _assert_non_authority()
    unknown = sorted(set(selections) - set(LANE_IDS))
    if unknown:
        _fail(FAILURE_UNKNOWN_LANE_ID, ",".join(unknown))

    bound_by_lane: dict[str, BoundInstrumentV1] = {}
    for lane_id in LANE_IDS:
        selection = selections.get(lane_id)
        if selection is None:
            continue
        if not isinstance(selection, SingleSelectedFutureSelectionV1):
            _fail(FAILURE_SELECTION_TYPE, lane_id)
        selection_state_root = Path(
            lane_state_root_for(
                topology_state_root_base=topology_state_root_base,
                lane_id=lane_id,
            )
        )
        gate = run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=selection_state_root,
            ranking_state_root=Path(ranking_state_root),
            universe_state_root=Path(universe_state_root),
            repository_sha=repository_sha,
            session_id=session_id,
            now_unix=now_unix,
            reconciliation_state_root=Path(reconciliation_state_root),
            observed_portfolio=observed_portfolio,
            expected_selection_config_digest=selection.config_digest,
            expected_selection_integrity_digest=selection.integrity_digest,
            mark_price_by_native_id=mark_price_by_native_id,
            skip_reconciliation=False,
        )
        if gate.ok is True and isinstance(gate.bound, BoundInstrumentV1):
            assert_handoff_invariants_v1(
                selection,
                gate.bound,
                ranking_snapshot_id=gate.bound.ranking_snapshot_id,
                ranking_universe_snapshot_id=gate.bound.universe_snapshot_id,
                universe_snapshot_id=gate.bound.universe_snapshot_id,
            )
            bound_by_lane[lane_id] = gate.bound
    return bound_by_lane
