"""S2 typed compose tests for Full-Autonomy occupied-lane MV2/DP handoff."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
    PREPARED_BOUND_CARDINALITY as BOUNDARY_PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY as BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.constants_v1 import (
    OWNER as INGEST_OWNER,
    S2_JOIN_SYMBOL as INGEST_S2_JOIN_SYMBOL,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1 import (
    constants_v1 as handoff_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.constants_v1 import (
    ADMITTED_MAP_PRODUCER_OWNER,
    AUTHORITY_EFFECT,
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_BINDING_OWNER,
    CAP24_CHANGE_REQUIRED,
    CONTRACT_ID,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_BOUND_TYPE,
    FAILURE_IDENTITY_MISMATCH,
    FAILURE_OCCUPANCY,
    FAILURE_STATE_ROOT_MISMATCH,
    FAILURE_UNKNOWN_LANE_ID,
    FIRST_TRADING_DECISION_CONSUMER,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    FULL_AUTONOMY_HOST_OWNER,
    HANDOFF_ADMITTED_INPUT_OBJECT,
    HANDOFF_ADMITTED_INPUT_PRODUCER,
    HANDOFF_CONSUMER_OWNER,
    HANDOFF_EGRESS_OBJECT,
    HANDOFF_SLOT_TYPE,
    HANDOFF_TOPOLOGY_INPUT_TYPE,
    HOST_JOIN,
    IDENTITY_PRESERVING_HANDOFF,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    LAST_RANKING_UNIVERSE_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    MV2_DP_INGRESS_TYPE,
    NEW_COLLECTION_DTO_CREATED,
    NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED,
    NEW_MV2_DP_INGRESS_DTO_CREATED,
    NEW_TOP5_HANDOFF_DTO_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PARALLEL_AUTHORITY_CREATED,
    PICK_ONE_AMONG_PREPARED_BOUNDS,
    PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RUNTIME_AUTHORIZATION_EFFECT,
    S2_IMPLEMENTED,
    S2_JOIN_SYMBOL,
    SLICE_ID,
    SLOT_IDENTITY,
    SLOT_STATE_ROOT_RESOLVER,
    THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT,
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    THIS_SLICE_MAY_RESTORE_CURSOR,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpHandoffJoinError,
    compose_occupied_lane_mv2_dp_handoff_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1 import (
    constants_v1 as topology_constants,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    LANE_IDS,
    OCCUPANCY_EMPTY,
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    IsolatedLaneTopologyV1,
    lane_state_root_for,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    FIRST_TRADING_DECISION_CONSUMER as HANDOFF_FIRST_TRADING_DECISION_CONSUMER,
    FULL_CORE_INGEST_OBJECT,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
    OWNER as CAP23_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
    OWNER as CAP24_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

PACKAGE_DIR = Path(handoff_constants.__file__).resolve().parent
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "handoff_join_v1.py").read_text(encoding="utf-8")
UNIVERSE_SNAPSHOT = "uni-shared"
RANKING_SNAPSHOT = "rank-shared"
RANKING_DIGEST = "rank-digest-shared"


def _import_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(alias.name for alias in node.names)
    return names


def _bound(*, lane_id: str, instrument_id: str | None = None) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=instrument_id or f"INST-{lane_id}",
        venue_native_id=f"VENUE-{lane_id[-1]}",
        ranking_snapshot_id=RANKING_SNAPSHOT,
        ranking_integrity_digest=RANKING_DIGEST,
        universe_snapshot_id=UNIVERSE_SNAPSHOT,
        selection_id=f"sel-{lane_id}",
        selection_integrity_digest=f"sel-digest-{lane_id}",
        selection_state="SELECTED",
    )


def _slot(
    *,
    lane_id: str,
    topology_state_root_base: Path,
    bound: BoundInstrumentV1 | None = None,
    occupancy: str | None = None,
    lane_state_root: str | None = None,
) -> IsolatedLaneSlotV1:
    occupied = bound is not None
    return IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=occupancy or (OCCUPANCY_OCCUPIED if occupied else OCCUPANCY_EMPTY),
        canonical_instrument_id=None if bound is None else bound.instrument_id,
        lane_state_root=lane_state_root
        or lane_state_root_for(topology_state_root_base=topology_state_root_base, lane_id=lane_id),
        universe_snapshot_id=None if bound is None else bound.universe_snapshot_id,
        ranking_snapshot_id=None if bound is None else bound.ranking_snapshot_id,
        ranking_integrity_digest=None if bound is None else bound.ranking_integrity_digest,
    )


def _topology(
    tmp_path: Path,
    occupied: dict[str, BoundInstrumentV1] | None = None,
    *,
    slot_overrides: dict[str, IsolatedLaneSlotV1] | None = None,
) -> IsolatedLaneTopologyV1:
    occupied = occupied or {}
    overrides = slot_overrides or {}
    topology_state_root_base = str(Path(tmp_path).expanduser().resolve())
    slots = []
    for lane_id in LANE_IDS:
        if lane_id in overrides:
            slots.append(overrides[lane_id])
            continue
        slots.append(
            _slot(
                lane_id=lane_id,
                topology_state_root_base=topology_state_root_base,
                bound=occupied.get(lane_id),
            )
        )
    occupied_ids = tuple(
        str(slot.canonical_instrument_id) for slot in slots if slot.occupancy == OCCUPANCY_OCCUPIED
    )
    return IsolatedLaneTopologyV1(
        schema_version=topology_constants.SCHEMA_VERSION,
        owner=topology_constants.OWNER,
        contract_id=topology_constants.CONTRACT_ID,
        topology_state_root_base=topology_state_root_base,
        membership_instance_id="membership-s2",
        universe_snapshot_id=UNIVERSE_SNAPSHOT,
        ranking_snapshot_id=RANKING_SNAPSHOT,
        ranking_integrity_digest=RANKING_DIGEST,
        slots=tuple(slots),
        occupied_count=len(occupied_ids),
        occupied_instrument_ids=occupied_ids,
        lane_identity_encodes_rank=False,
        no_padding=True,
        one_instrument_per_lane=True,
        one_lane_per_instrument=True,
        pure_rank_reorder_causes_lane_move=False,
        mf_productive_join=False,
        five_lane_runtime_created=False,
        max_positions_effective=1,
        initial_assignment_policy=topology_constants.INITIAL_ASSIGNMENT_POLICY,
        retained_member_policy=topology_constants.RETAINED_MEMBER_POLICY,
        exit_policy=topology_constants.EXIT_POLICY,
        entry_policy=topology_constants.ENTRY_POLICY,
        free_lane_assignment_policy=topology_constants.FREE_LANE_ASSIGNMENT_POLICY,
        restart_reconstruction_policy=topology_constants.RESTART_RECONSTRUCTION_POLICY,
    )


def test_s2_authority_flags_and_consumer_bind() -> None:
    assert SLICE_ID == "S2_TYPED_COMPOSE_JOIN"
    assert OWNER == "ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1"
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_HANDOFF_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_HANDOFF_JOIN_V1_S2_TYPED_COMPOSE_JOIN"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert HANDOFF_CONSUMER_OWNER == OWNER
    assert ADMITTED_MAP_PRODUCER_OWNER == INGEST_OWNER
    assert HANDOFF_ADMITTED_INPUT_PRODUCER == INGEST_S2_JOIN_SYMBOL
    assert HANDOFF_ADMITTED_INPUT_OBJECT == "dict[lane_id, BoundInstrumentV1]"
    assert HANDOFF_TOPOLOGY_INPUT_TYPE == IsolatedLaneTopologyV1.__name__
    assert HANDOFF_SLOT_TYPE == IsolatedLaneSlotV1.__name__
    assert HANDOFF_EGRESS_OBJECT == "dict[lane_id, (IsolatedLaneSlotV1, BoundInstrumentV1)]"
    assert MV2_DP_INGRESS_TYPE == FULL_CORE_INGEST_OBJECT == "BoundInstrumentV1"
    assert SLOT_IDENTITY == "lane_id"
    assert SLOT_STATE_ROOT_RESOLVER == lane_state_root_for.__name__
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
    assert CAP24_BINDING_OWNER == CAP24_OWNER
    assert LAST_RANKING_UNIVERSE_AUTHORITY.endswith("SINGLE_SELECTED_FUTURE_POLICY_V1")
    assert FIRST_TRADING_DECISION_CONSUMER == HANDOFF_FIRST_TRADING_DECISION_CONSUMER
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
    assert THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT is False
    assert THIS_SLICE_MAY_RESTORE_CURSOR is False
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert PARALLEL_AUTHORITY_CREATED is False
    assert PICK_ONE_AMONG_PREPARED_BOUNDS is False
    assert IDENTITY_PRESERVING_HANDOFF is True
    assert NEW_COLLECTION_DTO_CREATED is False
    assert NEW_TOP5_HANDOFF_DTO_CREATED is False
    assert NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED is False
    assert NEW_MV2_DP_INGRESS_DTO_CREATED is False
    assert HOST_JOIN is False
    assert FULL_AUTONOMY_HOST_OWNER == "stateful_no_order_host_join_v1"
    assert MF_PRODUCTIVE_JOIN is False
    assert FIVE_LANE_RUNTIME_CREATED is False
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MF_SINGLE_EGRESS_REWIRED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CAP23_CHANGE_REQUIRED is False
    assert CAP24_CHANGE_REQUIRED is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert DOUBLE_PLAY_CHANGE_REQUIRED is False
    assert FULL_AUTONOMY_HOST_CHANGE_REQUIRED is False
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    assert PREPARED_BOUND_CARDINALITY == BOUNDARY_PREPARED_BOUND_CARDINALITY == "0..5"
    assert PRODUCTIVE_RUNTIME_CARDINALITY == BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"


def test_s2_reuses_existing_lane_ids_and_lane_state_root_for(tmp_path: Path) -> None:
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert list(LANE_IDS) == ["LANE_1", "LANE_2", "LANE_3", "LANE_4", "LANE_5"]
    for lane_id in LANE_IDS:
        resolved = lane_state_root_for(
            topology_state_root_base=tmp_path,
            lane_id=lane_id,
        )
        assert resolved == str(tmp_path / lane_id)


def test_s2_join_is_implemented() -> None:
    assert S2_JOIN_SYMBOL == "compose_occupied_lane_mv2_dp_handoff_v1"
    assert S2_IMPLEMENTED is True
    assert (PACKAGE_DIR / "handoff_join_v1.py").is_file()
    handoff_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1",
        fromlist=["*"],
    )
    assert getattr(handoff_pkg, S2_JOIN_SYMBOL) is compose_occupied_lane_mv2_dp_handoff_v1
    assert callable(compose_occupied_lane_mv2_dp_handoff_v1)
    assert compose_occupied_lane_mv2_dp_handoff_v1.__name__ == S2_JOIN_SYMBOL
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE


def test_t_empty_returns_empty_dict(tmp_path: Path) -> None:
    composed = compose_occupied_lane_mv2_dp_handoff_v1({}, _topology(tmp_path))
    assert composed == {}
    assert list(composed) == []


def test_t_one_occupied_admitted_returns_exact_pair(tmp_path: Path) -> None:
    original = _bound(lane_id="LANE_3")
    topology = _topology(tmp_path, {"LANE_3": original})
    composed = compose_occupied_lane_mv2_dp_handoff_v1({"LANE_3": original}, topology)
    assert list(composed) == ["LANE_3"]
    slot, bound = composed["LANE_3"]
    assert bound is original
    assert slot is topology.slots[2]
    assert slot.lane_id == "LANE_3"
    assert slot.occupancy == OCCUPANCY_OCCUPIED
    assert slot.lane_state_root == lane_state_root_for(
        topology_state_root_base=tmp_path, lane_id="LANE_3"
    )


def test_t_occupied_without_admitted_is_omitted(tmp_path: Path) -> None:
    occupied = {
        "LANE_1": _bound(lane_id="LANE_1"),
        "LANE_4": _bound(lane_id="LANE_4"),
    }
    topology = _topology(tmp_path, occupied)
    composed = compose_occupied_lane_mv2_dp_handoff_v1(
        {"LANE_4": occupied["LANE_4"]},
        topology,
    )
    assert list(composed) == ["LANE_4"]
    assert composed["LANE_4"][1] is occupied["LANE_4"]
    assert "LANE_1" not in composed


def test_t_multi_up_to_5_follows_lane_ids_order(tmp_path: Path) -> None:
    originals = {lane_id: _bound(lane_id=lane_id) for lane_id in LANE_IDS}
    topology = _topology(tmp_path, originals)
    admitted = {
        "LANE_5": originals["LANE_5"],
        "LANE_1": originals["LANE_1"],
        "LANE_4": originals["LANE_4"],
        "LANE_2": originals["LANE_2"],
        "LANE_3": originals["LANE_3"],
    }
    composed = compose_occupied_lane_mv2_dp_handoff_v1(admitted, topology)
    assert list(composed) == list(LANE_IDS)
    for lane_id in LANE_IDS:
        slot, bound = composed[lane_id]
        assert bound is originals[lane_id]
        assert slot.lane_id == lane_id
        assert slot.lane_state_root == lane_state_root_for(
            topology_state_root_base=tmp_path, lane_id=lane_id
        )


def test_t_unknown_lane_fails_closed(tmp_path: Path) -> None:
    original = _bound(lane_id="LANE_1")
    topology = _topology(tmp_path, {"LANE_1": original})
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpHandoffJoinError) as exc:
        compose_occupied_lane_mv2_dp_handoff_v1(
            {"LANE_1": original, "LANE_X": original},
            topology,
        )
    assert exc.value.failure_code == FAILURE_UNKNOWN_LANE_ID
    assert "LANE_X" in exc.value.detail


def test_t_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    slot_bound = _bound(lane_id="LANE_2")
    admitted_bound = _bound(lane_id="LANE_2", instrument_id="INST-OTHER")
    topology = _topology(tmp_path, {"LANE_2": slot_bound})
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpHandoffJoinError) as exc:
        compose_occupied_lane_mv2_dp_handoff_v1({"LANE_2": admitted_bound}, topology)
    assert exc.value.failure_code == FAILURE_IDENTITY_MISMATCH
    assert exc.value.detail == "LANE_2"


def test_t_state_root_mismatch_fails_closed(tmp_path: Path) -> None:
    original = _bound(lane_id="LANE_1")
    wrong_root = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_2")
    topology = _topology(
        tmp_path,
        slot_overrides={
            "LANE_1": _slot(
                lane_id="LANE_1",
                topology_state_root_base=tmp_path,
                bound=original,
                lane_state_root=wrong_root,
            )
        },
    )
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpHandoffJoinError) as exc:
        compose_occupied_lane_mv2_dp_handoff_v1({"LANE_1": original}, topology)
    assert exc.value.failure_code == FAILURE_STATE_ROOT_MISMATCH
    assert exc.value.detail == "LANE_1"


def test_bound_type_mismatch_fails_closed(tmp_path: Path) -> None:
    topology = _topology(tmp_path, {"LANE_1": _bound(lane_id="LANE_1")})
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpHandoffJoinError) as exc:
        compose_occupied_lane_mv2_dp_handoff_v1(
            {"LANE_1": object()},  # type: ignore[dict-item]
            topology,
        )
    assert exc.value.failure_code == FAILURE_BOUND_TYPE
    assert exc.value.detail == "LANE_1"


def test_t_admitted_empty_lane_fails_closed(tmp_path: Path) -> None:
    original = _bound(lane_id="LANE_5")
    topology = _topology(tmp_path)
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpHandoffJoinError) as exc:
        compose_occupied_lane_mv2_dp_handoff_v1({"LANE_5": original}, topology)
    assert exc.value.failure_code == FAILURE_OCCUPANCY
    assert exc.value.detail == "LANE_5"


def test_t_no_pick_one(tmp_path: Path) -> None:
    originals = {
        "LANE_2": _bound(lane_id="LANE_2"),
        "LANE_4": _bound(lane_id="LANE_4"),
        "LANE_5": _bound(lane_id="LANE_5"),
    }
    topology = _topology(tmp_path, originals)
    composed = compose_occupied_lane_mv2_dp_handoff_v1(originals, topology)
    assert PICK_ONE_AMONG_PREPARED_BOUNDS is False
    assert list(composed) == ["LANE_2", "LANE_4", "LANE_5"]
    assert set(composed) == set(originals)
    for lane_id, bound in originals.items():
        assert composed[lane_id][1] is bound


def test_t_no_cap23_cap24_reentry() -> None:
    for source in (JOIN_SOURCE, INIT_SOURCE):
        assert "produce_occupied_lane_cap23_n1_selections_v1" not in source
        assert "run_single_selected_future_policy_v1" not in source
        assert "produce_single_selected_future_v1" not in source
        assert "run_single_selected_future_runtime_binding_gate_v1" not in source
        assert "ensure_single_selected_future_runtime_binding_v1" not in source
        assert "_pick_top_eligible" not in source
    imported = (
        _import_names(JOIN_SOURCE) | _import_names(INIT_SOURCE) | _import_names(CONSTANTS_SOURCE)
    )
    assert "src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1" not in imported
    assert "src.ops.single_selected_future_policy_v1.producer_v1" not in imported
    assert (
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.ingest_join_v1"
        not in imported
    )


def test_t_no_mv2_dp_host_execution_graph() -> None:
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in INIT_SOURCE
        assert forbidden not in JOIN_SOURCE
    imported = (
        _import_names(JOIN_SOURCE) | _import_names(INIT_SOURCE) | _import_names(CONSTANTS_SOURCE)
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1"
        not in imported
    )
    assert "trading.master_v2.integrated_offline_trading_logic_replay_v1" not in imported
    assert "src.ops.full_core_live_path_composition_root_v1.composition_root_v1" not in imported
    assert "src.ops.stateful_no_order_host_join_v1" not in imported
    assert "src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1" not in (
        imported
    )
    tree = ast.parse(JOIN_SOURCE)
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert not (called & FORBIDDEN_CALL_GRAPH_TARGETS)
    assert inspect.getsource(compose_occupied_lane_mv2_dp_handoff_v1)
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False


def test_t_cap61_state_root_untouched() -> None:
    assert THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT is False
    assert THIS_SLICE_MAY_RESTORE_CURSOR is False
    assert "ensure_host_confirmation_binding_v1" not in JOIN_SOURCE
    assert "state_root=" not in JOIN_SOURCE
    assert "CurrentProductiveSideStateConfirmationCursorV1" not in JOIN_SOURCE
    assert "run_current_productive_master_v2_runtime_cycle_v1" not in JOIN_SOURCE
    assert "run_integrated_offline_trading_logic_replay_v1" not in JOIN_SOURCE
