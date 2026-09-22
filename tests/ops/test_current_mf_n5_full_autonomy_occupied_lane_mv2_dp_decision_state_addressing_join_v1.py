"""S2 occupied-lane MV2/DP decision-state store-root resolver tests."""

from __future__ import annotations

import ast
import inspect
import json
import math
from dataclasses import fields, replace
from pathlib import Path

import pytest

from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.constants_v1 import (
    PREPARED_BOUND_CARDINALITY as BOUNDARY_PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY as BOUNDARY_PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    constants_v1 as addressing_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError,
    OccupiedLaneMv2DpDecisionStateConsumerInvocationV1,
    bind_occupied_lane_governed_cycle_store_roots_v1,
    bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1,
    carry_occupied_lane_mv2_dp_decision_state_in_memory_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
    invoke_occupied_lane_mv2_dp_decision_state_consumer_v1,
    persist_occupied_lane_mv2_dp_decision_state_cursor_v1,
    resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1,
    restore_occupied_lane_mv2_dp_decision_state_cursor_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    ADDRESSING_CONSUMER_OWNER,
    AUTHORITY_EFFECT,
    CAP61_CYCLE_STATE_ROOT_BOUND,
    CONSUMPTION_SEAM,
    CONSUMER_CYCLE_INPUTS,
    CONSUMER_CYCLE_TAKES_STORE_ROOT,
    CONSUMER_INVOKED,
    CAP23_CHANGE_REQUIRED,
    CAP23_SELECTION_OWNER,
    CAP24_BINDING_OWNER,
    CAP24_CHANGE_REQUIRED,
    CONSUMER_USED_EPHEMERAL_NOT_REQUIRED_CYCLE_CROSSING_STORE,
    CONTRACT_ID,
    CURSOR_BUNDLE_CYCLE_CROSSING_SURFACES,
    CURSOR_BUNDLE_TYPE,
    CURSOR_FILENAME,
    CURSOR_FILENAME_SHARED_ACROSS_LANES,
    CURSOR_HAS_LANE_ID_FIELD,
    CURSOR_OWNER,
    CURSOR_OWNER_CHANGE_REQUIRED,
    CURSOR_SCHEMA_CHANGED,
    DOUBLE_PLAY_CHANGE_REQUIRED,
    DURABLE_SIBLING_NOT_REQUIRED_CYCLE_CROSSING_STORE,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_ALIASED_LANE_STATE,
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
    FIRST_DECISION_STATE_CONSUMER,
    FIRST_TRADING_DECISION_CONSUMER,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FULL_AUTONOMY_HOST_CHANGE_REQUIRED,
    FULL_AUTONOMY_HOST_OWNER,
    GLOBAL_N1_CURSOR_REJECTED,
    GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME,
    GOVERNED_CYCLE_LOCK_ROOT_DIRNAME,
    HOST_JOIN,
    INTENDED_PER_LANE_STORE_ROOT,
    INTENDED_PER_LANE_STORE_ROOT_FIELD,
    INVOCATION_CONTEXT,
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
    MAY_INVOKE_GOVERNED_CYCLE,
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
    OCCUPIED_LANES_ONLY,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PAIR_MAP_OBJECT,
    PAIR_MAP_PRODUCER,
    PAIR_MAP_PRODUCER_OWNER,
    PAIR_MAP_SLOT_TYPE,
    PARALLEL_AUTHORITY_CREATED,
    PREPARED_BOUND_CARDINALITY,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RESOLUTION_RULE,
    RUNTIME_AUTHORIZATION_EFFECT,
    S2_IMPLEMENTED,
    S2_INTENDED_EGRESS,
    S2_JOIN_SYMBOL,
    S3_IMPLEMENTED,
    S3_INTENDED_EGRESS,
    S3_JOIN_SYMBOL,
    S4_IMPLEMENTED,
    S4_INTENDED_EGRESS,
    S4_JOIN_SYMBOL,
    ATOMICITY_SEMANTICS,
    PERSIST_ENABLED,
    PERSIST_SURFACE_OWNER,
    S5_IMPLEMENTED,
    S5_JOIN_SYMBOL,
    S6_IMPLEMENTED,
    S6_JOIN_SYMBOL,
    S6_PERSIST_SYMBOL,
    S6_RESTORE_SYMBOL,
    S7_IMPLEMENTED,
    S7_JOIN_SYMBOL,
    S8_CONSUMPTION_SEAM,
    S8_IMPLEMENTED,
    S8_INTENDED_EGRESS,
    S8_JOIN_SYMBOL,
    IN_MEMORY_CURSOR_HOLDER,
    LANE_STATE_ROOT_ROLE,
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
    UNIQUE_MUTABLE_ROOTS_ENFORCED,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.constants_v1 import (
    HANDOFF_EGRESS_OBJECT,
    OWNER as HANDOFF_OWNER,
    S2_IMPLEMENTED as HANDOFF_S2_IMPLEMENTED,
    S2_JOIN_SYMBOL as HANDOFF_S2_JOIN_SYMBOL,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1 import (
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
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CurrentProductiveCursorError,
    load_current_productive_sidestate_confirmation_cursor_v1,
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME as EXISTING_CURSOR_FILENAME,
    CurrentProductiveSideStateConfirmationCursorV1,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_layered_core_bind_wiring_v1 import (
    productive_layered_core_bind_cycle_kwargs_v1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    FIRST_TRADING_DECISION_CONSUMER as HANDOFF_FIRST_TRADING_DECISION_CONSUMER,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
    OWNER as CAP23_OWNER,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
    OWNER as CAP24_OWNER,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)

PACKAGE_DIR = Path(addressing_constants.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "addressing_join_v1.py").read_text(encoding="utf-8")
CYCLE_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
).read_text(encoding="utf-8")
ONESHOT_V1_HOST = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1.py"
)
CURSOR_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_sidestate_confirmation_cursor_v1.py"
).read_text(encoding="utf-8")
UNIVERSE_SNAPSHOT = "uni-shared"
RANKING_SNAPSHOT = "rank-shared"
RANKING_DIGEST = "rank-digest-shared"
SUBSTRING_FORBIDDEN_INIT = frozenset(
    name
    for name in FORBIDDEN_CALL_GRAPH_TARGETS
    if name
    not in {
        "master_v2",
        "double_play",
        "execution",
    }
)


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


def _called_names(source: str) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


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


def _pair(
    tmp_path: Path,
    lane_id: str,
    *,
    bound: BoundInstrumentV1 | None = None,
    occupancy: str | None = None,
    lane_state_root: str | None = None,
) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    instrument = bound or _bound(lane_id=lane_id)
    return (
        _slot(
            lane_id=lane_id,
            topology_state_root_base=tmp_path,
            bound=instrument,
            occupancy=occupancy,
            lane_state_root=lane_state_root,
        ),
        instrument,
    )


def _topology(
    tmp_path: Path,
    occupied: dict[str, BoundInstrumentV1] | None = None,
) -> IsolatedLaneTopologyV1:
    occupied = occupied or {}
    topology_state_root_base = str(Path(tmp_path).expanduser().resolve())
    slots = [
        _slot(
            lane_id=lane_id,
            topology_state_root_base=topology_state_root_base,
            bound=occupied.get(lane_id),
        )
        for lane_id in LANE_IDS
    ]
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


