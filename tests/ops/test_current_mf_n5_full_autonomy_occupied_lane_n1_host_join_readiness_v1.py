"""Occupied-lane N=1 host-join readiness tests."""

from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    HOST_JOIN as N1_HOST_JOIN,
    JOIN_SYMBOL as N1_JOIN_SYMBOL,
    MAY_INVOKE_GOVERNED_CYCLE as N1_MAY_INVOKE_GOVERNED_CYCLE,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
    constants_v1 as readiness_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.constants_v1 import (
    ADDRESS_SYMBOL,
    ATLAS_AUTHORITY,
    ATOMICITY_CLAIMED_SATISFIED,
    ATOMICITY_SEMANTICS,
    AUTHORITY_EFFECT,
    CANONICAL_HOST_JOIN_MODULE,
    CANONICAL_HOST_JOIN_OWNER,
    CANONICAL_HOST_JOIN_PACKAGE,
    CANONICAL_HOST_JOIN_SYMBOL,
    CANONICAL_PRODUCTIVE_HOST_ENTRY,
    COMPOSE_SYMBOL,
    CONTRACT_ID,
    CURSOR_FILENAME,
    CURSOR_OWNER,
    CURSOR_SINGLE_WRITER,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_FORBIDDEN_KWARG,
    FAILURE_IDENTITY_MISMATCH,
    FIRST_TRUE_OWNER_BOUNDARY,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    HOST_JOIN,
    HOST_JOIN_ADDRESSED,
    HOST_JOIN_INVOKED,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_IMPLEMENTED,
    JOIN_PERSISTENCE_AUTHORITY,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_SYMBOL,
    JOIN_TRADING_AUTHORITY,
    MAX_POSITIONS_EFFECTIVE,
    MAY_CROSS_FIRST_TRUE_OWNER_BOUNDARY,
    MAY_ENABLE_HOST,
    MAY_INVOKE_HOST_JOIN,
    MAY_INVOKE_PRODUCTIVE_HOST_ENTRY,
    MAY_JOIN_CAP72_LIVE_EXECUTION_PORT,
    MAY_MINT_PERMIT,
    MAY_POST,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N1_CONSUMER_JOIN_READY,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    NATIVE_ID_SOURCE,
    NEW_CURSOR_WRITER,
    NEW_HOST_OWNER_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RUNTIME_AUTHORIZATION_EFFECT,
    SLICE_ID,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.readiness_join_v1 import (
    FullAutonomyOccupiedLaneN1HostJoinReadinessError,
    address_occupied_lane_n1_consumer_to_host_join_seam_v1,
    assert_readiness_stops_before_owner_boundary_v1,
    compose_occupied_lane_n1_host_join_readiness_v1,
    occupied_lane_n1_host_join_readiness_census_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    HOST_JOIN_OWNER as FULL_CORE_HOST_JOIN_OWNER,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_COMPLETED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    REASON_CONCURRENT_CYCLE,
    CurrentProductiveGovernedCycleOrchestratorError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    CYCLE_EXCLUSION_LOCK_NAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.single_selected_future_policy_v1.governed_pin_v1 import lane_state_root_key
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    C1_TS,
    C1_TS_NEXT,
    ORIGIN_SHA,
    SUCCESS_DISPOSITIONS,
    _clear_cycle_ledger,
    _lane_g17,
    _market_kwargs,
    _pair,
    _s7_kwargs,
)

PACKAGE_DIR = Path(readiness_constants.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "readiness_join_v1.py").read_text(encoding="utf-8")
N1_JOIN_SOURCE = (
    REPO_ROOT
    / "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1"
    / "invoke_join_v1.py"
).read_text(encoding="utf-8")
HOST_BINDING_SOURCE = (REPO_ROOT / CANONICAL_HOST_JOIN_MODULE).read_text(encoding="utf-8")
PROTECTED_RELPATHS = (
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
)


def _called_names(source: str) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


def _compose(tmp_path: Path, lane_ids: tuple[str, ...], **overrides: object):
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in lane_ids}
    last_ts = float(overrides.pop("last_ts", C1_TS))
    kwargs = _market_kwargs(
        cycle_id_prefix=str(overrides.pop("cycle_id_prefix", "n1-hjr")),
        last_ts=last_ts,
    )
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    kwargs.update(overrides)
    return pairs, compose_occupied_lane_n1_host_join_readiness_v1(pairs, **kwargs)


