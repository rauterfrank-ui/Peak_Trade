"""S1 contract/census bind tests for occupied-lane MV2/DP decision-state addressing."""

from __future__ import annotations

import ast
import inspect
from dataclasses import fields
from pathlib import Path

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
    PREPARED_BOUND_CARDINALITY as BOUNDARY_PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY as BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    constants_v1 as addressing_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    ADDRESSING_CONSUMER_OWNER,
    AUTHORITY_EFFECT,
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_BINDING_OWNER,
    CAP24_CHANGE_REQUIRED,
    CONSUMER_USED_EPHEMERAL_NOT_REQUIRED_CYCLE_CROSSING_STORE,
    CONTRACT_ID,
    CURSOR_BUNDLE_CYCLE_CROSSING_SURFACES,
    CURSOR_BUNDLE_TYPE,
    CURSOR_FILENAME,
    CURSOR_HAS_LANE_ID_FIELD,
    CURSOR_OWNER,
    CURSOR_OWNER_CHANGE_REQUIRED,
    CURSOR_SCHEMA_CHANGED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    DURABLE_SIBLING_NOT_REQUIRED_CYCLE_CROSSING_STORE,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FIRST_TRADING_DECISION_CONSUMER,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    FULL_AUTONOMY_HOST_OWNER,
    HOST_JOIN,
    INTENDED_PER_LANE_STORE_ROOT,
    INTENDED_PER_LANE_STORE_ROOT_FIELD,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_TRADING_AUTHORITY,
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_CAP61_PERSIST,
    MAY_CAP62_PERSIST,
    MAY_EXIT_POLICY_PERSIST,
    MAY_G17_CHECKPOINT,
    MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK,
    MAY_PERSIST_CURSOR,
    MF_PRODUCTIVE_JOIN,
    MF_SINGLE_EGRESS_REWIRED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N1_GLOBAL_CURSOR_LANE_SAFE,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    NEW_COLLECTION_DTO_CREATED,
    NEW_CURSOR_LANE_ID_FIELD,
    NEW_CURSOR_SCHEMA_CREATED,
    NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED,
    NEW_MV2_DP_INGRESS_DTO_CREATED,
    NEW_STATE_OWNER_CREATED,
    NEW_TOP5_HANDOFF_DTO_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PAIR_MAP_OBJECT,
    PAIR_MAP_PRODUCER,
    PAIR_MAP_PRODUCER_OWNER,
    PAIR_MAP_SLOT_TYPE,
    PARALLEL_AUTHORITY_CREATED,
    PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RUNTIME_AUTHORIZATION_EFFECT,
    S2_IMPLEMENTED,
    S2_INTENDED_EGRESS,
    S2_JOIN_SYMBOL,
    SAME_TRADING_CONFIGURATION_ACROSS_LANES,
    SHARED_MUTABLE_STATE_ACROSS_LANES,
    SLICE_ID,
    SLOT_IDENTITY,
    SLOT_STATE_ROOT_RESOLVER,
    THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT,
    THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
    THIS_SLICE_MAY_RESTORE_CURSOR,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.constants_v1 import (
    HANDOFF_EGRESS_OBJECT,
    OWNER as HANDOFF_OWNER,
    S2_IMPLEMENTED as HANDOFF_S2_IMPLEMENTED,
    S2_JOIN_SYMBOL as HANDOFF_S2_JOIN_SYMBOL,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME as EXISTING_CURSOR_FILENAME,
    CurrentProductiveSideStateConfirmationCursorV1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    FIRST_TRADING_DECISION_CONSUMER as HANDOFF_FIRST_TRADING_DECISION_CONSUMER,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
    OWNER as CAP23_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
    OWNER as CAP24_OWNER,
)

PACKAGE_DIR = Path(addressing_constants.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
CYCLE_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
).read_text(encoding="utf-8")
ONESHOT_V1_SOURCE = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1.py"
).read_text(encoding="utf-8")
CURSOR_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_sidestate_confirmation_cursor_v1.py"
).read_text(encoding="utf-8")


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