def test_s2_authority_flags_and_addressing_census_bind() -> None:
    assert SLICE_ID == "S8_HARNESS_BIND_OCCUPIED_LANE_GOVERNED_CYCLE_ROOTS_WITHOUT_INVOKE"
    assert OWNER == (
        "ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1"
    )
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_V1"
        "_S8_HARNESS_BIND_OCCUPIED_LANE_GOVERNED_CYCLE_ROOTS_WITHOUT_INVOKE"
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
    assert RESOLUTION_RULE == "occupied_lane_id -> IsolatedLaneSlotV1.lane_state_root"
    assert OCCUPIED_LANES_ONLY is True
    assert UNIQUE_MUTABLE_ROOTS_ENFORCED is True
    assert GLOBAL_N1_CURSOR_REJECTED is True
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
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is True
    assert INVOCATION_CONTEXT == "BOUNDED_TEST_HARNESS_LANE_ISOLATED"
    assert CONSUMER_INVOKED is True
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
    assert MAY_PERSIST_CURSOR is True
    assert MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK is True
    assert PERSIST_ENABLED is True
    assert PERSIST_SURFACE_OWNER == CURSOR_OWNER
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert MAY_CAP61_PERSIST is False
    assert MAY_CAP62_PERSIST is False
    assert MAY_G17_CHECKPOINT is False
    assert MAY_EXIT_POLICY_PERSIST is False
    assert MAY_INVOKE_GOVERNED_CYCLE is False
    assert THIS_SLICE_MAY_BIND_CAP61_STATE_ROOT is False
    assert THIS_SLICE_MAY_RESTORE_CURSOR is True
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
    assert S3_IMPLEMENTED is True
    assert S4_IMPLEMENTED is True
    assert S5_IMPLEMENTED is True
    assert S6_IMPLEMENTED is True
    assert S7_IMPLEMENTED is True
    assert S8_IMPLEMENTED is True
    assert S8_JOIN_SYMBOL == "bind_occupied_lane_governed_cycle_store_roots_v1"
    assert S4_JOIN_SYMBOL == "invoke_occupied_lane_mv2_dp_decision_state_consumer_v1"
    assert FIRST_DECISION_STATE_CONSUMER == FIRST_TRADING_DECISION_CONSUMER
    assert CONSUMPTION_SEAM == "pre_invoke_run_current_productive_master_v2_runtime_cycle_v1"
    assert CONSUMER_CYCLE_TAKES_STORE_ROOT is False
    assert CONSUMER_CYCLE_INPUTS == ("bound_instrument", "incoming_cursor")
    assert CURSOR_FILENAME_SHARED_ACROSS_LANES is True
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False


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
        assert resolved == str(Path(tmp_path).expanduser().resolve() / lane_id)
        assert resolved != N1_GLOBAL_CURSOR_STORE_RELPATH


def test_s1_n1_global_cursor_path_is_not_lane_safe() -> None:
    assert N1_GLOBAL_CURSOR_LANE_SAFE is False
    assert GLOBAL_N1_CURSOR_REJECTED is True
    assert N1_GLOBAL_CURSOR_STORE_RELPATH == (
        "evidence/ops/full_core_current_productive_sidestate_confirmation_cursor_current_v1"
    )
    assert not ONESHOT_V1_HOST.is_file()
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


def test_s2_join_is_implemented() -> None:
    assert S2_JOIN_SYMBOL == "resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1"
    assert S2_IMPLEMENTED is True
    assert S2_INTENDED_EGRESS == "dict[lane_id, str]"
    assert S3_IMPLEMENTED is True
    assert S4_IMPLEMENTED is True
    assert S5_IMPLEMENTED is True
    assert FIRST_DECISION_STATE_CONSUMER == FIRST_TRADING_DECISION_CONSUMER
    assert CONSUMPTION_SEAM == "pre_invoke_run_current_productive_master_v2_runtime_cycle_v1"
    assert CONSUMER_CYCLE_TAKES_STORE_ROOT is False
    assert CONSUMER_CYCLE_INPUTS == ("bound_instrument", "incoming_cursor")
    assert CURSOR_FILENAME_SHARED_ACROSS_LANES is True
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert (PACKAGE_DIR / "addressing_join_v1.py").is_file()
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert (
        getattr(addressing_pkg, S2_JOIN_SYMBOL)
        is resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1
    )
    assert callable(resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1)
    assert resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1.__name__ == S2_JOIN_SYMBOL
    assert f"def {S2_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S2_JOIN_SYMBOL}" in JOIN_SOURCE


def test_s3_join_is_implemented() -> None:
    assert S3_JOIN_SYMBOL == "bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1"
    assert S3_IMPLEMENTED is True
    assert S3_INTENDED_EGRESS == ("dict[lane_id, (BoundInstrumentV1, store_root, cursor_address)]")
    assert S4_IMPLEMENTED is True
    assert S5_IMPLEMENTED is True
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert (
        getattr(addressing_pkg, S3_JOIN_SYMBOL)
        is bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1
    )
    assert callable(bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1)
    assert bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1.__name__ == S3_JOIN_SYMBOL
    assert f"def {S3_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S3_JOIN_SYMBOL}" in JOIN_SOURCE
    assert FIRST_DECISION_STATE_CONSUMER == "run_current_productive_master_v2_runtime_cycle_v1"
    assert CONSUMPTION_SEAM == "pre_invoke_run_current_productive_master_v2_runtime_cycle_v1"


def test_t_empty_returns_empty_dict() -> None:
    resolved = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1({})
    assert resolved == {}
    assert list(resolved) == []


def test_t_n1_single_occupied_lane_maps_to_existing_lane_state_root(tmp_path: Path) -> None:
    pair = _pair(tmp_path, "LANE_3")
    resolved = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1({"LANE_3": pair})
    expected = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_3")
    assert list(resolved) == ["LANE_3"]
    assert resolved["LANE_3"] == expected
    assert resolved["LANE_3"] == pair[0].lane_state_root
    assert resolved["LANE_3"] != N1_GLOBAL_CURSOR_STORE_RELPATH


def test_t_occupied_lanes_only_omits_absent_lanes(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1"),
        "LANE_4": _pair(tmp_path, "LANE_4"),
    }
    resolved = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(pairs)
    assert list(resolved) == ["LANE_1", "LANE_4"]
    assert "LANE_2" not in resolved
    assert "LANE_3" not in resolved
    assert "LANE_5" not in resolved


def test_t_multi_occupied_is_deterministic_and_unique(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in LANE_IDS}
    shuffled = {
        "LANE_5": pairs["LANE_5"],
        "LANE_1": pairs["LANE_1"],
        "LANE_4": pairs["LANE_4"],
        "LANE_2": pairs["LANE_2"],
        "LANE_3": pairs["LANE_3"],
    }
    resolved = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(shuffled)
    assert list(resolved) == list(LANE_IDS)
    roots = list(resolved.values())
    assert len(roots) == len(set(roots))
    for lane_id in LANE_IDS:
        expected = lane_state_root_for(topology_state_root_base=tmp_path, lane_id=lane_id)
        assert resolved[lane_id] == expected
        assert resolved[lane_id] == pairs[lane_id][0].lane_state_root
        for other_id in LANE_IDS:
            if other_id == lane_id:
                continue
            assert resolved[lane_id] != resolved[other_id]


def test_t_compose_pair_map_is_accepted_without_recompose(tmp_path: Path) -> None:
    originals = {
        "LANE_2": _bound(lane_id="LANE_2"),
        "LANE_5": _bound(lane_id="LANE_5"),
    }
    topology = _topology(tmp_path, originals)
    composed = compose_occupied_lane_mv2_dp_handoff_v1(originals, topology)
    resolved = resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(composed)
    assert list(resolved) == ["LANE_2", "LANE_5"]
    for lane_id in ("LANE_2", "LANE_5"):
        assert resolved[lane_id] == composed[lane_id][0].lane_state_root
        assert resolved[lane_id] == lane_state_root_for(
            topology_state_root_base=tmp_path, lane_id=lane_id
        )


def test_t_unknown_lane_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1"), "LANE_X": _pair(tmp_path, "LANE_1")}
        )
    assert exc.value.failure_code == FAILURE_UNKNOWN_LANE_ID
    assert "LANE_X" in exc.value.detail


def test_t_empty_occupancy_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_5": _pair(tmp_path, "LANE_5", occupancy=OCCUPANCY_EMPTY)}
        )
    assert exc.value.failure_code == FAILURE_OCCUPANCY
    assert exc.value.detail == "LANE_5"


def test_t_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    slot, _bound_slot = _pair(tmp_path, "LANE_2")
    other = _bound(lane_id="LANE_2", instrument_id="INST-OTHER")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1({"LANE_2": (slot, other)})
    assert exc.value.failure_code == FAILURE_IDENTITY_MISMATCH
    assert exc.value.detail == "LANE_2"


def test_t_missing_root_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root="   ")}
        )
    assert exc.value.failure_code == FAILURE_MISSING_STORE_ROOT
    assert exc.value.detail == "LANE_1"


def test_t_invalid_root_fails_closed(tmp_path: Path) -> None:
    wrong_root = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_2")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root=wrong_root)}
        )
    assert exc.value.failure_code == FAILURE_INVALID_STORE_ROOT
    assert exc.value.detail == "LANE_1"


def test_t_shared_symlink_root_fails_closed(tmp_path: Path) -> None:
    lane1 = tmp_path / "LANE_1"
    lane1.mkdir()
    (tmp_path / "LANE_2").symlink_to(lane1)
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {
                "LANE_1": _pair(tmp_path, "LANE_1"),
                "LANE_2": _pair(tmp_path, "LANE_2"),
            }
        )
    assert exc.value.failure_code == FAILURE_SHARED_STORE_ROOT
    assert "LANE_1" in exc.value.detail
    assert "LANE_2" in exc.value.detail