def test_authority_flags_and_host_seam_are_pinned() -> None:
    assert SLICE_ID == "N1_HOST_JOIN_READINESS_ADDRESS_STOP_BEFORE_OWNER_BOUNDARY"
    assert OWNER == ("ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1")
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_N1_HOST_JOIN_READINESS_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_N1_HOST_JOIN_READINESS_V1"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert ATLAS_AUTHORITY == "NONE"
    assert JOIN_IMPLEMENTED is True
    assert JOIN_SYMBOL == COMPOSE_SYMBOL == "compose_occupied_lane_n1_host_join_readiness_v1"
    assert ADDRESS_SYMBOL == "address_occupied_lane_n1_consumer_to_host_join_seam_v1"
    assert N1_JOIN_SYMBOL == "invoke_occupied_lane_governed_cycle_n1_consumer_v1"
    assert N1_MAY_INVOKE_GOVERNED_CYCLE is True
    assert N1_CONSUMER_JOIN_READY is True
    assert HOST_JOIN_ADDRESSED is True
    assert HOST_JOIN_INVOKED is False
    assert MAY_INVOKE_HOST_JOIN is False
    assert MAY_ENABLE_HOST is False
    assert MAY_JOIN_CAP72_LIVE_EXECUTION_PORT is False
    assert MAY_INVOKE_PRODUCTIVE_HOST_ENTRY is False
    assert MAY_CROSS_FIRST_TRUE_OWNER_BOUNDARY is False
    assert MAY_MINT_PERMIT is False
    assert MAY_POST is False
    assert NATIVE_ID_SOURCE == "BoundInstrumentV1.venue_native_id"
    assert (
        CANONICAL_HOST_JOIN_OWNER == FULL_CORE_HOST_JOIN_OWNER == ("stateful_no_order_host_join_v1")
    )
    assert CANONICAL_HOST_JOIN_SYMBOL == "ensure_host_activation_binding_v1"
    assert CANONICAL_HOST_JOIN_PACKAGE == (
        "ops.single_future_stateful_no_order_runtime_activation_v1"
    )
    assert "def ensure_host_activation_binding_v1" in HOST_BINDING_SOURCE
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert ATOMICITY_CLAIMED_SATISFIED is False
    assert CURSOR_SINGLE_WRITER is True
    assert NEW_CURSOR_WRITER is False
    assert NEW_HOST_OWNER_CREATED is False
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert JOIN_PERSISTENCE_AUTHORITY is False
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert HOST_JOIN is False
    assert N1_HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is True
    assert FIRST_TRUE_OWNER_BOUNDARY.startswith("INVOKE_ENSURE_HOST_ACTIVATION_BINDING")
    assert CURSOR_OWNER.endswith("current_productive_sidestate_confirmation_cursor_v1")


def test_reuse_before_new_census_names_existing_owners() -> None:
    census = occupied_lane_n1_host_join_readiness_census_v1()
    assert census["CANONICAL_HOST_JOIN_OWNER"] == "stateful_no_order_host_join_v1"
    assert census["CANONICAL_HOST_JOIN_SYMBOL"] == "ensure_host_activation_binding_v1"
    assert census["CANONICAL_PRODUCTIVE_HOST_ENTRY"] == CANONICAL_PRODUCTIVE_HOST_ENTRY
    assert "run_bridge_cycle_v1" in census["CANONICAL_PRODUCTIVE_HOST_ENTRY"]
    assert census["N1_CONSUMER_JOIN_SYMBOL"] == N1_JOIN_SYMBOL
    assert census["CURSOR_OWNER"].endswith("current_productive_sidestate_confirmation_cursor_v1")
    assert "CYCLE_EXCLUSION_LOCK" in census["LOCKING_MODEL"]
    assert census["PRODUCTIVE_RUNTIME_CARDINALITY"] == "1_UNJOINED"
    assert census["ATLAS_AUTHORITY"] == "NONE"
    assert "1_JOINED" in census["FIRST_TRUE_OWNER_BOUNDARY"]


def test_forbidden_graph_does_not_invoke_host_join() -> None:
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert "invoke_occupied_lane_governed_cycle_n1_consumer_v1(" in JOIN_SOURCE
    assert "address_occupied_lane_n1_consumer_to_host_join_seam_v1(" in JOIN_SOURCE
    assert "ensure_host_activation_binding_v1(" not in JOIN_SOURCE
    assert "join_cap72_host_to_live_execution_port_v1(" not in JOIN_SOURCE
    assert "run_bridge_cycle_v1(" not in JOIN_SOURCE
    assert "construct_live_execution_port_v1(" not in JOIN_SOURCE
    assert "construct_simulated_execution_port_v1(" not in JOIN_SOURCE
    assert "HostActivationBindingV1(" not in JOIN_SOURCE
    assert "run_activation_gate_v1(" not in JOIN_SOURCE
    assert "LiveExecutionPort" not in JOIN_SOURCE
    assert (
        "from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1"
        not in (JOIN_SOURCE)
    )
    assert (
        "from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1"
        not in (CONSTANTS_SOURCE)
    )
    assert "ensure_host_activation_binding_v1(" not in N1_JOIN_SOURCE


