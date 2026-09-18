"""S2 typed ingest tests for Full-Autonomy occupied-lane bound ingest."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
    OWNER as BOUNDARY_BIND_JOIN_OWNER_VALUE,
    PREPARED_BOUND_CARDINALITY as BOUNDARY_PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY as BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1 import (
    constants_v1 as ingest_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    BOUNDARY_BIND_JOIN_OWNER,
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_BINDING_OWNER,
    CAP24_CHANGE_REQUIRED,
    CONTRACT_ID,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_BOUND_TYPE,
    FAILURE_UNKNOWN_LANE_ID,
    FIRST_TRADING_DECISION_CONSUMER,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    FULL_AUTONOMY_HOST_OWNER,
    HOST_JOIN,
    IDENTITY_PRESERVING_INGEST,
    INGEST_INPUT_OBJECT,
    INGEST_INPUT_PRODUCER,
    INGEST_VALUE_TYPE_NAME,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    LAST_RANKING_UNIVERSE_AUTHORITY,
    MAP_CONSUMER_OWNER,
    MAP_CONSUMER_ROLE,
    MAP_PRODUCER_OWNER,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEW_COLLECTION_DTO_CREATED,
    NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED,
    NEW_TOP5_HANDOFF_DTO_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PARALLEL_AUTHORITY_CREATED,
    PICK_ONE_AMONG_PREPARED_BOUNDS,
    PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    S2_IMPLEMENTED,
    S2_JOIN_SYMBOL,
    SLICE_ID,
    SLOT_IDENTITY,
    SLOT_STATE_ROOT_RESOLVER,
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.ingest_join_v1 import (
    FullAutonomyOccupiedLaneBoundIngestJoinError,
    admit_occupied_lane_bound_instruments_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
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

PACKAGE_DIR = Path(ingest_constants.__file__).resolve().parent
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "ingest_join_v1.py").read_text(encoding="utf-8")


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


def _bound(*, lane_id: str) -> BoundInstrumentV1:
    suffix = lane_id[-1]
    return BoundInstrumentV1(
        instrument_id=f"INST-{lane_id}",
        venue_native_id=f"VENUE-{suffix}",
        ranking_snapshot_id=f"rank-{lane_id}",
        ranking_integrity_digest=f"rank-digest-{lane_id}",
        universe_snapshot_id=f"uni-{lane_id}",
        selection_id=f"sel-{lane_id}",
        selection_integrity_digest=f"sel-digest-{lane_id}",
        selection_state="SELECTED",
    )


def _assert_same_bound(left: BoundInstrumentV1, right: BoundInstrumentV1) -> None:
    assert left is right
    assert left.instrument_id == right.instrument_id
    assert left.venue_native_id == right.venue_native_id
    assert left.ranking_snapshot_id == right.ranking_snapshot_id
    assert left.ranking_integrity_digest == right.ranking_integrity_digest
    assert left.universe_snapshot_id == right.universe_snapshot_id
    assert left.selection_id == right.selection_id
    assert left.selection_integrity_digest == right.selection_integrity_digest
    assert left.selection_state == right.selection_state
    assert left.selected_future_count == right.selected_future_count == 1
    assert left.max_positions_effective == right.max_positions_effective == 1


def test_s2_authority_flags_and_consumer_bind() -> None:
    assert SLICE_ID == "S2_TYPED_INGEST_JOIN"
    assert OWNER == "ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1"
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_BOUND_INGEST_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_BOUND_INGEST_JOIN_V1_S2_TYPED_INGEST_JOIN"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert MAP_CONSUMER_ROLE == "FULL_AUTONOMY_INGEST"
    assert MAP_CONSUMER_OWNER == OWNER
    assert MAP_PRODUCER_OWNER == BOUNDARY_BIND_JOIN_OWNER == BOUNDARY_BIND_JOIN_OWNER_VALUE
    assert INGEST_INPUT_PRODUCER == "bind_occupied_lane_cap24_n1_instruments_v1"
    assert INGEST_INPUT_OBJECT == "dict[lane_id, BoundInstrumentV1]"
    assert INGEST_VALUE_TYPE_NAME == FULL_CORE_INGEST_OBJECT == "BoundInstrumentV1"
    assert INGEST_VALUE_TYPE_NAME == BoundInstrumentV1.__name__
    assert SLOT_IDENTITY == "lane_id"
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert SLOT_STATE_ROOT_RESOLVER == lane_state_root_for.__name__
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
    assert CAP24_BINDING_OWNER == CAP24_OWNER
    assert LAST_RANKING_UNIVERSE_AUTHORITY.endswith("SINGLE_SELECTED_FUTURE_POLICY_V1")
    assert FIRST_TRADING_DECISION_CONSUMER == HANDOFF_FIRST_TRADING_DECISION_CONSUMER
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
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
    assert IDENTITY_PRESERVING_INGEST is True
    assert NEW_COLLECTION_DTO_CREATED is False
    assert NEW_TOP5_HANDOFF_DTO_CREATED is False
    assert NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED is False
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
    assert PREPARED_BOUND_CARDINALITY != "5_PRODUCTIVE_LANES"


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
    assert S2_JOIN_SYMBOL == "admit_occupied_lane_bound_instruments_v1"
    assert S2_IMPLEMENTED is True
    assert (PACKAGE_DIR / "ingest_join_v1.py").is_file()
    ingest_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1",
        fromlist=["*"],
    )
    assert getattr(ingest_pkg, S2_JOIN_SYMBOL) is admit_occupied_lane_bound_instruments_v1
    assert callable(admit_occupied_lane_bound_instruments_v1)
    assert admit_occupied_lane_bound_instruments_v1.__name__ == S2_JOIN_SYMBOL
    assert "def admit_occupied_lane_bound_instruments_v1" not in CONSTANTS_SOURCE


def test_t_empty_returns_empty_dict() -> None:
    admitted = admit_occupied_lane_bound_instruments_v1({})
    assert admitted == {}
    assert list(admitted) == []


def test_t_one_preserves_lane_and_value_identity() -> None:
    original = _bound(lane_id="LANE_3")
    admitted = admit_occupied_lane_bound_instruments_v1({"LANE_3": original})
    assert list(admitted) == ["LANE_3"]
    _assert_same_bound(admitted["LANE_3"], original)


def test_t_multi_up_to_5_keeps_all_successful_lanes_unchanged() -> None:
    originals = {lane_id: _bound(lane_id=lane_id) for lane_id in LANE_IDS}
    admitted = admit_occupied_lane_bound_instruments_v1(originals)
    assert list(admitted) == list(LANE_IDS)
    for lane_id in LANE_IDS:
        _assert_same_bound(admitted[lane_id], originals[lane_id])


def test_t_unknown_lane_fails_closed() -> None:
    original = _bound(lane_id="LANE_1")
    with pytest.raises(FullAutonomyOccupiedLaneBoundIngestJoinError) as exc:
        admit_occupied_lane_bound_instruments_v1(
            {"LANE_1": original, "LANE_X": original},
        )
    assert exc.value.failure_code == FAILURE_UNKNOWN_LANE_ID
    assert "LANE_X" in exc.value.detail


def test_t_order_follows_canonical_lane_ids() -> None:
    originals = {
        "LANE_5": _bound(lane_id="LANE_5"),
        "LANE_1": _bound(lane_id="LANE_1"),
        "LANE_4": _bound(lane_id="LANE_4"),
    }
    admitted = admit_occupied_lane_bound_instruments_v1(originals)
    assert list(admitted) == ["LANE_1", "LANE_4", "LANE_5"]
    assert list(admitted) != list(originals)
    for lane_id, bound in originals.items():
        _assert_same_bound(admitted[lane_id], bound)


def test_t_no_pick_one() -> None:
    originals = {
        "LANE_2": _bound(lane_id="LANE_2"),
        "LANE_4": _bound(lane_id="LANE_4"),
        "LANE_5": _bound(lane_id="LANE_5"),
    }
    admitted = admit_occupied_lane_bound_instruments_v1(originals)
    assert PICK_ONE_AMONG_PREPARED_BOUNDS is False
    assert len(admitted) == 3
    assert list(admitted) == ["LANE_2", "LANE_4", "LANE_5"]
    assert set(admitted) == set(originals)
    for lane_id, bound in originals.items():
        _assert_same_bound(admitted[lane_id], bound)


def test_bound_type_mismatch_fails_closed() -> None:
    with pytest.raises(FullAutonomyOccupiedLaneBoundIngestJoinError) as exc:
        admit_occupied_lane_bound_instruments_v1({"LANE_1": object()})  # type: ignore[dict-item]
    assert exc.value.failure_code == FAILURE_BOUND_TYPE
    assert exc.value.detail == "LANE_1"


def test_t_no_cap23_cap24_reentry() -> None:
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
    for source in (JOIN_SOURCE, INIT_SOURCE):
        assert "produce_occupied_lane_cap23_n1_selections_v1" not in source
        assert "run_single_selected_future_policy_v1" not in source
        assert "produce_single_selected_future_v1" not in source
        assert "produce_from_ranking_state_root_v1" not in source
        assert "persist_selection_bundle_atomic_v1" not in source
        assert "_pick_top_eligible" not in source
        assert "run_single_selected_future_runtime_binding_gate_v1" not in source
        assert "ensure_single_selected_future_runtime_binding_v1" not in source
        assert "persist_binding_evidence_atomic_v1" not in source
        assert "bind_occupied_lane_cap24_n1_instruments_v1" not in source
    assert "def bind_occupied_lane_cap24_n1_instruments_v1" not in CONSTANTS_SOURCE
    imported = (
        _import_names(JOIN_SOURCE) | _import_names(INIT_SOURCE) | _import_names(CONSTANTS_SOURCE)
    )
    assert "src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1" not in imported
    assert "src.ops.single_selected_future_policy_v1.producer_v1" not in imported
    assert (
        "src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1"
        not in imported
    )


def test_t_no_mv2_dp_host_execution_graph() -> None:
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in JOIN_SOURCE
        assert forbidden not in INIT_SOURCE
    imported = (
        _import_names(JOIN_SOURCE) | _import_names(INIT_SOURCE) | _import_names(CONSTANTS_SOURCE)
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1"
        not in imported
    )
    assert not any(
        name.startswith(
            "src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        )
        for name in imported
    )
    assert "src.ops.full_core_live_path_composition_root_v1.composition_root_v1" not in imported
    assert "src.ops.stateful_no_order_host_join_v1" not in imported
    assert HOST_JOIN is False
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert DOUBLE_PLAY_CHANGE_REQUIRED is False
    assert JOIN_EXECUTION_AUTHORITY is False
    tree = ast.parse(JOIN_SOURCE)
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert S2_JOIN_SYMBOL not in called
    assert not (called & FORBIDDEN_CALL_GRAPH_TARGETS)
    assert inspect.getsource(admit_occupied_lane_bound_instruments_v1)
    assert FORBIDDEN_CALL_GRAPH_TARGETS == {
        "produce_occupied_lane_cap23_n1_selections_v1",
        "run_single_selected_future_policy_v1",
        "produce_single_selected_future_v1",
        "produce_from_ranking_state_root_v1",
        "persist_selection_bundle_atomic_v1",
        "_pick_top_eligible",
        "run_single_selected_future_runtime_binding_gate_v1",
        "ensure_single_selected_future_runtime_binding_v1",
        "persist_binding_evidence_atomic_v1",
        "run_current_productive_master_v2_runtime_cycle_v1",
        "compose_core_live_execution_intent_v1",
        "mf_canonical_single_egress_authority_handoff_contract_v1",
        "master_v2",
        "double_play",
        "execution",
        "top_n_active_set",
        "LiveExecutionPort",
    }