def test_t_n1_global_cursor_path_rejected_as_store_root(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {
                "LANE_1": _pair(
                    tmp_path,
                    "LANE_1",
                    lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH,
                )
            }
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    assert exc.value.detail == "LANE_1"


def test_t_n1_global_cursor_path_rejected_as_shared_n5_base(tmp_path: Path) -> None:
    n1_base = tmp_path / N1_GLOBAL_CURSOR_STORE_RELPATH
    n1_base.mkdir(parents=True)
    n1_lane_root = lane_state_root_for(topology_state_root_base=n1_base, lane_id="LANE_4")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_4": _pair(tmp_path, "LANE_4", lane_state_root=n1_lane_root)}
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    assert exc.value.detail == "LANE_4"


def test_t_pair_and_slot_type_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": object()}  # type: ignore[dict-item]
        )
    assert exc.value.failure_code == FAILURE_PAIR_TYPE
    slot, bound = _pair(tmp_path, "LANE_1")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": (object(), bound)}  # type: ignore[dict-item]
        )
    assert exc.value.failure_code == FAILURE_SLOT_TYPE
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1(
            {"LANE_1": (slot, object())}  # type: ignore[dict-item]
        )
    assert exc.value.failure_code == FAILURE_BOUND_TYPE


def test_t_no_cursor_io_consumer_cap61_or_runtime_side_effects() -> None:
    for source in (JOIN_SOURCE, INIT_SOURCE):
        assert "open(" not in source
        assert "write_text" not in source
        assert "read_text" not in source
        assert "Path.write" not in source
        assert "json.dump" not in source
        assert "json.load" not in source
        assert "ensure_host_confirmation_binding_v1" not in source
        assert "CurrentProductiveSideStateConfirmationCursorV1" not in source
        assert "state_root=" not in source
        assert "persist=" not in source
        assert "persist_current_productive_sidestate_confirmation_cursor_v1" not in INIT_SOURCE
        assert "load_current_productive_sidestate_confirmation_cursor_v1" not in INIT_SOURCE
        assert "restore_current_productive_sidestate_confirmation_cursor_v1" not in source
    assert "run_current_productive_master_v2_runtime_cycle_v1" not in INIT_SOURCE
    assert "compose_occupied_lane_mv2_dp_handoff_v1" not in JOIN_SOURCE
    imported_init_constants = _import_names(INIT_SOURCE) | _import_names(CONSTANTS_SOURCE)
    assert (
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1"
        not in imported_init_constants
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1"
        not in imported_init_constants
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1"
        not in imported_init_constants
    )
    assert "src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1" not in (
        imported_init_constants
    )
    assert "src.ops.stateful_no_order_host_join_v1" not in imported_init_constants
    assert "trading.master_v2.integrated_offline_trading_logic_replay_v1" not in (
        imported_init_constants | _import_names(JOIN_SOURCE)
    )
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert inspect.getsource(resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1)


def test_s2_forbidden_graph_and_protected_imports() -> None:
    for forbidden in SUBSTRING_FORBIDDEN_INIT:
        assert forbidden not in INIT_SOURCE
    imported = (
        _import_names(CONSTANTS_SOURCE) | _import_names(INIT_SOURCE) | _import_names(JOIN_SOURCE)
    )
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
        not in (_import_names(CONSTANTS_SOURCE) | _import_names(INIT_SOURCE))
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1"
        not in (_import_names(CONSTANTS_SOURCE) | _import_names(INIT_SOURCE))
    )
    assert (
        "src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1"
        in _import_names(JOIN_SOURCE)
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
    assert FIRST_TRADING_DECISION_CONSUMER in CONSTANTS_SOURCE
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is True
    assert MAY_PERSIST_CURSOR is True
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert lane_state_root_key
    assert S3_IMPLEMENTED is True
    assert S4_IMPLEMENTED is True
    assert S5_IMPLEMENTED is True
    assert FIRST_DECISION_STATE_CONSUMER == FIRST_TRADING_DECISION_CONSUMER
    assert CONSUMPTION_SEAM == "pre_invoke_run_current_productive_master_v2_runtime_cycle_v1"
    assert CONSUMER_CYCLE_TAKES_STORE_ROOT is False
    assert CONSUMER_CYCLE_INPUTS == ("bound_instrument", "incoming_cursor")
    assert CURSOR_FILENAME_SHARED_ACROSS_LANES is True
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False


def test_s3_n1_parity_binds_existing_lane_state_root_and_shared_filename(
    tmp_path: Path,
) -> None:
    pair = _pair(tmp_path, "LANE_3")
    bound_seam = bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1({"LANE_3": pair})
    store_root = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_3")
    expected_cursor = lane_state_root_key(Path(store_root) / CURSOR_FILENAME)
    assert list(bound_seam) == ["LANE_3"]
    bound, root, cursor_address = bound_seam["LANE_3"]
    assert bound is pair[1]
    assert root == pair[0].lane_state_root
    assert root == store_root
    assert cursor_address == expected_cursor
    assert cursor_address.endswith(CURSOR_FILENAME)
    assert root != N1_GLOBAL_CURSOR_STORE_RELPATH
    assert cursor_address != N1_GLOBAL_CURSOR_STORE_RELPATH


def test_s3_n_gt_1_isolation_distinct_store_roots_and_cursor_addresses(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in LANE_IDS}
    shuffled = {
        "LANE_5": pairs["LANE_5"],
        "LANE_1": pairs["LANE_1"],
        "LANE_4": pairs["LANE_4"],
        "LANE_2": pairs["LANE_2"],
        "LANE_3": pairs["LANE_3"],
    }
    bound_seam = bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(shuffled)
    assert list(bound_seam) == list(LANE_IDS)
    roots = [item[1] for item in bound_seam.values()]
    cursors = [item[2] for item in bound_seam.values()]
    assert len(roots) == len(set(roots))
    assert len(cursors) == len(set(cursors))
    assert CURSOR_FILENAME_SHARED_ACROSS_LANES is True
    for lane_id in LANE_IDS:
        bound, root, cursor_address = bound_seam[lane_id]
        assert bound is pairs[lane_id][1]
        assert root == pairs[lane_id][0].lane_state_root
        assert cursor_address == lane_state_root_key(Path(root) / CURSOR_FILENAME)
        assert cursor_address.endswith("/" + CURSOR_FILENAME)
        for other_id in LANE_IDS:
            if other_id == lane_id:
                continue
            assert bound_seam[lane_id][1] != bound_seam[other_id][1]
            assert bound_seam[lane_id][2] != bound_seam[other_id][2]


def test_s3_occupied_only_omits_absent_lanes(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1"),
        "LANE_4": _pair(tmp_path, "LANE_4"),
    }
    bound_seam = bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(pairs)
    assert list(bound_seam) == ["LANE_1", "LANE_4"]
    assert "LANE_2" not in bound_seam
    assert "LANE_3" not in bound_seam
    assert "LANE_5" not in bound_seam


def test_s3_cursor_filename_alias_fails_closed(tmp_path: Path) -> None:
    lane1 = tmp_path / "LANE_1"
    lane2 = tmp_path / "LANE_2"
    lane1.mkdir()
    lane2.mkdir()
    cursor1 = lane1 / CURSOR_FILENAME
    cursor1.write_text("{}", encoding="utf-8")
    (lane2 / CURSOR_FILENAME).symlink_to(cursor1)
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(
            {
                "LANE_1": _pair(tmp_path, "LANE_1"),
                "LANE_2": _pair(tmp_path, "LANE_2"),
            }
        )
    assert exc.value.failure_code == FAILURE_CURSOR_ADDRESS_ALIAS
    assert "LANE_1" in exc.value.detail
    assert "LANE_2" in exc.value.detail


def test_s3_n1_global_cursor_rejected_at_seam(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(
            {
                "LANE_1": _pair(
                    tmp_path,
                    "LANE_1",
                    lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH,
                )
            }
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE


def test_s3_missing_and_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root="   ")}
        )
    assert exc.value.failure_code == FAILURE_MISSING_STORE_ROOT
    wrong_root = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_2")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root=wrong_root)}
        )
    assert exc.value.failure_code == FAILURE_INVALID_STORE_ROOT


def test_s3_no_consumer_cursor_cap61_or_runtime_side_effects() -> None:
    bind_source = inspect.getsource(bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1)
    assert "run_current_productive_master_v2_runtime_cycle_v1(" not in bind_source
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in bind_source
    assert "load_current_productive_sidestate_confirmation_cursor_v1(" not in bind_source
    assert "restore_current_productive_sidestate_confirmation_cursor_v1(" not in JOIN_SOURCE
    assert "ensure_host_confirmation_binding_v1(" not in JOIN_SOURCE
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert "resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1" in JOIN_SOURCE
    assert THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER is True
    assert MAY_PERSIST_CURSOR is True
    assert MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK is True
    assert PERSIST_ENABLED is True
    assert PERSIST_SURFACE_OWNER == CURSOR_OWNER
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert inspect.getsource(bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1)