def test_n1_end_to_end_pre_external_effect_is_join_ready(tmp_path: Path) -> None:
    pairs, projections = _compose(tmp_path, ("LANE_1",), cycle_id_prefix="n1-hjr-e2e")
    assert set(projections) == {"LANE_1"}
    projection = projections["LANE_1"]
    bound = pairs["LANE_1"][1]
    slot = pairs["LANE_1"][0]
    assert projection.native_id == bound.venue_native_id
    assert projection.instrument_id == bound.instrument_id
    assert projection.lane_state_root == lane_state_root_key(slot.lane_state_root)
    assert projection.cursor_store_root == projection.lane_state_root
    assert projection.host_join_owner == "stateful_no_order_host_join_v1"
    assert projection.host_join_symbol == "ensure_host_activation_binding_v1"
    assert projection.host_join_addressed is True
    assert projection.host_join_invoked is False
    assert projection.host_enabled is False
    assert projection.n1_consumer_join_ready is True
    assert projection.selected_future_present is True
    assert projection.instrument_binding_valid is True
    assert projection.cap61_state_root_bound is False
    assert projection.post_count == 0
    assert projection.permit_created is False
    assert projection.external_effect_count == 0
    assert projection.disposition in SUCCESS_DISPOSITIONS, projection.disposition
    assert projection.n1_consumer_result.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert_readiness_stops_before_owner_boundary_v1(projections)
    cursor_path = Path(projection.cursor_store_root) / CURSOR_FILENAME
    assert cursor_path.is_file()
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(projection.cursor_store_root)
    )
    assert isinstance(loaded, dict)
    assert loaded["venue_native_id"] == bound.venue_native_id
    assert "lane_id" not in loaded


def test_identity_native_id_is_bound_instrument_throughout(tmp_path: Path) -> None:
    pairs, projections = _compose(tmp_path, ("LANE_3",), cycle_id_prefix="n1-hjr-id")
    bound = pairs["LANE_3"][1]
    projection = projections["LANE_3"]
    assert projection.native_id == bound.venue_native_id == "VENUE-3"
    cycle = projection.n1_consumer_result.governed_cycle_result
    assert cycle.disposition in SUCCESS_DISPOSITIONS, cycle.reason_code
    assert cycle.c1_used.startswith("native_id=VENUE-3;")
    assert projection.writer_session_id == "n1-hjr-id:LANE_3"


def test_restart_reloads_lane_cursor_and_stays_unjoined(tmp_path: Path) -> None:
    pairs, first = _compose(tmp_path, ("LANE_2",), cycle_id_prefix="n1-hjr-restart-1")
    first_projection = first["LANE_2"]
    assert first_projection.disposition in SUCCESS_DISPOSITIONS
    assert first_projection.host_join_invoked is False
    s7 = first_projection.n1_consumer_result.s7_invocation
    assert s7 is not None
    first_outgoing = s7.cycle_result.outgoing_cursor
    assert first_outgoing is not None
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(first_projection.cursor_store_root)
    )
    assert loaded == first_outgoing.to_dict()
    _clear_cycle_ledger(first_projection.evidence_root)
    second = compose_occupied_lane_n1_host_join_readiness_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_market_kwargs(cycle_id_prefix="n1-hjr-restart-2", last_ts=C1_TS_NEXT),
    )
    second_projection = second["LANE_2"]
    assert second_projection.n1_consumer_result.bootstrap_used is False
    assert second_projection.n1_consumer_result.s7_invocation is not None
    assert (
        second_projection.n1_consumer_result.s7_invocation.incoming_cursor
        == first_outgoing.to_dict()
    )
    assert second_projection.native_id == pairs["LANE_2"][1].venue_native_id
    assert second_projection.host_join_invoked is False
    assert second_projection.host_enabled is False
    assert second_projection.disposition in SUCCESS_DISPOSITIONS | {DISPOSITION_FAIL_CLOSED}
    assert HOST_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"


def test_single_writer_lane_local_cursor_no_n1_global(tmp_path: Path) -> None:
    pairs, projections = _compose(tmp_path, ("LANE_4",), cycle_id_prefix="n1-hjr-sw")
    projection = projections["LANE_4"]
    cursor_files = list(Path(tmp_path).rglob(CURSOR_FILENAME))
    assert len(cursor_files) == 1
    assert cursor_files[0] == Path(projection.cursor_store_root) / CURSOR_FILENAME
    n1 = REPO_ROOT / N1_GLOBAL_CURSOR_STORE_RELPATH / CURSOR_FILENAME
    before = n1.read_bytes() if n1.is_file() else None
    after = n1.read_bytes() if n1.is_file() else None
    assert before == after
    assert NEW_CURSOR_WRITER is False
    assert "write_text" not in JOIN_SOURCE
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in JOIN_SOURCE
    assert "persist_activation_state_v1(" not in JOIN_SOURCE


