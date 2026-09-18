"""S1 contract/authority bind tests for Full-Autonomy occupied-lane MV2/DP handoff."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

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
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
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


def test_s1_authority_flags_and_consumer_bind() -> None:
    assert SLICE_ID == "S1_CONTRACT_BIND"
    assert OWNER == "ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1"
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_HANDOFF_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_HANDOFF_JOIN_V1_S1_CONTRACT_BIND"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert HANDOFF_CONSUMER_OWNER == OWNER
    assert ADMITTED_MAP_PRODUCER_OWNER == INGEST_OWNER
    assert HANDOFF_ADMITTED_INPUT_PRODUCER == INGEST_S2_JOIN_SYMBOL
    assert HANDOFF_ADMITTED_INPUT_PRODUCER == "admit_occupied_lane_bound_instruments_v1"
    assert HANDOFF_ADMITTED_INPUT_OBJECT == "dict[lane_id, BoundInstrumentV1]"
    assert HANDOFF_TOPOLOGY_INPUT_TYPE == IsolatedLaneTopologyV1.__name__
    assert HANDOFF_SLOT_TYPE == IsolatedLaneSlotV1.__name__
    assert HANDOFF_EGRESS_OBJECT == "dict[lane_id, (IsolatedLaneSlotV1, BoundInstrumentV1)]"
    assert MV2_DP_INGRESS_TYPE == FULL_CORE_INGEST_OBJECT == "BoundInstrumentV1"
    assert MV2_DP_INGRESS_TYPE == BoundInstrumentV1.__name__
    assert SLOT_IDENTITY == "lane_id"
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert SLOT_STATE_ROOT_RESOLVER == lane_state_root_for.__name__
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
    assert CAP24_BINDING_OWNER == CAP24_OWNER
    assert LAST_RANKING_UNIVERSE_AUTHORITY.endswith("SINGLE_SELECTED_FUTURE_POLICY_V1")
    assert FIRST_TRADING_DECISION_CONSUMER == HANDOFF_FIRST_TRADING_DECISION_CONSUMER
    assert FIRST_TRADING_DECISION_CONSUMER == ("run_current_productive_master_v2_runtime_cycle_v1")
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
    assert PREPARED_BOUND_CARDINALITY != "5_PRODUCTIVE_LANES"


def test_s1_reuses_existing_lane_ids_and_lane_state_root_for(tmp_path: Path) -> None:
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert list(LANE_IDS) == ["LANE_1", "LANE_2", "LANE_3", "LANE_4", "LANE_5"]
    for lane_id in LANE_IDS:
        resolved = lane_state_root_for(
            topology_state_root_base=tmp_path,
            lane_id=lane_id,
        )
        assert resolved == str(tmp_path / lane_id)


def test_s2_join_is_named_but_not_implemented() -> None:
    assert S2_JOIN_SYMBOL == "compose_occupied_lane_mv2_dp_handoff_v1"
    assert S2_IMPLEMENTED is False
    assert not (PACKAGE_DIR / "handoff_join_v1.py").exists()
    assert not (PACKAGE_DIR / "compose_join_v1.py").exists()
    assert not hasattr(handoff_constants, S2_JOIN_SYMBOL)
    package = inspect.getmodule(handoff_constants)
    assert package is not None
    handoff_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1",
        fromlist=["*"],
    )
    assert not hasattr(handoff_pkg, S2_JOIN_SYMBOL)
    assert not callable(getattr(handoff_pkg, S2_JOIN_SYMBOL, None))
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S2_JOIN_SYMBOL}" not in INIT_SOURCE


def test_s1_forbidden_graph_and_protected_imports() -> None:
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in INIT_SOURCE
    imported = _import_names(CONSTANTS_SOURCE) | _import_names(INIT_SOURCE)
    assert (
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.ingest_join_v1"
        not in imported
    )
    assert (
        "src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1"
        not in imported
    )
    assert "src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1" not in imported
    assert "src.ops.single_selected_future_policy_v1.producer_v1" not in imported
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1"
        not in imported
    )
    assert "trading.master_v2.integrated_offline_trading_logic_replay_v1" not in imported
    assert not any(
        name.startswith(
            "src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        )
        for name in imported
    )
    assert "src.ops.full_core_live_path_composition_root_v1.composition_root_v1" not in imported
    assert "src.ops.stateful_no_order_host_join_v1" not in imported
    assert "src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1" not in (
        imported
    )
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S2_JOIN_SYMBOL}" not in INIT_SOURCE
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
        "run_integrated_offline_trading_logic_replay_v1",
        "ensure_host_confirmation_binding_v1",
        "compose_core_live_execution_intent_v1",
        "mf_canonical_single_egress_authority_handoff_contract_v1",
        "master_v2",
        "double_play",
        "execution",
        "top_n_active_set",
        "LiveExecutionPort",
    }
    assert FIRST_TRADING_DECISION_CONSUMER in CONSTANTS_SOURCE
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False