def _invoke_kwargs() -> dict[str, object]:
    return {
        "cycle_id_prefix": "s4-harness",
        "observed_unix": 1_700_000_000.0,
        "mark_px": 100.0,
        "index_px": 100.0,
        "bid_px": 99.5,
        "ask_px": 100.5,
        "volume": 10.0,
        "open_interest": 20.0,
        "funding_rate": 0.0001,
        "finalized_closes": (98.0, 99.0, 100.0),
        "last_finalized_event_ts_unix": 1_699_999_940.0,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
    }


def test_s4_n1_parity_matches_direct_cycle(tmp_path: Path) -> None:
    pair = _pair(tmp_path, "LANE_3")
    kwargs = _invoke_kwargs()
    invoked = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_3": pair},
        **kwargs,  # type: ignore[arg-type]
    )
    direct = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=pair[1],
        cycle_id="s4-harness:LANE_3",
        observed_unix=kwargs["observed_unix"],  # type: ignore[arg-type]
        mark_px=kwargs["mark_px"],  # type: ignore[arg-type]
        index_px=kwargs["index_px"],  # type: ignore[arg-type]
        bid_px=kwargs["bid_px"],  # type: ignore[arg-type]
        ask_px=kwargs["ask_px"],  # type: ignore[arg-type]
        volume=kwargs["volume"],  # type: ignore[arg-type]
        open_interest=kwargs["open_interest"],  # type: ignore[arg-type]
        funding_rate=kwargs["funding_rate"],  # type: ignore[arg-type]
        finalized_closes=kwargs["finalized_closes"],  # type: ignore[arg-type]
        last_finalized_event_ts_unix=kwargs["last_finalized_event_ts_unix"],  # type: ignore[arg-type]
        venue_flat=kwargs["venue_flat"],  # type: ignore[arg-type]
        existing_position_side=kwargs["existing_position_side"],  # type: ignore[arg-type]
        incoming_cursor=None,
    )
    assert list(invoked) == ["LANE_3"]
    record = invoked["LANE_3"]
    assert isinstance(record, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1)
    assert record.bound_instrument is pair[1]
    assert record.store_root == pair[0].lane_state_root
    assert record.incoming_cursor is None
    assert record.persist_enabled is False
    assert record.cap61_state_root_bound is False
    assert record.cycle_result.cycle_id == "s4-harness:LANE_3"
    assert record.cycle_result.decision_outcome == direct.decision_outcome
    assert record.cycle_result.fail_reasons == direct.fail_reasons
    assert record.cycle_result.cursor_restore_status == direct.cursor_restore_status
    assert INVOCATION_CONTEXT == "BOUNDED_TEST_HARNESS_LANE_ISOLATED"
    assert not (Path(record.store_root) / CURSOR_FILENAME).exists()


def test_s4_n_gt_1_distinct_invocations_and_no_root_alias(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in ("LANE_1", "LANE_4", "LANE_5")}
    shuffled = {"LANE_5": pairs["LANE_5"], "LANE_1": pairs["LANE_1"], "LANE_4": pairs["LANE_4"]}
    invoked = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        shuffled,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    assert list(invoked) == ["LANE_1", "LANE_4", "LANE_5"]
    roots = [item.store_root for item in invoked.values()]
    cursors = [item.cursor_address for item in invoked.values()]
    results = [item.cycle_result for item in invoked.values()]
    assert len(set(roots)) == 3
    assert len(set(cursors)) == 3
    assert len({id(item) for item in results}) == 3
    for lane_id, record in invoked.items():
        assert record.lane_id == lane_id
        assert record.bound_instrument is pairs[lane_id][1]
        assert record.bound_instrument.instrument_id == f"INST-{lane_id}"
        assert record.store_root == pairs[lane_id][0].lane_state_root
        assert record.cycle_result.cycle_id == f"s4-harness:{lane_id}"
        assert record.persist_enabled is False
        assert record.cap61_state_root_bound is False
        assert record.incoming_cursor is None
        assert record.store_root != N1_GLOBAL_CURSOR_STORE_RELPATH
        assert not (Path(record.store_root) / CURSOR_FILENAME).exists()


def test_s4_incoming_cursor_and_n1_path_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
            {"LANE_1": _pair(tmp_path, "LANE_1")},
            incoming_cursor=object(),
            **_invoke_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_INCOMING_CURSOR_FORBIDDEN
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
            {
                "LANE_2": _pair(
                    tmp_path,
                    "LANE_2",
                    lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH,
                )
            },
            **_invoke_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    invoke_source = inspect.getsource(invoke_occupied_lane_mv2_dp_decision_state_consumer_v1)
    assert "incoming_cursor=None" in invoke_source
    invoke_cycle = invoke_source.split("run_current_productive_master_v2_runtime_cycle_v1(", 1)[
        1
    ].split(")", 1)[0]
    assert "productive_layered_core_bind_cycle_kwargs_v1(" in invoke_cycle
    assert " store_root=" not in invoke_cycle
    assert "persist=" not in invoke_source
    assert MAY_PERSIST_CURSOR is True
    assert MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK is True
    assert PERSIST_ENABLED is True
    assert PERSIST_SURFACE_OWNER == CURSOR_OWNER
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def _memory_g17_producer(*, instrument_id: str, venue_native_id: str) -> object:
    venue = "OKX"
    t0 = 1_700_000_000.0
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=venue,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
        persistence_path=None,
    )
    for index in range(61):
        sample = MarketSampleIdentityV1(
            venue=venue,
            canonical_instrument_id=instrument_id,
            venue_instrument_id=venue_native_id,
            event_time=EventTimeInstantV1(unix_seconds=t0 + float(index * 60)),
            mark_price=100.0 * math.exp(0.001 * index),
        )
        producer.ingest_finalized_pt1m_mark_sample_v1(
            sample=sample,
            transport=ObservationTransportMetadataV1(receive_time=t0 + index * 60 + 0.5),
        )
    return producer