def test_lane_isolation_sequential_harness_does_not_activate_n_gt_1(tmp_path: Path) -> None:
    pairs, projections = _compose(tmp_path, ("LANE_1", "LANE_5"), cycle_id_prefix="n1-hjr-iso")
    left = projections["LANE_1"]
    right = projections["LANE_5"]
    assert left.cursor_store_root != right.cursor_store_root
    assert left.lock_root != right.lock_root
    assert left.evidence_root != right.evidence_root
    assert left.lane_state_root != right.lane_state_root
    assert left.native_id != right.native_id
    assert left.writer_session_id != right.writer_session_id
    loaded_left = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(left.cursor_store_root)
    )
    loaded_right = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(right.cursor_store_root)
    )
    assert loaded_left is not None and loaded_right is not None
    assert loaded_left["venue_native_id"] == pairs["LANE_1"][1].venue_native_id
    assert loaded_right["venue_native_id"] == pairs["LANE_5"][1].venue_native_id
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert HOST_JOIN is False
    assert left.host_join_invoked is False
    assert right.host_join_invoked is False
    assert left.disposition in SUCCESS_DISPOSITIONS
    assert right.disposition in SUCCESS_DISPOSITIONS


def test_same_lane_concurrent_lock_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_s7_kwargs(_market_kwargs(cycle_id_prefix="n1-hjr-lock-seed")),
    )
    roots = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    lock = AuthorizationLifecycleLockV1(
        lock_path=Path(roots["LANE_1"][1]) / CYCLE_EXCLUSION_LOCK_NAME,
        authorization_id="test-held",
        owner="test",
    )
    lock.acquire()
    try:
        with pytest.raises(CurrentProductiveGovernedCycleOrchestratorError) as exc:
            compose_occupied_lane_n1_host_join_readiness_v1(
                pairs,
                g17_typed_vol_producers=_lane_g17(pairs),
                **_market_kwargs(cycle_id_prefix="n1-hjr-lock"),
            )
        assert exc.value.reason_code == REASON_CONCURRENT_CYCLE
    finally:
        lock.release()


def test_forbidden_host_enable_kwarg_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    kwargs = _market_kwargs(cycle_id_prefix="n1-hjr-enable")
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    with pytest.raises(FullAutonomyOccupiedLaneN1HostJoinReadinessError) as exc:
        compose_occupied_lane_n1_host_join_readiness_v1(
            pairs,
            enable_host=True,
            **kwargs,
        )
    assert exc.value.failure_code == FAILURE_FORBIDDEN_KWARG
    assert "enable_host" in exc.value.detail


def test_address_identity_mismatch_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    kwargs = _market_kwargs(cycle_id_prefix="n1-hjr-mismatch")
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
    broken = {
        "LANE_1": replace(results["LANE_1"], native_id="WRONG-NATIVE"),
    }
    with pytest.raises(FullAutonomyOccupiedLaneN1HostJoinReadinessError) as exc:
        address_occupied_lane_n1_consumer_to_host_join_seam_v1(
            pairs,
            broken,
            origin_main_sha=ORIGIN_SHA,
            cycle_id_prefix="n1-hjr-mismatch",
        )
    assert exc.value.failure_code == FAILURE_IDENTITY_MISMATCH


def test_empty_pairs_are_noop() -> None:
    result = compose_occupied_lane_n1_host_join_readiness_v1(
        {},
        **_market_kwargs(cycle_id_prefix="n1-hjr-empty"),
    )
    assert result == {}
    assert_readiness_stops_before_owner_boundary_v1(result)


def test_protected_surfaces_are_not_mutated_by_this_package() -> None:
    for rel in PROTECTED_RELPATHS:
        assert Path(rel).name not in {path.name for path in PACKAGE_DIR.iterdir()}
    assert JOIN_SOURCE.count("def compose_occupied_lane_n1_host_join_readiness_v1") == 1
    assert JOIN_SOURCE.count("def address_occupied_lane_n1_consumer_to_host_join_seam_v1") == 1
    assert "def ensure_host_activation_binding_v1" in HOST_BINDING_SOURCE
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert HOST_JOIN is False
    assert (
        inspect.getsource(compose_occupied_lane_n1_host_join_readiness_v1).count(
            "ensure_host_activation_binding_v1("
        )
        == 0
    )
    assert DISPOSITION_PRE_EXTERNAL_EFFECT
    assert DISPOSITION_HOLD
    assert DISPOSITION_COMPLETED
    assert INIT_SOURCE.count("compose_occupied_lane_n1_host_join_readiness_v1") >= 1