def test_s1_authority_flags_and_addressing_census_bind() -> None:
    assert SLICE_ID == "S1_CONTRACT_BIND"
    assert OWNER == (
        "ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1"
    )
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_V1"
        "_S1_CONTRACT_BIND"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert ADDRESSING_CONSUMER_OWNER == OWNER
    assert PAIR_MAP_PRODUCER_OWNER == HANDOFF_OWNER
    assert PAIR_MAP_PRODUCER == HANDOFF_S2_JOIN_SYMBOL
    assert PAIR_MAP_PRODUCER == "compose_occupied_lane_mv2_dp_handoff_v1"
    assert HANDOFF_S2_IMPLEMENTED is True
    assert PAIR_MAP_OBJECT == HANDOFF_EGRESS_OBJECT
    assert PAIR_MAP_OBJECT == "dict[lane_id, (IsolatedLaneSlotV1, BoundInstrumentV1)]"
    assert PAIR_MAP_SLOT_TYPE == IsolatedLaneSlotV1.__name__
    assert SLOT_IDENTITY == "lane_id"
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert SLOT_STATE_ROOT_RESOLVER == lane_state_root_for.__name__
    assert INTENDED_PER_LANE_STORE_ROOT == "IsolatedLaneSlotV1.lane_state_root"
    assert INTENDED_PER_LANE_STORE_ROOT_FIELD == "lane_state_root"
    assert N1_GLOBAL_CURSOR_LANE_SAFE is False
    assert CURSOR_BUNDLE_TYPE == CurrentProductiveSideStateConfirmationCursorV1.__name__
    assert CURSOR_HAS_LANE_ID_FIELD is False
    assert CURSOR_SCHEMA_CHANGED is False
    assert NEW_CURSOR_LANE_ID_FIELD is False
    assert NEW_CURSOR_SCHEMA_CREATED is False
    assert NEW_STATE_OWNER_CREATED is False
    assert SAME_TRADING_CONFIGURATION_ACROSS_LANES is True
    assert SHARED_MUTABLE_STATE_ACROSS_LANES is False
    assert CAP23_SELECTION_OWNER == CAP23_OWNER
    assert CAP24_BINDING_OWNER == CAP24_OWNER
    assert FIRST_TRADING_DECISION_CONSUMER == HANDOFF_FIRST_TRADING_DECISION_CONSUMER
    assert FIRST_TRADING_DECISION_CONSUMER == ("run_current_productive_master_v2_runtime_cycle_v1")
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
    assert MAY_PERSIST_CURSOR is False
    assert MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK is False
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert MAY_CAP61_PERSIST is False
    assert MAY_CAP62_PERSIST is False
    assert MAY_G17_CHECKPOINT is False
    assert MAY_EXIT_POLICY_PERSIST is False
    assert THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT is False
    assert THIS_SLICE_MAY_RESTORE_CURSOR is False
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert JOIN_PERSISTENCE_AUTHORITY is False
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert PARALLEL_AUTHORITY_CREATED is False
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
    assert CURSOR_OWNER_CHANGE_REQUIRED is False
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    assert PREPARED_BOUND_CARDINALITY == BOUNDARY_PREPARED_BOUND_CARDINALITY == "0..5"
    assert PRODUCTIVE_RUNTIME_CARDINALITY == BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert PREPARED_BOUND_CARDINALITY != "5_PRODUCTIVE_LANES"


def test_s1_reuses_existing_lane_ids_and_lane_state_root_field(tmp_path: Path) -> None:
    assert SLOT_STATE_ROOT_RESOLVER == "lane_state_root_for"
    assert list(LANE_IDS) == ["LANE_1", "LANE_2", "LANE_3", "LANE_4", "LANE_5"]
    slot_fields = {item.name for item in fields(IsolatedLaneSlotV1)}
    assert INTENDED_PER_LANE_STORE_ROOT_FIELD in slot_fields
    for lane_id in LANE_IDS:
        resolved = lane_state_root_for(
            topology_state_root_base=tmp_path,
            lane_id=lane_id,
        )
        assert resolved == str(tmp_path / lane_id)
        assert resolved != N1_GLOBAL_CURSOR_STORE_RELPATH


def test_s1_n1_global_cursor_path_is_not_lane_safe() -> None:
    assert N1_GLOBAL_CURSOR_LANE_SAFE is False
    assert N1_GLOBAL_CURSOR_STORE_RELPATH == (
        "evidence/ops/full_core_current_productive_sidestate_confirmation_cursor_current_v1"
    )
    assert "CURRENT_CURSOR_STORE_RELPATH" in ONESHOT_V1_SOURCE
    assert N1_GLOBAL_CURSOR_STORE_RELPATH in ONESHOT_V1_SOURCE
    assert CURSOR_FILENAME == EXISTING_CURSOR_FILENAME
    assert CURSOR_FILENAME == "current_productive_sidestate_confirmation_cursor_v1.json"