def _lane_g17_producers(
    pairs: dict[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> dict[str, object]:
    return {
        lane_id: _memory_g17_producer(
            instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
        )
        for lane_id, (_slot, bound) in pairs.items()
    }


def _carry_kwargs(*, cycle_id_prefix: str = "s5-cycle-2") -> dict[str, object]:
    kwargs = _invoke_kwargs()
    kwargs["cycle_id_prefix"] = cycle_id_prefix
    return kwargs


def test_s5_reuses_existing_invocation_cursor_without_new_owner() -> None:
    assert S5_JOIN_SYMBOL == "carry_occupied_lane_mv2_dp_decision_state_in_memory_v1"
    assert S5_IMPLEMENTED is True
    assert IN_MEMORY_CURSOR_HOLDER == (
        "OccupiedLaneMv2DpDecisionStateConsumerInvocationV1.cycle_result.outgoing_cursor"
    )
    assert NEW_STATE_OWNER_CREATED is False
    assert LANE_STATE_ROOT_ROLE == "EXTERNAL_ADDRESSING_ONLY"
    assert CURSOR_SCHEMA_CHANGED is False
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert getattr(addressing_pkg, S5_JOIN_SYMBOL) is (
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1
    )
    carry_source = inspect.getsource(carry_occupied_lane_mv2_dp_decision_state_in_memory_v1)
    cycle_call = carry_source.split("run_current_productive_master_v2_runtime_cycle_v1(", 1)[
        1
    ].split(")", 1)[0]
    assert "incoming_cursor=lane_cursor" in cycle_call
    assert "productive_layered_core_bind_cycle_kwargs_v1(" in cycle_call
    assert " store_root=" not in cycle_call
    assert "persist=" not in carry_source
    assert "state_root=" not in carry_source
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in carry_source
    assert "load_current_productive_sidestate_confirmation_cursor_v1(" not in carry_source
    assert "restore_current_productive_sidestate_confirmation_cursor_v1(" not in JOIN_SOURCE
    assert "open(" not in JOIN_SOURCE
    assert "write_text" not in JOIN_SOURCE
    assert "CurrentProductiveSideStateConfirmationCursorV1" not in JOIN_SOURCE


def test_s5_n1_two_cycle_parity(tmp_path: Path) -> None:
    pair = _pair(tmp_path, "LANE_3")
    producers = _lane_g17_producers({"LANE_3": pair})
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_3": pair},
        g17_typed_vol_producers=producers,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    outgoing = first["LANE_3"].cycle_result.outgoing_cursor
    assert outgoing is not None
    second_kwargs = _carry_kwargs()
    second = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        {"LANE_3": pair},
        first,
        g17_typed_vol_producers=producers,
        **second_kwargs,  # type: ignore[arg-type]
    )
    direct = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=pair[1],
        cycle_id="s5-cycle-2:LANE_3",
        observed_unix=second_kwargs["observed_unix"],  # type: ignore[arg-type]
        mark_px=second_kwargs["mark_px"],  # type: ignore[arg-type]
        index_px=second_kwargs["index_px"],  # type: ignore[arg-type]
        bid_px=second_kwargs["bid_px"],  # type: ignore[arg-type]
        ask_px=second_kwargs["ask_px"],  # type: ignore[arg-type]
        volume=second_kwargs["volume"],  # type: ignore[arg-type]
        open_interest=second_kwargs["open_interest"],  # type: ignore[arg-type]
        funding_rate=second_kwargs["funding_rate"],  # type: ignore[arg-type]
        finalized_closes=second_kwargs["finalized_closes"],  # type: ignore[arg-type]
        last_finalized_event_ts_unix=second_kwargs["last_finalized_event_ts_unix"],  # type: ignore[arg-type]
        venue_flat=second_kwargs["venue_flat"],  # type: ignore[arg-type]
        existing_position_side=second_kwargs["existing_position_side"],  # type: ignore[arg-type]
        incoming_cursor=outgoing,
        g17_typed_vol_producer=producers["LANE_3"],
        **productive_layered_core_bind_cycle_kwargs_v1(
            layered_core_store_root=pair[0].lane_state_root,
            incoming_cursor=outgoing,
        ),
    )
    record = second["LANE_3"]
    assert record.incoming_cursor is outgoing
    assert record.persist_enabled is False
    assert record.cap61_state_root_bound is False
    assert record.store_root == pair[0].lane_state_root
    assert record.cycle_result.decision_outcome == direct.decision_outcome
    assert record.cycle_result.fail_reasons == direct.fail_reasons
    assert record.cycle_result.cursor_restore_status == direct.cursor_restore_status
    assert record.cycle_result.cursor_restore_status == "restored"
    assert record.cycle_result.outgoing_cursor is not None
    assert direct.outgoing_cursor is not None
    assert record.cycle_result.outgoing_cursor.to_dict() == direct.outgoing_cursor.to_dict()
    assert not (Path(record.store_root) / CURSOR_FILENAME).exists()


def test_s5_n_gt_1_isolation_and_permutation(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in ("LANE_1", "LANE_4")}
    producers = _lane_g17_producers(pairs)
    shuffled_producers = {"LANE_4": producers["LANE_4"], "LANE_1": producers["LANE_1"]}
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_4": pairs["LANE_4"], "LANE_1": pairs["LANE_1"]},
        g17_typed_vol_producers=shuffled_producers,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    assert list(first) == ["LANE_1", "LANE_4"]
    second = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        {"LANE_4": pairs["LANE_4"], "LANE_1": pairs["LANE_1"]},
        {"LANE_4": first["LANE_4"], "LANE_1": first["LANE_1"]},
        g17_typed_vol_producers=shuffled_producers,
        **_carry_kwargs(),  # type: ignore[arg-type]
    )
    assert list(second) == ["LANE_1", "LANE_4"]
    for lane_id in ("LANE_1", "LANE_4"):
        outgoing = first[lane_id].cycle_result.outgoing_cursor
        assert outgoing is not None
        assert second[lane_id].incoming_cursor is outgoing
        assert second[lane_id].bound_instrument.instrument_id == f"INST-{lane_id}"
        assert not (Path(second[lane_id].store_root) / CURSOR_FILENAME).exists()
    assert second["LANE_1"].incoming_cursor is not second["LANE_4"].incoming_cursor
    assert first["LANE_1"].cycle_result.outgoing_cursor is not second["LANE_4"].incoming_cursor
    third = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        pairs,
        second,
        g17_typed_vol_producers=producers,
        **_carry_kwargs(cycle_id_prefix="s5-cycle-3"),  # type: ignore[arg-type]
    )
    assert third["LANE_1"].incoming_cursor is second["LANE_1"].cycle_result.outgoing_cursor
    assert third["LANE_4"].incoming_cursor is second["LANE_4"].cycle_result.outgoing_cursor
    assert "LANE_2" not in third


def test_s5_interleaved_subset_does_not_leak(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in ("LANE_2", "LANE_5")}
    producers = _lane_g17_producers(pairs)
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        pairs,
        g17_typed_vol_producers=producers,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    later_5 = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        {"LANE_5": pairs["LANE_5"]},
        {"LANE_5": first["LANE_5"]},
        g17_typed_vol_producers={"LANE_5": producers["LANE_5"]},
        **_carry_kwargs(cycle_id_prefix="s5-interleave-5"),  # type: ignore[arg-type]
    )
    later_2 = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        {"LANE_2": pairs["LANE_2"]},
        {"LANE_2": first["LANE_2"]},
        g17_typed_vol_producers={"LANE_2": producers["LANE_2"]},
        **_carry_kwargs(cycle_id_prefix="s5-interleave-2"),  # type: ignore[arg-type]
    )
    assert later_5["LANE_5"].incoming_cursor is first["LANE_5"].cycle_result.outgoing_cursor
    assert later_2["LANE_2"].incoming_cursor is first["LANE_2"].cycle_result.outgoing_cursor
    assert later_2["LANE_2"].incoming_cursor is not later_5["LANE_5"].incoming_cursor
    assert "LANE_5" not in later_2
    assert "LANE_2" not in later_5


def test_s5_missing_mismatched_and_aliased_lane_state_fail_closed(tmp_path: Path) -> None:
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in ("LANE_1", "LANE_2")}
    producers = _lane_g17_producers(pairs)
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        pairs,
        g17_typed_vol_producers=producers,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            pairs,
            {"LANE_1": first["LANE_1"]},
            g17_typed_vol_producers=producers,
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_MISSING_LANE_STATE
    blocked = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_1": pairs["LANE_1"]},
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    assert blocked["LANE_1"].cycle_result.outgoing_cursor is None
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            {"LANE_1": pairs["LANE_1"]},
            blocked,
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_MISSING_LANE_STATE
    cursor = first["LANE_1"].cycle_result.outgoing_cursor
    assert cursor is not None
    mismatched_cursor = replace(cursor, instrument_id="INST-OTHER")
    mismatched = replace(
        first["LANE_1"],
        cycle_result=replace(first["LANE_1"].cycle_result, outgoing_cursor=mismatched_cursor),
    )
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            {"LANE_1": pairs["LANE_1"]},
            {"LANE_1": mismatched},
            g17_typed_vol_producers={"LANE_1": producers["LANE_1"]},
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_MISMATCHED_LANE_STATE
    shared = _bound(lane_id="LANE_1", instrument_id="INST-SHARED")
    shared_2 = BoundInstrumentV1(
        instrument_id=shared.instrument_id,
        venue_native_id=shared.venue_native_id,
        ranking_snapshot_id=shared.ranking_snapshot_id,
        ranking_integrity_digest=shared.ranking_integrity_digest,
        universe_snapshot_id=shared.universe_snapshot_id,
        selection_id="sel-shared-2",
        selection_integrity_digest="sel-digest-shared-2",
        selection_state="SELECTED",
    )
    pair_1 = _pair(tmp_path, "LANE_1", bound=shared)
    pair_2 = _pair(tmp_path, "LANE_2", bound=shared_2)
    alias_producers = {
        "LANE_1": _memory_g17_producer(
            instrument_id=shared.instrument_id,
            venue_native_id=shared.venue_native_id,
        ),
        "LANE_2": _memory_g17_producer(
            instrument_id=shared_2.instrument_id,
            venue_native_id=shared_2.venue_native_id,
        ),
    }
    origin = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_1": pair_1},
        g17_typed_vol_producers={"LANE_1": alias_producers["LANE_1"]},
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )["LANE_1"]
    aliased = replace(
        origin,
        lane_id="LANE_2",
        store_root=pair_2[0].lane_state_root,
        bound_instrument=shared_2,
    )
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            {"LANE_1": pair_1, "LANE_2": pair_2},
            {"LANE_1": origin, "LANE_2": aliased},
            g17_typed_vol_producers=alias_producers,
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_ALIASED_LANE_STATE
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            {"LANE_1": pairs["LANE_1"]},
            {"LANE_1": object()},  # type: ignore[dict-item]
            g17_typed_vol_producers={"LANE_1": producers["LANE_1"]},
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_PRIOR_INVOCATION_TYPE
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
            pairs,
            first,
            g17_typed_vol_producers={"LANE_1": producers["LANE_1"], "LANE_2": producers["LANE_1"]},
            **_carry_kwargs(),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_SHARED_G17_PRODUCER
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MAY_PERSIST_CURSOR is True
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert "state_root=None" in CYCLE_SOURCE
    assert "persist=False" in CYCLE_SOURCE


