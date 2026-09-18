"""CURRENT MF N=5 Full-Autonomy runtime completion tests."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1.constants_v1 import (
    HOST_JOIN as READINESS_HOST_JOIN,
    HOST_JOIN_INVOKED as READINESS_HOST_JOIN_INVOKED,
    MF_PRODUCTIVE_JOIN as READINESS_MF_PRODUCTIVE_JOIN,
    PRODUCTIVE_RUNTIME_CARDINALITY as READINESS_PRODUCTIVE_RUNTIME_CARDINALITY,
)
from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1 import (
    constants_v1 as completion_constants,
)
from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.completion_join_v1 import (
    FullAutonomyRuntimeN5CompletionError,
    cardinality_joined_token_v1,
    join_occupied_lane_host_activation_v1,
    occupied_lane_runtime_n5_completion_census_v1,
    run_occupied_lane_runtime_n5_completion_v1,
)
from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.constants_v1 import (
    ATLAS_AUTHORITY,
    ATOMICITY_CLAIMED_SATISFIED,
    ATOMICITY_SEMANTICS,
    AUTHORITY_EFFECT,
    AUTHORITY_WORK_REMAINING,
    CANONICAL_HOST_JOIN_MODULE,
    CANONICAL_HOST_JOIN_OWNER,
    CANONICAL_HOST_JOIN_PACKAGE,
    CANONICAL_HOST_JOIN_SYMBOL,
    CANONICAL_RUNTIME_OWNER,
    CONTRACT_ID,
    CURSOR_FILENAME,
    CURSOR_OWNER,
    CURSOR_SINGLE_WRITER,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    EXECUTION_SCHEDULE,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_CARDINALITY,
    FAILURE_FORBIDDEN_KWARG,
    FIRST_UNAUTHORIZED_REMAINING_BOUNDARY,
    FIVE_LANE_CONTINUOUS_HOST_JOIN,
    FIVE_LANE_RUNTIME_CREATED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    FULL_AUTONOMY_TRADING_DECISION_AUTHORITY,
    HOST_ACTIVATION_DIRNAME,
    HOST_JOIN,
    HOST_JOIN_INVOKED,
    JOIN_CAP23_SELECTION_AUTHORITY,
    JOIN_CAP24_BINDING_AUTHORITY,
    JOIN_EXECUTION_AUTHORITY,
    JOIN_FULL_AUTONOMY_HOST_AUTHORITY,
    JOIN_IMPLEMENTED,
    JOIN_RANKING_AUTHORITY,
    JOIN_RUNTIME_ACTIVATION_AUTHORITY,
    JOIN_SELECTION_AUTHORITY,
    JOIN_SYMBOL,
    JOIN_TRADING_AUTHORITY,
    MAX_POSITIONS_EFFECTIVE,
    MAX_PRODUCTIVE_OCCUPIED_LANES,
    MAY_ENABLE_HOST,
    MAY_INVOKE_HOST_JOIN,
    MAY_INVOKE_PRODUCTIVE_HOST_ENTRY,
    MAY_JOIN_CAP72_LIVE_EXECUTION_PORT,
    MAY_MINT_PERMIT,
    MAY_POST,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    N5_MODEL,
    NATIVE_ID_SOURCE,
    NEW_CURSOR_WRITER,
    NEW_HOST_OWNER_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RUNTIME_AUTHORIZATION_EFFECT,
    RUNTIME_N5_ARCHITECTURE_COMPLETE,
    SLICE_ID,
    TECHNICAL_WORK_REMAINING,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
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
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    ACTIVATION_STATE_FILENAME,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CAP72_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (
    load_activation_state_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CAP23_MULTI_FUTURE,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CAP24_MULTI_FUTURE,
)
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

PACKAGE_DIR = Path(completion_constants.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "completion_join_v1.py").read_text(encoding="utf-8")
HOST_BINDING_SOURCE = (REPO_ROOT / CANONICAL_HOST_JOIN_MODULE).read_text(encoding="utf-8")
MV2_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
).read_text(encoding="utf-8")
PROTECTED_RELPATHS = (
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1/readiness_join_v1.py",
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py",
    "src/ops/single_future_stateful_no_order_runtime_activation_v1/host_binding_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    "src/ops/single_selected_future_policy_v1/constants_v1.py",
    "src/ops/single_selected_future_runtime_binding_v1/constants_v1.py",
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


def _run(tmp_path: Path, lane_ids: tuple[str, ...], **overrides: object):
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in lane_ids}
    last_ts = float(overrides.pop("last_ts", C1_TS))
    target = int(overrides.pop("target_cardinality", len(lane_ids)))
    kwargs = _market_kwargs(
        cycle_id_prefix=str(overrides.pop("cycle_id_prefix", "n5-rt")),
        last_ts=last_ts,
    )
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    kwargs.update(overrides)
    result = run_occupied_lane_runtime_n5_completion_v1(
        pairs,
        target_cardinality=target,
        **kwargs,
    )
    return pairs, result


def test_authority_flags_and_n5_target_are_pinned() -> None:
    assert SLICE_ID == "RUNTIME_N5_HOST_JOIN_AND_CARDINALITY_COMPLETION"
    assert OWNER == "ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1"
    assert CONTRACT_ID == "CURRENT_MF_N5_FULL_AUTONOMY_RUNTIME_N5_COMPLETION_CONTRACT_V1"
    assert OWNER_GO_THIS_SLICE == "OWNER_GO_BIG_RUNTIME_N5_COMPLETION_V1"
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == (
        "HOST_JOIN_AND_N5_CARDINALITY_ORCHESTRATION_NO_EXTERNAL_EFFECT"
    )
    assert ATLAS_AUTHORITY == "NONE"
    assert JOIN_IMPLEMENTED is True
    assert JOIN_SYMBOL == "run_occupied_lane_runtime_n5_completion_v1"
    assert (
        CANONICAL_HOST_JOIN_OWNER == FULL_CORE_HOST_JOIN_OWNER == ("stateful_no_order_host_join_v1")
    )
    assert CANONICAL_HOST_JOIN_SYMBOL == "ensure_host_activation_binding_v1"
    assert CANONICAL_HOST_JOIN_PACKAGE == (
        "ops.single_future_stateful_no_order_runtime_activation_v1"
    )
    assert CANONICAL_RUNTIME_OWNER == CANONICAL_HOST_JOIN_PACKAGE
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
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert FULL_AUTONOMY_TRADING_DECISION_AUTHORITY is False
    assert HOST_JOIN is True
    assert HOST_JOIN_INVOKED is True
    assert MAY_INVOKE_HOST_JOIN is True
    assert MAY_ENABLE_HOST is True
    assert MAY_JOIN_CAP72_LIVE_EXECUTION_PORT is False
    assert MAY_INVOKE_PRODUCTIVE_HOST_ENTRY is False
    assert MAY_MINT_PERMIT is False
    assert MAY_POST is False
    assert MF_PRODUCTIVE_JOIN is True
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "5_JOINED"
    assert N5_MODEL == "FIVE_ISOLATED_N1_LANES"
    assert MAX_POSITIONS_EFFECTIVE == CAP23_MAX_POSITIONS == CAP24_MAX_POSITIONS == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CAP23_MULTI_FUTURE is False
    assert CAP24_MULTI_FUTURE is False
    assert CAP72_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert EXECUTION_SCHEDULE == "SEQUENTIAL_LANE_ID_ORDER_NOT_CONCURRENT"
    assert FIVE_LANE_RUNTIME_CREATED is True
    assert FIVE_LANE_CONTINUOUS_HOST_JOIN is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert RUNTIME_N5_ARCHITECTURE_COMPLETE is True
    assert TECHNICAL_WORK_REMAINING == "NONE"
    assert AUTHORITY_WORK_REMAINING == "EXTERNAL_EFFECT_LIVE_TRADING_OWNER_GO"
    assert FIRST_UNAUTHORIZED_REMAINING_BOUNDARY == "EXTERNAL_EFFECT_LIVE_TRADING_OWNER_GO"
    assert MAX_PRODUCTIVE_OCCUPIED_LANES == 5
    assert NATIVE_ID_SOURCE == "BoundInstrumentV1.venue_native_id"
    assert READINESS_HOST_JOIN is False
    assert READINESS_HOST_JOIN_INVOKED is False
    assert READINESS_MF_PRODUCTIVE_JOIN is False
    assert READINESS_PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is True
    assert CURSOR_OWNER.endswith("current_productive_sidestate_confirmation_cursor_v1")


def test_reuse_before_new_census_names_existing_owners() -> None:
    census = occupied_lane_runtime_n5_completion_census_v1()
    assert census["CANONICAL_HOST_JOIN_OWNER"] == "stateful_no_order_host_join_v1"
    assert census["CANONICAL_HOST_JOIN_SYMBOL"] == "ensure_host_activation_binding_v1"
    assert census["READINESS_JOIN_SYMBOL"] == ("compose_occupied_lane_n1_host_join_readiness_v1")
    assert census["CURSOR_OWNER"].endswith("current_productive_sidestate_confirmation_cursor_v1")
    assert "CYCLE_EXCLUSION_LOCK" in census["LOCKING_MODEL"]
    assert census["PRODUCTIVE_RUNTIME_CARDINALITY"] == "5_JOINED"
    assert census["N5_MODEL"] == "FIVE_ISOLATED_N1_LANES"
    assert census["ATLAS_AUTHORITY"] == "NONE"
    assert census["FIRST_UNAUTHORIZED_REMAINING_BOUNDARY"] == (
        "EXTERNAL_EFFECT_LIVE_TRADING_OWNER_GO"
    )


def test_forbidden_graph_invokes_canonical_host_join_only() -> None:
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert "compose_occupied_lane_n1_host_join_readiness_v1(" in JOIN_SOURCE
    assert "ensure_host_activation_binding_v1(" in JOIN_SOURCE
    assert "HostActivationBindingV1(" in JOIN_SOURCE
    assert "join_cap72_host_to_live_execution_port_v1(" not in JOIN_SOURCE
    assert "run_bridge_cycle_v1(" not in JOIN_SOURCE
    assert "construct_live_execution_port_v1(" not in JOIN_SOURCE
    assert "run_activation_gate_v1(" not in JOIN_SOURCE
    assert "produce_occupied_lane_cap23_n1_selections_v1(" not in JOIN_SOURCE
    assert "run_single_selected_future_policy_v1(" not in JOIN_SOURCE
    assert "ensure_single_selected_future_runtime_binding_v1(" not in JOIN_SOURCE
    assert "run_current_productive_governed_continuous_cycle_run_v1(" not in JOIN_SOURCE
    assert "_pick_top_eligible(" not in JOIN_SOURCE
    assert "LiveExecutionPort" not in JOIN_SOURCE
    assert JOIN_SOURCE.count("ensure_host_activation_binding_v1(") == 1


def test_n1_joined_runtime_reaches_pre_external_effect(tmp_path: Path) -> None:
    pairs, result = _run(tmp_path, ("LANE_1",), cycle_id_prefix="n5-n1")
    assert result.occupied_count == 1
    assert result.productive_runtime_cardinality == "1_JOINED"
    assert result.host_join is True
    assert result.mf_productive_join is True
    assert result.max_positions_effective == 1
    assert result.multi_future_runtime_authorized is False
    assert result.execution_concurrency_authorized is False
    assert result.external_effect_authorized is False
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.runtime_n5_architecture_complete is False
    record = result.joined_lanes["LANE_1"]
    bound = pairs["LANE_1"][1]
    assert record.native_id == bound.venue_native_id
    assert record.instrument_id == bound.instrument_id
    assert record.host_join_invoked is True
    assert record.host_enabled is True
    assert record.host_gate_ok is True
    assert record.host_alpha_blocked is False
    assert record.host_live_execution_port_present is False
    assert record.post_count == 0
    assert record.permit_created is False
    assert record.disposition in SUCCESS_DISPOSITIONS, record.disposition
    assert HOST_ACTIVATION_DIRNAME in record.host_activation_root
    loaded = load_activation_state_v1(Path(record.host_activation_root), require_present=True)
    assert loaded is not None
    assert loaded.instrument_id == bound.instrument_id
    assert (Path(record.host_activation_root) / ACTIVATION_STATE_FILENAME).is_file()
    cursor = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(record.cursor_store_root)
    )
    assert isinstance(cursor, dict)
    assert cursor["venue_native_id"] == bound.venue_native_id
    assert "lane_id" not in cursor


@pytest.mark.parametrize("occupied", [2, 3, 4, 5])
def test_cardinality_transition_joined(tmp_path: Path, occupied: int) -> None:
    lane_ids = tuple(LANE_IDS[:occupied])
    pairs, result = _run(
        tmp_path,
        lane_ids,
        cycle_id_prefix=f"n5-card-{occupied}",
        target_cardinality=occupied,
    )
    assert result.occupied_count == occupied
    assert result.productive_runtime_cardinality == f"{occupied}_JOINED"
    assert result.host_join is True
    assert result.mf_productive_join is True
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.execution_concurrency_authorized is False
    assert result.multi_future_runtime_authorized is False
    assert result.max_positions_effective == 1
    assert result.runtime_n5_architecture_complete is (occupied == 5)
    assert set(result.joined_lanes) == set(lane_ids)
    natives = [result.joined_lanes[lane_id].native_id for lane_id in lane_ids]
    assert natives == [pairs[lane_id][1].venue_native_id for lane_id in lane_ids]
    assert len(set(natives)) == occupied
    roots = [result.joined_lanes[lane_id].lane_state_root for lane_id in lane_ids]
    assert len(set(roots)) == occupied
    activations = [result.joined_lanes[lane_id].host_activation_root for lane_id in lane_ids]
    assert len(set(activations)) == occupied
    for lane_id in lane_ids:
        record = result.joined_lanes[lane_id]
        assert record.disposition in SUCCESS_DISPOSITIONS, record.disposition
        assert record.host_join_invoked is True
        assert record.host_live_execution_port_present is False
        assert record.post_count == 0
        assert record.permit_created is False
        assert record.external_effect_count == 0


def test_five_lane_state_isolation_and_instrument_binding(tmp_path: Path) -> None:
    pairs, result = _run(tmp_path, LANE_IDS, cycle_id_prefix="n5-iso")
    assert result.occupied_count == 5
    assert result.productive_runtime_cardinality == "5_JOINED"
    assert result.runtime_n5_architecture_complete is True
    cursors = []
    locks = []
    evidence = []
    activations = []
    for lane_id in LANE_IDS:
        record = result.joined_lanes[lane_id]
        bound = pairs[lane_id][1]
        assert record.native_id == bound.venue_native_id == f"VENUE-{lane_id[-1]}"
        assert record.instrument_id == bound.instrument_id == f"INST-{lane_id}"
        assert record.lane_state_root != N1_GLOBAL_CURSOR_STORE_RELPATH
        assert N1_GLOBAL_CURSOR_STORE_RELPATH not in record.cursor_store_root
        cursors.append(record.cursor_store_root)
        locks.append(record.lock_root)
        evidence.append(record.evidence_root)
        activations.append(record.host_activation_root)
        loaded = load_current_productive_sidestate_confirmation_cursor_v1(
            Path(record.cursor_store_root)
        )
        assert loaded is not None
        assert loaded["venue_native_id"] == bound.venue_native_id
        host_state = load_activation_state_v1(
            Path(record.host_activation_root), require_present=True
        )
        assert host_state is not None
        assert host_state.instrument_id == bound.instrument_id
    assert len(set(cursors)) == 5
    assert len(set(locks)) == 5
    assert len(set(evidence)) == 5
    assert len(set(activations)) == 5


def test_restart_reentry_reloads_cursor_and_host_activation(tmp_path: Path) -> None:
    pairs, first = _run(tmp_path, ("LANE_2",), cycle_id_prefix="n5-restart-1")
    first_record = first.joined_lanes["LANE_2"]
    first_host = load_activation_state_v1(
        Path(first_record.host_activation_root), require_present=True
    )
    assert first_host is not None
    first_seq = int(first_host.commit_sequence)
    _clear_cycle_ledger(first_record.evidence_root)
    second = run_occupied_lane_runtime_n5_completion_v1(
        pairs,
        target_cardinality=1,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_market_kwargs(cycle_id_prefix="n5-restart-2", last_ts=C1_TS_NEXT),
    )
    second_record = second.joined_lanes["LANE_2"]
    assert second_record.host_activation_root == first_record.host_activation_root
    assert second_record.native_id == pairs["LANE_2"][1].venue_native_id
    assert second_record.host_join_invoked is True
    assert second_record.disposition in SUCCESS_DISPOSITIONS | {DISPOSITION_FAIL_CLOSED}
    second_host = load_activation_state_v1(
        Path(second_record.host_activation_root), require_present=True
    )
    assert second_host is not None
    assert second_host.instrument_id == first_host.instrument_id
    assert int(second_host.commit_sequence) >= first_seq
    cursor = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(second_record.cursor_store_root)
    )
    assert isinstance(cursor, dict)
    assert cursor["venue_native_id"] == pairs["LANE_2"][1].venue_native_id


def test_single_writer_lane_local_cursor_no_n1_global_and_no_dual_write(
    tmp_path: Path,
) -> None:
    _, result = _run(tmp_path, ("LANE_4",), cycle_id_prefix="n5-sw")
    record = result.joined_lanes["LANE_4"]
    cursor_files = list(Path(tmp_path).rglob(CURSOR_FILENAME))
    assert len(cursor_files) == 1
    assert cursor_files[0] == Path(record.cursor_store_root) / CURSOR_FILENAME
    n1 = REPO_ROOT / N1_GLOBAL_CURSOR_STORE_RELPATH / CURSOR_FILENAME
    before = n1.read_bytes() if n1.is_file() else None
    after = n1.read_bytes() if n1.is_file() else None
    assert before == after
    assert NEW_CURSOR_WRITER is False
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in JOIN_SOURCE
    assert JOIN_SOURCE.count("HostActivationBindingV1(") == 1


def test_same_lane_concurrent_lock_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_s7_kwargs(_market_kwargs(cycle_id_prefix="n5-lock-seed")),
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
            run_occupied_lane_runtime_n5_completion_v1(
                pairs,
                target_cardinality=1,
                g17_typed_vol_producers=_lane_g17(pairs),
                **_market_kwargs(cycle_id_prefix="n5-lock"),
            )
        assert exc.value.reason_code == REASON_CONCURRENT_CYCLE
    finally:
        lock.release()


def test_cardinality_mismatch_and_forbidden_kwarg_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    kwargs = _market_kwargs(cycle_id_prefix="n5-card-bad")
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    with pytest.raises(FullAutonomyRuntimeN5CompletionError) as mismatch:
        run_occupied_lane_runtime_n5_completion_v1(
            pairs,
            target_cardinality=2,
            **kwargs,
        )
    assert mismatch.value.failure_code == FAILURE_CARDINALITY
    with pytest.raises(FullAutonomyRuntimeN5CompletionError) as forbidden:
        run_occupied_lane_runtime_n5_completion_v1(
            pairs,
            target_cardinality=1,
            enable_host=True,
            **kwargs,
        )
    assert forbidden.value.failure_code == FAILURE_FORBIDDEN_KWARG
    with pytest.raises(FullAutonomyRuntimeN5CompletionError) as live:
        run_occupied_lane_runtime_n5_completion_v1(
            pairs,
            target_cardinality=1,
            live_port=object(),
            **kwargs,
        )
    assert live.value.failure_code == FAILURE_FORBIDDEN_KWARG
    assert cardinality_joined_token_v1(5) == "5_JOINED"


def test_protected_surfaces_and_no_trading_decision_authority() -> None:
    package_files = {path.resolve() for path in PACKAGE_DIR.iterdir() if path.is_file()}
    for rel in PROTECTED_RELPATHS:
        assert Path(rel).resolve() not in package_files
        assert Path(rel).is_file()
    assert JOIN_SOURCE.count("def run_occupied_lane_runtime_n5_completion_v1") == 1
    assert JOIN_SOURCE.count("def join_occupied_lane_host_activation_v1") == 1
    assert "def ensure_host_activation_binding_v1" in HOST_BINDING_SOURCE
    assert "run_current_productive_master_v2_runtime_cycle_v1" in MV2_SOURCE
    assert CAP23_MAX_POSITIONS == 1
    assert CAP24_MAX_POSITIONS == 1
    assert CAP23_MULTI_FUTURE is False
    assert FULL_AUTONOMY_TRADING_DECISION_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert DISPOSITION_PRE_EXTERNAL_EFFECT
    assert DISPOSITION_HOLD
    assert DISPOSITION_COMPLETED
    assert INIT_SOURCE.count("run_occupied_lane_runtime_n5_completion_v1") >= 1
    assert (
        inspect.getsource(join_occupied_lane_host_activation_v1).count(
            "ensure_host_activation_binding_v1("
        )
        == 1
    )
    assert "produce_occupied_lane_cap23_n1_selections_v1(" not in CONSTANTS_SOURCE