def test_s1_cursor_bundle_has_no_lane_id_and_carries_cycle_crossing_surfaces() -> None:
    cursor_fields = {item.name for item in fields(CurrentProductiveSideStateConfirmationCursorV1)}
    assert "lane_id" not in cursor_fields
    assert "lane_state_root" not in cursor_fields
    assert CURSOR_HAS_LANE_ID_FIELD is False
    assert "side_state" in cursor_fields
    assert "runtime_scope_state" in cursor_fields
    assert "existing_scope" in cursor_fields
    assert "scope_confirmation" in cursor_fields
    assert "cap61_confirmation_state" in cursor_fields
    assert CURSOR_BUNDLE_CYCLE_CROSSING_SURFACES == (
        "SideState",
        "RuntimeScopeState",
        "CanonicalScopeSnapshotV1",
        "ScopeConfirmationStateV1",
        "CanonicalConfirmationStateV1",
    )
    assert CURSOR_OWNER.endswith("current_productive_sidestate_confirmation_cursor_v1")
    assert (
        "lane_id"
        not in CURSOR_SOURCE.split("class CurrentProductiveSideStateConfirmationCursorV1", 1)[
            1
        ].split("def to_dict", 1)[0]
    )


def test_s1_cycle_cap61_is_in_memory_and_durable_siblings_are_not_required_stores() -> None:
    assert "state_root=None" in CYCLE_SOURCE
    assert "persist=False" in CYCLE_SOURCE
    assert "def _bind_cap61_confirmation_v1" in CYCLE_SOURCE
    assert "commit_host_confirmation_after_replay_v1" in CYCLE_SOURCE
    assert "load_dynamic_scope_state_v1" not in CYCLE_SOURCE
    assert "persist_dynamic_scope_state_atomic_v1" not in CYCLE_SOURCE
    assert "apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1" not in (CYCLE_SOURCE)
    assert "persist_exit_policy_state_atomic_v1" not in CYCLE_SOURCE
    assert "commit_host_exit_policy_state_v1" not in CYCLE_SOURCE
    assert DURABLE_SIBLING_NOT_REQUIRED_CYCLE_CROSSING_STORE == (
        "Cap61_confirmation_state_v1.json",
        "Cap62_dynamic_scope_state_v1.json",
        "G17_mark_history_checkpoint",
        "exit_policy_state_v1.json",
    )
    assert CONSUMER_USED_EPHEMERAL_NOT_REQUIRED_CYCLE_CROSSING_STORE == (
        "HostConfirmationBindingV1_in_memory",
        "HostExitPolicyBindingV1_ephemeral",
        "optional_G17_producer_in_memory",
    )


def test_s1_same_trading_configuration_is_not_shared_mutable_state() -> None:
    assert SAME_TRADING_CONFIGURATION_ACROSS_LANES is True
    assert SHARED_MUTABLE_STATE_ACROSS_LANES is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert DOUBLE_PLAY_CHANGE_REQUIRED is False
    assert FIRST_TRADING_DECISION_CONSUMER == "run_current_productive_master_v2_runtime_cycle_v1"
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_s2_resolver_is_named_but_not_implemented() -> None:
    assert S2_JOIN_SYMBOL == "resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1"
    assert S2_IMPLEMENTED is False
    assert S2_INTENDED_EGRESS == "dict[lane_id, str]"
    assert not (PACKAGE_DIR / "addressing_join_v1.py").exists()
    assert not (PACKAGE_DIR / "store_root_join_v1.py").exists()
    assert not (PACKAGE_DIR / "handoff_join_v1.py").exists()
    assert not hasattr(addressing_constants, S2_JOIN_SYMBOL)
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert not hasattr(addressing_pkg, S2_JOIN_SYMBOL)
    assert not callable(getattr(addressing_pkg, S2_JOIN_SYMBOL, None))
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S2_JOIN_SYMBOL}" not in INIT_SOURCE
    assert inspect.getmodule(addressing_constants) is not None


def test_s1_forbidden_graph_and_protected_imports() -> None:
    for forbidden in FORBIDDEN_CALL_GRAPH_TARGETS:
        assert forbidden not in INIT_SOURCE
    imported = _import_names(CONSTANTS_SOURCE) | _import_names(INIT_SOURCE)
    assert (
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1"
        not in imported
    )
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
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1"
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
    assert "src.ops.dynamic_scope_persistence_binding_v1.persistence_v1" not in imported
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_mark_history_checkpoint_v1"
        not in imported
    )
    assert "src.ops.exit_policy_producer_binding_v1.host_binding_v1" not in imported
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S2_JOIN_SYMBOL}" not in INIT_SOURCE
    assert FIRST_TRADING_DECISION_CONSUMER in CONSTANTS_SOURCE
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is False
    assert MAY_PERSIST_CURSOR is False
    assert MAY_BIND_CAP61_STATE_ROOT is False