def _direct_next_cycle(
    bound,
    incoming,
    producer,
    cycle_id: str,
    *,
    layered_core_store_root: str | None = None,
):
    raw = _invoke_kwargs()
    raw.pop("cycle_id_prefix")
    return run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id=cycle_id,
        incoming_cursor=incoming,
        g17_typed_vol_producer=producer,
        **productive_layered_core_bind_cycle_kwargs_v1(
            layered_core_store_root=layered_core_store_root,
            incoming_cursor=incoming,
        ),
        **raw,  # type: ignore[arg-type]
    )


def _seed_outgoing(tmp_path: Path, lane_ids: tuple[str, ...]):
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in lane_ids}
    producers = _lane_g17_producers(pairs)
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        pairs,
        g17_typed_vol_producers=producers,
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    written = persist_occupied_lane_mv2_dp_decision_state_cursor_v1(pairs, first)
    return pairs, first, written


def test_s6_reuses_existing_cursor_owner_without_new_schema() -> None:
    assert S6_IMPLEMENTED is True
    assert S6_JOIN_SYMBOL == "restore_occupied_lane_mv2_dp_decision_state_cursor_v1"
    assert S6_PERSIST_SYMBOL == "persist_occupied_lane_mv2_dp_decision_state_cursor_v1"
    assert PERSIST_ENABLED is True
    assert PERSIST_SURFACE_OWNER == CURSOR_OWNER
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert NEW_STATE_OWNER_CREATED is False
    assert CURSOR_SCHEMA_CHANGED is False
    assert JOIN_PERSISTENCE_AUTHORITY is False
    assert MAY_CAP61_PERSIST is False
    persist_source = inspect.getsource(persist_occupied_lane_mv2_dp_decision_state_cursor_v1)
    restore_source = inspect.getsource(restore_occupied_lane_mv2_dp_decision_state_cursor_v1)
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" in persist_source
    assert "load_current_productive_sidestate_confirmation_cursor_v1(" in restore_source
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in restore_source
    assert "load_current_productive_sidestate_confirmation_cursor_v1(" not in persist_source
    owner_persist = inspect.getsource(persist_current_productive_sidestate_confirmation_cursor_v1)
    assert "path.write_text" in owner_persist
    assert "os.replace" not in owner_persist
    assert "NamedTemporaryFile" not in owner_persist
    restore_cycle = restore_source.split("run_current_productive_master_v2_runtime_cycle_v1(", 1)[
        1
    ].split(")", 1)[0]
    assert "incoming_cursor=incoming" in restore_cycle
    assert "productive_layered_core_bind_cycle_kwargs_v1(" in restore_cycle
    assert " store_root=" not in restore_cycle
    assert "state_root=" not in restore_source
    assert "CurrentProductiveSideStateConfirmationCursorV1" not in JOIN_SOURCE


def test_s6_n1_persist_restart_restore_parity(tmp_path: Path) -> None:
    pairs, first, written = _seed_outgoing(tmp_path, ("LANE_3",))
    outgoing = first["LANE_3"].cycle_result.outgoing_cursor
    assert outgoing is not None
    assert written["LANE_3"] == lane_state_root_key(
        Path(pairs["LANE_3"][0].lane_state_root) / CURSOR_FILENAME
    )
    del first
    restored = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s6-restart"),  # type: ignore[arg-type]
    )
    loaded = restored["LANE_3"].incoming_cursor
    assert loaded == outgoing.to_dict()
    direct = _direct_next_cycle(
        pairs["LANE_3"][1],
        outgoing,
        _memory_g17_producer(
            instrument_id=pairs["LANE_3"][1].instrument_id,
            venue_native_id=pairs["LANE_3"][1].venue_native_id,
        ),
        "s6-memory:LANE_3",
        layered_core_store_root=pairs["LANE_3"][0].lane_state_root,
    )
    disk = _direct_next_cycle(
        pairs["LANE_3"][1],
        loaded,
        _memory_g17_producer(
            instrument_id=pairs["LANE_3"][1].instrument_id,
            venue_native_id=pairs["LANE_3"][1].venue_native_id,
        ),
        "s6-disk:LANE_3",
        layered_core_store_root=pairs["LANE_3"][0].lane_state_root,
    )
    assert disk.decision_outcome == direct.decision_outcome
    assert disk.cursor_restore_status == direct.cursor_restore_status == "restored"
    assert restored["LANE_3"].persist_enabled is False
    assert restored["LANE_3"].cap61_state_root_bound is False


def test_s6_n_gt_1_distinct_roots_survive_restart(tmp_path: Path) -> None:
    pairs, first, written = _seed_outgoing(tmp_path, ("LANE_1", "LANE_5"))
    assert written["LANE_1"] != written["LANE_5"]
    restored = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s6-n5"),  # type: ignore[arg-type]
    )
    for lane_id in ("LANE_1", "LANE_5"):
        outgoing = first[lane_id].cycle_result.outgoing_cursor
        assert outgoing is not None
        assert restored[lane_id].incoming_cursor == outgoing.to_dict()
        assert restored[lane_id].store_root == pairs[lane_id][0].lane_state_root
    assert restored["LANE_1"].incoming_cursor != restored["LANE_5"].incoming_cursor


def test_s6_cross_lane_file_rejected_and_interleaved_isolated(tmp_path: Path) -> None:
    left = {"LANE_1": _pair(tmp_path, "LANE_1")}
    right = {"LANE_5": _pair(tmp_path / "other", "LANE_5")}
    left_first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        left,
        g17_typed_vol_producers=_lane_g17_producers(left),
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    right_first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        right,
        g17_typed_vol_producers=_lane_g17_producers(right),
        **_invoke_kwargs(),  # type: ignore[arg-type]
    )
    persist_occupied_lane_mv2_dp_decision_state_cursor_v1(left, left_first)
    persist_occupied_lane_mv2_dp_decision_state_cursor_v1(right, right_first)
    left_only = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        left,
        g17_typed_vol_producers=_lane_g17_producers(left),
        **_carry_kwargs(cycle_id_prefix="s6-left"),  # type: ignore[arg-type]
    )
    right_only = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        right,
        g17_typed_vol_producers=_lane_g17_producers(right),
        **_carry_kwargs(cycle_id_prefix="s6-right"),  # type: ignore[arg-type]
    )
    assert left_only["LANE_1"].incoming_cursor == (
        left_first["LANE_1"].cycle_result.outgoing_cursor.to_dict()
    )
    assert right_only["LANE_5"].incoming_cursor == (
        right_first["LANE_5"].cycle_result.outgoing_cursor.to_dict()
    )
    foreign = Path(right["LANE_5"][0].lane_state_root) / CURSOR_FILENAME
    foreign.write_text(
        (Path(left["LANE_1"][0].lane_state_root) / CURSOR_FILENAME).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
            right,
            g17_typed_vol_producers=_lane_g17_producers(right),
            **_carry_kwargs(cycle_id_prefix="s6-foreign"),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_MISMATCHED_LANE_STATE
    assert exc.value.detail == "LANE_5"


def test_s6_missing_file_follows_existing_load_none(tmp_path: Path) -> None:
    pairs = {"LANE_2": _pair(tmp_path, "LANE_2")}
    restored = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        **_carry_kwargs(cycle_id_prefix="s6-missing"),  # type: ignore[arg-type]
    )
    assert restored["LANE_2"].incoming_cursor is None
    assert restored["LANE_2"].cycle_result.cursor_restore_status == "missing"


def test_s6_corrupt_and_schema_follow_existing_contract(tmp_path: Path) -> None:
    pairs, _first, _written = _seed_outgoing(tmp_path, ("LANE_4",))
    path = Path(pairs["LANE_4"][0].lane_state_root) / CURSOR_FILENAME
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    payload["schema_name"] = "not-the-canonical-schema"
    path.write_text(json.dumps(payload), encoding="utf-8")
    restored = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s6-schema"),  # type: ignore[arg-type]
    )
    direct = _direct_next_cycle(
        pairs["LANE_4"][1],
        payload,
        _memory_g17_producer(
            instrument_id=pairs["LANE_4"][1].instrument_id,
            venue_native_id=pairs["LANE_4"][1].venue_native_id,
        ),
        "s6-schema-direct",
        layered_core_store_root=pairs["LANE_4"][0].lane_state_root,
    )
    assert restored["LANE_4"].cycle_result.cursor_restore_status == direct.cursor_restore_status
    assert direct.cursor_restore_status == "refused_mismatch"
    payload["schema_name"] = json.loads(original)["schema_name"]
    payload["side_state"] = "NOT_A_SIDESTATE"
    path.write_text(json.dumps(payload), encoding="utf-8")
    invalid = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s6-invalid"),  # type: ignore[arg-type]
    )
    direct_invalid = _direct_next_cycle(
        pairs["LANE_4"][1],
        payload,
        _memory_g17_producer(
            instrument_id=pairs["LANE_4"][1].instrument_id,
            venue_native_id=pairs["LANE_4"][1].venue_native_id,
        ),
        "s6-invalid-direct",
        layered_core_store_root=pairs["LANE_4"][0].lane_state_root,
    )
    assert invalid["LANE_4"].cycle_result.cursor_restore_status == (
        direct_invalid.cursor_restore_status
    )
    assert direct_invalid.cursor_restore_status == "fail_closed_invalid_sidestate"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(CurrentProductiveCursorError) as exc:
        restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
            pairs,
            **_carry_kwargs(cycle_id_prefix="s6-corrupt"),  # type: ignore[arg-type]
        )
    assert exc.value.reason_code == "CURSOR_FILE_CORRUPT"


def test_s6_n1_global_root_still_rejected(tmp_path: Path) -> None:
    pairs, first, _written = _seed_outgoing(tmp_path, ("LANE_1",))
    blocked = {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH)}
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        persist_occupied_lane_mv2_dp_decision_state_cursor_v1(blocked, first)
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
            blocked,
            **_carry_kwargs(cycle_id_prefix="s6-n1"),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_s7_reuses_s6_restore_then_persist_without_new_owner() -> None:
    assert S7_IMPLEMENTED is True
    assert S7_JOIN_SYMBOL == "compose_occupied_lane_mv2_dp_durable_cycle_v1"
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert NEW_STATE_OWNER_CREATED is False
    assert CURSOR_OWNER_CHANGE_REQUIRED is False
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert HOST_JOIN is False
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert getattr(addressing_pkg, S7_JOIN_SYMBOL) is compose_occupied_lane_mv2_dp_durable_cycle_v1
    compose_source = inspect.getsource(compose_occupied_lane_mv2_dp_durable_cycle_v1)
    restore_source = inspect.getsource(restore_occupied_lane_mv2_dp_decision_state_cursor_v1)
    restore_idx = compose_source.find("restore_occupied_lane_mv2_dp_decision_state_cursor_v1(")
    persist_idx = compose_source.find("persist_occupied_lane_mv2_dp_decision_state_cursor_v1(")
    assert 0 <= restore_idx < persist_idx
    assert "run_current_productive_master_v2_runtime_cycle_v1(" not in compose_source
    assert "productive_layered_core_bind_cycle_kwargs_v1(" not in compose_source
    assert "persist_enabled=True" in compose_source
    assert "cap61_state_root_bound=False" in compose_source
    assert "persist_enabled=False" in restore_source
    assert "persist_occupied_lane_mv2_dp_decision_state_cursor_v1(" not in restore_source
    restore_cycle = restore_source.split("run_current_productive_master_v2_runtime_cycle_v1(", 1)[
        1
    ].split(")", 1)[0]
    assert "incoming_cursor=incoming" in restore_cycle
    assert "productive_layered_core_bind_cycle_kwargs_v1(" in restore_cycle
    assert " store_root=" not in restore_cycle
    assert "os.replace" not in compose_source
    assert "write_text" not in JOIN_SOURCE
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert "produce_occupied_lane_cap23_n1_selections_v1" not in JOIN_SOURCE
    assert "stateful_no_order_host_join_v1" not in JOIN_SOURCE
    assert "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation" not in (
        JOIN_SOURCE
    )


def test_s7_n1_durable_load_cycle_persist_then_restore(tmp_path: Path) -> None:
    pairs, first, _written = _seed_outgoing(tmp_path, ("LANE_3",))
    first_outgoing = first["LANE_3"].cycle_result.outgoing_cursor
    assert first_outgoing is not None
    del first
    composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-compose"),  # type: ignore[arg-type]
    )
    second_outgoing = composed["LANE_3"].cycle_result.outgoing_cursor
    assert second_outgoing is not None
    assert composed["LANE_3"].incoming_cursor == first_outgoing.to_dict()
    assert composed["LANE_3"].persist_enabled is True
    assert composed["LANE_3"].cap61_state_root_bound is False
    loaded_after_s7 = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(pairs["LANE_3"][0].lane_state_root)
    )
    assert loaded_after_s7 == second_outgoing.to_dict()
    del composed
    restored = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-after"),  # type: ignore[arg-type]
    )
    assert restored["LANE_3"].incoming_cursor == second_outgoing.to_dict()
    assert restored["LANE_3"].persist_enabled is False
    assert restored["LANE_3"].cap61_state_root_bound is False


def test_s7_missing_file_none_then_persists_new_outgoing(tmp_path: Path) -> None:
    pairs = {"LANE_2": _pair(tmp_path, "LANE_2")}
    cursor_path = Path(pairs["LANE_2"][0].lane_state_root) / CURSOR_FILENAME
    assert cursor_path.exists() is False
    composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-missing"),  # type: ignore[arg-type]
    )
    assert composed["LANE_2"].incoming_cursor is None
    assert composed["LANE_2"].cycle_result.cursor_restore_status == "missing"
    assert composed["LANE_2"].persist_enabled is True
    assert composed["LANE_2"].cap61_state_root_bound is False
    outgoing = composed["LANE_2"].cycle_result.outgoing_cursor
    assert outgoing is not None
    assert cursor_path.is_file() is True
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(pairs["LANE_2"][0].lane_state_root)
    )
    assert loaded == outgoing.to_dict()


def test_s7_n_gt_1_distinct_roots_and_no_cross_lane_leak(tmp_path: Path) -> None:
    pairs, _first, _written = _seed_outgoing(tmp_path, ("LANE_1", "LANE_5"))
    composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-n5"),  # type: ignore[arg-type]
    )
    left_root = Path(pairs["LANE_1"][0].lane_state_root)
    right_root = Path(pairs["LANE_5"][0].lane_state_root)
    assert left_root != right_root
    left_loaded = load_current_productive_sidestate_confirmation_cursor_v1(left_root)
    right_loaded = load_current_productive_sidestate_confirmation_cursor_v1(right_root)
    assert left_loaded == composed["LANE_1"].cycle_result.outgoing_cursor.to_dict()
    assert right_loaded == composed["LANE_5"].cycle_result.outgoing_cursor.to_dict()
    assert left_loaded != right_loaded
    assert composed["LANE_1"].persist_enabled is True
    assert composed["LANE_5"].persist_enabled is True
    foreign = right_root / CURSOR_FILENAME
    foreign.write_text((left_root / CURSOR_FILENAME).read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        compose_occupied_lane_mv2_dp_durable_cycle_v1(
            {"LANE_5": pairs["LANE_5"]},
            g17_typed_vol_producers=_lane_g17_producers({"LANE_5": pairs["LANE_5"]}),
            **_carry_kwargs(cycle_id_prefix="s7-foreign"),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_MISMATCHED_LANE_STATE
    assert exc.value.detail == "LANE_5"


def test_s7_corrupt_schema_and_n1_global_follow_existing_contract(tmp_path: Path) -> None:
    pairs, _first, _written = _seed_outgoing(tmp_path, ("LANE_4",))
    path = Path(pairs["LANE_4"][0].lane_state_root) / CURSOR_FILENAME
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    payload["schema_name"] = "not-the-canonical-schema"
    path.write_text(json.dumps(payload), encoding="utf-8")
    composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-schema"),  # type: ignore[arg-type]
    )
    assert composed["LANE_4"].cycle_result.cursor_restore_status == "refused_mismatch"
    assert composed["LANE_4"].persist_enabled is True
    payload["schema_name"] = json.loads(original)["schema_name"]
    payload["side_state"] = "NOT_A_SIDESTATE"
    path.write_text(json.dumps(payload), encoding="utf-8")
    restored_invalid = restore_occupied_lane_mv2_dp_decision_state_cursor_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17_producers(pairs),
        **_carry_kwargs(cycle_id_prefix="s7-invalid-restore"),  # type: ignore[arg-type]
    )
    assert restored_invalid["LANE_4"].cycle_result.cursor_restore_status == (
        "fail_closed_invalid_sidestate"
    )
    assert restored_invalid["LANE_4"].persist_enabled is False
    assert restored_invalid["LANE_4"].cycle_result.outgoing_cursor is None
    with pytest.raises(
        FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError
    ) as invalid_exc:
        compose_occupied_lane_mv2_dp_durable_cycle_v1(
            pairs,
            g17_typed_vol_producers=_lane_g17_producers(pairs),
            **_carry_kwargs(cycle_id_prefix="s7-invalid"),  # type: ignore[arg-type]
        )
    assert invalid_exc.value.failure_code == FAILURE_MISSING_LANE_STATE
    path.write_text("{", encoding="utf-8")
    with pytest.raises(CurrentProductiveCursorError) as exc:
        compose_occupied_lane_mv2_dp_durable_cycle_v1(
            pairs,
            **_carry_kwargs(cycle_id_prefix="s7-corrupt"),  # type: ignore[arg-type]
        )
    assert exc.value.reason_code == "CURSOR_FILE_CORRUPT"
    blocked = {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH)}
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as n1_exc:
        compose_occupied_lane_mv2_dp_durable_cycle_v1(
            blocked,
            **_carry_kwargs(cycle_id_prefix="s7-n1"),  # type: ignore[arg-type]
        )
    assert n1_exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def _existing_paths(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {str(path) for path in root.rglob("*")} | {str(root)}


def test_s8_join_is_implemented_without_governed_cycle_invoke() -> None:
    assert S8_IMPLEMENTED is True
    assert S8_JOIN_SYMBOL == "bind_occupied_lane_governed_cycle_store_roots_v1"
    assert S8_INTENDED_EGRESS == "dict[lane_id, (cursor_store_root, lock_root, evidence_root)]"
    assert S8_CONSUMPTION_SEAM == "pre_invoke_governed_cycle_path_params"
    assert MAY_INVOKE_GOVERNED_CYCLE is False
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert MAX_POSITIONS_EFFECTIVE == 1
    addressing_pkg = __import__(
        "src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1",
        fromlist=["*"],
    )
    assert (
        getattr(addressing_pkg, S8_JOIN_SYMBOL) is bind_occupied_lane_governed_cycle_store_roots_v1
    )
    assert callable(bind_occupied_lane_governed_cycle_store_roots_v1)
    assert bind_occupied_lane_governed_cycle_store_roots_v1.__name__ == S8_JOIN_SYMBOL
    assert f"def {S8_JOIN_SYMBOL}" not in CONSTANTS_SOURCE
    assert f"def {S8_JOIN_SYMBOL}" in JOIN_SOURCE
    bind_source = inspect.getsource(bind_occupied_lane_governed_cycle_store_roots_v1)
    assert "bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1(" in bind_source
    assert "run_current_productive_governed_cycle_v1" not in JOIN_SOURCE
    assert "run_current_productive_governed_cycle_v1(" not in bind_source
    assert "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation" not in (
        JOIN_SOURCE
    )
    assert "stateful_no_order_host_join_v1" not in JOIN_SOURCE
    assert "compose_occupied_lane_mv2_dp_handoff_v1" not in JOIN_SOURCE
    assert "produce_occupied_lane_cap23_n1_selections_v1" not in JOIN_SOURCE
    assert "run_single_selected_future_policy_v1" not in JOIN_SOURCE
    assert "run_single_selected_future_runtime_binding_gate_v1" not in JOIN_SOURCE
    assert "mkdir" not in bind_source
    assert "write_text" not in bind_source
    assert "open(" not in bind_source
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    compose_source = inspect.getsource(compose_occupied_lane_mv2_dp_durable_cycle_v1)
    restore_source = inspect.getsource(restore_occupied_lane_mv2_dp_decision_state_cursor_v1)
    restore_idx = compose_source.find("restore_occupied_lane_mv2_dp_decision_state_cursor_v1(")
    persist_idx = compose_source.find("persist_occupied_lane_mv2_dp_decision_state_cursor_v1(")
    assert 0 <= restore_idx < persist_idx
    assert "bind_occupied_lane_governed_cycle_store_roots_v1(" not in compose_source
    assert "persist_enabled=False" in restore_source
    assert "persist_occupied_lane_mv2_dp_decision_state_cursor_v1(" not in restore_source


def test_s8_n1_binds_three_lane_local_roots_without_disk_write(tmp_path: Path) -> None:
    pairs = {"LANE_3": _pair(tmp_path, "LANE_3")}
    before = _existing_paths(tmp_path)
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    after = _existing_paths(tmp_path)
    assert after == before
    assert list(addressed) == ["LANE_3"]
    cursor_store_root, lock_root, evidence_root = addressed["LANE_3"]
    expected_store = lane_state_root_for(topology_state_root_base=tmp_path, lane_id="LANE_3")
    assert cursor_store_root == expected_store
    assert cursor_store_root == pairs["LANE_3"][0].lane_state_root
    assert lock_root == lane_state_root_key(Path(expected_store) / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME)
    assert evidence_root == lane_state_root_key(
        Path(expected_store) / GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME
    )
    assert cursor_store_root != lock_root != evidence_root
    assert cursor_store_root != evidence_root
    assert lock_root.startswith(cursor_store_root)
    assert evidence_root.startswith(cursor_store_root)
    assert cursor_store_root != N1_GLOBAL_CURSOR_STORE_RELPATH
    assert lock_root != N1_GLOBAL_CURSOR_STORE_RELPATH
    assert evidence_root != N1_GLOBAL_CURSOR_STORE_RELPATH
    assert N1_GLOBAL_CURSOR_STORE_RELPATH not in cursor_store_root
    assert HOST_JOIN is False
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"


def test_s8_n_gt_1_lane_1_and_5_root_sets_are_disjoint(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1"),
        "LANE_5": _pair(tmp_path, "LANE_5"),
    }
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    assert list(addressed) == ["LANE_1", "LANE_5"]
    left = set(addressed["LANE_1"])
    right = set(addressed["LANE_5"])
    assert len(left) == 3
    assert len(right) == 3
    assert left.isdisjoint(right)
    for lane_id, (cursor_store_root, lock_root, evidence_root) in addressed.items():
        expected = pairs[lane_id][0].lane_state_root
        assert cursor_store_root == expected
        assert lock_root == lane_state_root_key(Path(expected) / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME)
        assert evidence_root == lane_state_root_key(
            Path(expected) / GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME
        )


def test_s8_cross_lane_lock_alias_fails_closed(tmp_path: Path) -> None:
    pairs = {
        "LANE_1": _pair(tmp_path, "LANE_1"),
        "LANE_2": _pair(tmp_path, "LANE_2"),
    }
    left_lock = Path(pairs["LANE_1"][0].lane_state_root) / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME
    right_lock = Path(pairs["LANE_2"][0].lane_state_root) / GOVERNED_CYCLE_LOCK_ROOT_DIRNAME
    left_lock.mkdir(parents=True)
    Path(pairs["LANE_2"][0].lane_state_root).mkdir(parents=True)
    right_lock.symlink_to(left_lock)
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    assert exc.value.failure_code == FAILURE_SHARED_STORE_ROOT
    assert "LANE_1" in exc.value.detail
    assert "LANE_2" in exc.value.detail


def test_s8_n1_global_cursor_relpath_rejected(tmp_path: Path) -> None:
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_governed_cycle_store_roots_v1(
            {
                "LANE_1": _pair(
                    tmp_path,
                    "LANE_1",
                    lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH,
                )
            }
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE


def test_s8_empty_unoccupied_skipped_and_occupancy_mismatch_fail_closed(tmp_path: Path) -> None:
    assert bind_occupied_lane_governed_cycle_store_roots_v1({}) == {}
    occupied = {
        "LANE_1": _pair(tmp_path, "LANE_1"),
        "LANE_4": _pair(tmp_path, "LANE_4"),
    }
    addressed = bind_occupied_lane_governed_cycle_store_roots_v1(occupied)
    assert list(addressed) == ["LANE_1", "LANE_4"]
    assert "LANE_2" not in addressed
    assert "LANE_3" not in addressed
    assert "LANE_5" not in addressed
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        bind_occupied_lane_governed_cycle_store_roots_v1(
            {"LANE_5": _pair(tmp_path, "LANE_5", occupancy=OCCUPANCY_EMPTY)}
        )
    assert exc.value.failure_code == FAILURE_OCCUPANCY
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert MAY_INVOKE_GOVERNED_CYCLE is False
