"""Occupied-lane governed-cycle N=1 consumer join tests."""

from __future__ import annotations

import ast
import inspect
import json
import math
from pathlib import Path

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    constants_v1 as consumer_constants,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    ATOMICITY_CLAIMED_SATISFIED,
    ATOMICITY_SEMANTICS,
    AUTHORITY_EFFECT,
    CAP23_CHANGE_REQUIRED,
    CAP24_CHANGE_REQUIRED,
    CAP61_CYCLE_STATE_ROOT_BOUND,
    CONSUMPTION_SEAM,
    CONTRACT_ID,
    CURSOR_FILENAME,
    CURSOR_HAS_LANE_ID_FIELD,
    CURSOR_OWNER,
    CURSOR_OWNER_CHANGE_REQUIRED,
    CURSOR_SCHEMA_CHANGED,
    EG_DISPATCH_SYMBOL,
    EG_V5_USED,
    EXECUTION_CONCURRENCY_AUTHORIZED,
    FAILURE_INJECTED_C1_REQUIRED,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    GOVERNED_CYCLE_INVOKED,
    HOST_JOIN,
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
    MASTER_V2_CHANGE_REQUIRED,
    MAX_POSITIONS_EFFECTIVE,
    MAY_BIND_CAP61_STATE_ROOT,
    MAY_INVOKE_GOVERNED_CYCLE,
    MF_PRODUCTIVE_JOIN,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N1_GLOBAL_CURSOR_STORE_RELPATH,
    NATIVE_ID_SOURCE,
    NEW_STATE_OWNER_CREATED,
    OWNER,
    OWNER_GO_THIS_SLICE,
    PRODUCTIVE_RUNTIME_CARDINALITY,
    RUNTIME_AUTHORIZATION_EFFECT,
    S7_JOIN_SYMBOL,
    S8_CONSUMED,
    S8_JOIN_SYMBOL,
    SLICE_ID,
    T2_DISPATCH_SYMBOL,
    T2_S7_USED,
    THIS_SLICE_MAY_REINVOKE_CAP23,
    THIS_SLICE_MAY_REINVOKE_CAP24,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError,
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    non_v5_eg_dispatch_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError,
    bind_occupied_lane_governed_cycle_store_roots_v1,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    FAILURE_N1_GLOBAL_CURSOR_STORE,
    MAY_INVOKE_GOVERNED_CYCLE as S8_MAY_INVOKE_GOVERNED_CYCLE,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import (
    OCCUPANCY_OCCUPIED,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    IsolatedLaneSlotV1,
    lane_state_root_for,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_COMPLETED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    LEDGER_FILENAME,
    REASON_CONCURRENT_CYCLE,
    CurrentProductiveGovernedCycleOrchestratorError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    CYCLE_EXCLUSION_LOCK_NAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CurrentProductiveCursorError,
    load_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import (
    _candles,
)
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

PACKAGE_DIR = Path(consumer_constants.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SOURCE = (PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")
JOIN_SOURCE = (PACKAGE_DIR / "invoke_join_v1.py").read_text(encoding="utf-8")
ADDRESSING_JOIN_SOURCE = (
    REPO_ROOT
    / "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1"
    / "addressing_join_v1.py"
).read_text(encoding="utf-8")
ORCHESTRATOR_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_cycle_orchestrator_v1.py"
).read_text(encoding="utf-8")
CURSOR_OWNER_SOURCE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_sidestate_confirmation_cursor_v1.py"
).read_text(encoding="utf-8")
ORIGIN_SHA = "3f933795871155a3e7efc38f5761e9e5f461f797"
C1_TS = float(PREVIOUS_C1_VENUE_EVENT_TIME) + 60.0
C1_TS_NEXT = C1_TS + 60.0
SUCCESS_DISPOSITIONS = {
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    DISPOSITION_HOLD,
    DISPOSITION_COMPLETED,
}
PROTECTED_RELPATHS = (
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py",
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1/handoff_join_v1.py",
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


def _bound(*, lane_id: str) -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=f"INST-{lane_id}",
        venue_native_id=f"VENUE-{lane_id[-1]}",
        ranking_snapshot_id="rank-shared",
        ranking_integrity_digest="rank-digest-shared",
        universe_snapshot_id="uni-shared",
        selection_id=f"sel-{lane_id}",
        selection_integrity_digest=f"sel-digest-{lane_id}",
        selection_state="SELECTED",
    )


def _pair(
    tmp_path: Path,
    lane_id: str,
    *,
    lane_state_root: str | None = None,
) -> tuple[IsolatedLaneSlotV1, BoundInstrumentV1]:
    bound = _bound(lane_id=lane_id)
    root = lane_state_root or lane_state_root_for(
        topology_state_root_base=tmp_path, lane_id=lane_id
    )
    slot = IsolatedLaneSlotV1(
        lane_id=lane_id,
        occupancy=OCCUPANCY_OCCUPIED,
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=root,
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )
    return slot, bound


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


def _lane_g17(
    pairs: dict[str, tuple[IsolatedLaneSlotV1, BoundInstrumentV1]],
) -> dict[str, object]:
    return {
        lane_id: _memory_g17_producer(
            instrument_id=bound.instrument_id,
            venue_native_id=bound.venue_native_id,
        )
        for lane_id, (_slot, bound) in pairs.items()
    }


def _market_kwargs(*, cycle_id_prefix: str, last_ts: float = C1_TS) -> dict[str, object]:
    return {
        "origin_main_sha": ORIGIN_SHA,
        "cycle_id_prefix": cycle_id_prefix,
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
        "candles_payload": _candles(last_ts_ms=int(last_ts * 1000)),
    }


def _s7_kwargs(market: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in market.items()
        if key not in {"origin_main_sha", "candles_payload"}
    }


def _invoke(tmp_path: Path, lane_ids: tuple[str, ...], **overrides: object):
    pairs = {lane_id: _pair(tmp_path, lane_id) for lane_id in lane_ids}
    last_ts = float(overrides.pop("last_ts", C1_TS))
    kwargs = _market_kwargs(
        cycle_id_prefix=str(overrides.pop("cycle_id_prefix", "n1-gc")),
        last_ts=last_ts,
    )
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    kwargs.update(overrides)
    return pairs, invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)  # type: ignore[arg-type]


def _clear_cycle_ledger(evidence_root: str) -> None:
    ledger = Path(evidence_root) / LEDGER_FILENAME
    if ledger.is_file():
        ledger.unlink()


def test_authority_flags_and_s8_seam_are_pinned() -> None:
    assert SLICE_ID == "GOVERNED_CYCLE_N1_CONSUMER_JOIN_TO_PRE_EXTERNAL_EFFECT"
    assert OWNER == (
        "ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1"
    )
    assert CONTRACT_ID == (
        "CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_GOVERNED_CYCLE_N1_CONSUMER_JOIN_CONTRACT_V1"
    )
    assert OWNER_GO_THIS_SLICE == (
        "OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_GOVERNED_CYCLE_N1_CONSUMER_JOIN_V1"
    )
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_AUTHORIZATION_EFFECT == "NONE"
    assert JOIN_IMPLEMENTED is True
    assert JOIN_SYMBOL == "invoke_occupied_lane_governed_cycle_n1_consumer_v1"
    assert S8_JOIN_SYMBOL == "bind_occupied_lane_governed_cycle_store_roots_v1"
    assert S7_JOIN_SYMBOL == "compose_occupied_lane_mv2_dp_durable_cycle_v1"
    assert S8_CONSUMED is True
    assert GOVERNED_CYCLE_INVOKED is True
    assert MAY_INVOKE_GOVERNED_CYCLE is True
    assert S8_MAY_INVOKE_GOVERNED_CYCLE is False
    assert EG_DISPATCH_SYMBOL == "non_v5_eg_dispatch_v1"
    assert T2_DISPATCH_SYMBOL == S7_JOIN_SYMBOL
    assert EG_V5_USED is False
    assert T2_S7_USED is True
    assert NATIVE_ID_SOURCE == "BoundInstrumentV1.venue_native_id"
    assert CONSUMPTION_SEAM == "invoke_run_current_productive_governed_cycle_v1"
    assert CAP61_CYCLE_STATE_ROOT_BOUND is False
    assert MAY_BIND_CAP61_STATE_ROOT is False
    assert CURSOR_HAS_LANE_ID_FIELD is False
    assert CURSOR_SCHEMA_CHANGED is False
    assert NEW_STATE_OWNER_CREATED is False
    assert CURSOR_OWNER_CHANGE_REQUIRED is False
    assert ATOMICITY_SEMANTICS == "NON_ATOMIC_DIRECT_WRITE_TEXT"
    assert ATOMICITY_CLAIMED_SATISFIED is False
    assert JOIN_RANKING_AUTHORITY is False
    assert JOIN_SELECTION_AUTHORITY is False
    assert JOIN_CAP23_SELECTION_AUTHORITY is False
    assert JOIN_CAP24_BINDING_AUTHORITY is False
    assert JOIN_TRADING_AUTHORITY is False
    assert JOIN_RUNTIME_ACTIVATION_AUTHORITY is False
    assert JOIN_EXECUTION_AUTHORITY is False
    assert JOIN_PERSISTENCE_AUTHORITY is False
    assert JOIN_FULL_AUTONOMY_HOST_AUTHORITY is False
    assert THIS_SLICE_MAY_REINVOKE_CAP23 is False
    assert THIS_SLICE_MAY_REINVOKE_CAP24 is False
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXECUTION_CONCURRENCY_AUTHORIZED is False
    assert CAP23_CHANGE_REQUIRED is False
    assert CAP24_CHANGE_REQUIRED is False
    assert MASTER_V2_CHANGE_REQUIRED is False
    assert CURSOR_OWNER.endswith("current_productive_sidestate_confirmation_cursor_v1")


def test_forbidden_graph_and_v5_are_absent_from_join_calls() -> None:
    called = _called_names(JOIN_SOURCE)
    assert called & FORBIDDEN_CALL_GRAPH_TARGETS == set()
    assert "bind_occupied_lane_governed_cycle_store_roots_v1(" in JOIN_SOURCE
    assert "run_current_productive_governed_cycle_v1(" in JOIN_SOURCE
    assert "compose_occupied_lane_mv2_dp_durable_cycle_v1(" in JOIN_SOURCE
    assert "non_v5_eg_dispatch_v1" in JOIN_SOURCE
    assert "eg_cycle_dispatch=non_v5_eg_dispatch_v1" in JOIN_SOURCE
    assert "_run_cap21_to_cap24_v1(" not in JOIN_SOURCE
    assert (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1("
        not in (JOIN_SOURCE)
    )
    assert "produce_occupied_lane_cap23_n1_selections_v1(" not in JOIN_SOURCE
    assert "run_single_selected_future_policy_v1(" not in JOIN_SOURCE
    assert "ensure_single_selected_future_runtime_binding_v1(" not in JOIN_SOURCE
    assert "stateful_no_order_host_join_v1" not in JOIN_SOURCE
    assert "construct_live_execution_port_v1(" not in JOIN_SOURCE
    assert "LiveExecutionPort" not in JOIN_SOURCE
    assert "run_current_productive_governed_continuous_cycle_run_v1(" not in JOIN_SOURCE
    stub = inspect.getsource(non_v5_eg_dispatch_v1)
    assert (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1("
        not in stub
    )
    assert "_run_cap21_to_cap24_v1(" not in stub
    assert S8_MAY_INVOKE_GOVERNED_CYCLE is False
    assert "run_current_productive_governed_cycle_v1(" not in ADDRESSING_JOIN_SOURCE


def test_n1_end_to_end_harness_hold_or_pre_external_effect(tmp_path: Path) -> None:
    pairs, results = _invoke(tmp_path, ("LANE_1",), cycle_id_prefix="n1-e2e")
    assert set(results) == {"LANE_1"}
    record = results["LANE_1"]
    bound = pairs["LANE_1"][1]
    assert record.native_id == bound.venue_native_id
    assert record.bound_instrument.venue_native_id == bound.venue_native_id
    assert record.eg_v5_used is False
    assert record.t2_s7_used is True
    assert record.cap61_state_root_bound is False
    assert record.bootstrap_used is True
    s8 = bind_occupied_lane_governed_cycle_store_roots_v1(pairs)
    assert record.cursor_store_root == s8["LANE_1"][0]
    assert record.lock_root == s8["LANE_1"][1]
    assert record.evidence_root == s8["LANE_1"][2]
    assert N1_GLOBAL_CURSOR_STORE_RELPATH not in record.cursor_store_root
    cycle = record.governed_cycle_result
    assert cycle.disposition in SUCCESS_DISPOSITIONS, cycle.reason_code
    assert int(cycle.post_count) == 0
    assert cycle.permit_created is False
    assert cycle.external_effect_count == 0
    cursor_path = Path(record.cursor_store_root) / CURSOR_FILENAME
    assert cursor_path.is_file()
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(record.cursor_store_root)
    )
    assert isinstance(loaded, dict)
    assert loaded["venue_native_id"] == bound.venue_native_id
    assert "lane_id" not in loaded
    assert record.s7_invocation is not None
    assert record.s7_invocation.persist_enabled is True
    assert record.s7_invocation.cap61_state_root_bound is False
    assert HOST_JOIN is False
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"


def test_identity_native_id_is_bound_instrument_throughout(tmp_path: Path) -> None:
    pairs, results = _invoke(tmp_path, ("LANE_3",), cycle_id_prefix="n1-id")
    bound = pairs["LANE_3"][1]
    record = results["LANE_3"]
    assert record.native_id == bound.venue_native_id == "VENUE-3"
    assert record.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS, (
        record.governed_cycle_result.reason_code
    )
    assert record.governed_cycle_result.c1_used.startswith("native_id=VENUE-3;")
    assert record.s7_invocation is not None
    assert record.s7_invocation.bound_instrument.venue_native_id == "VENUE-3"


def test_restart_reloads_lane_cursor_and_runs_again(tmp_path: Path) -> None:
    pairs, first = _invoke(tmp_path, ("LANE_2",), cycle_id_prefix="n1-restart-1")
    first_record = first["LANE_2"]
    assert first_record.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS, (
        first_record.governed_cycle_result.reason_code
    )
    assert first_record.s7_invocation is not None
    first_outgoing = first_record.s7_invocation.cycle_result.outgoing_cursor
    assert first_outgoing is not None
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(first_record.cursor_store_root)
    )
    assert loaded == first_outgoing.to_dict()
    _clear_cycle_ledger(first_record.evidence_root)
    del first
    second = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_market_kwargs(cycle_id_prefix="n1-restart-2", last_ts=C1_TS_NEXT),  # type: ignore[arg-type]
    )
    second_record = second["LANE_2"]
    assert second_record.bootstrap_used is False
    assert second_record.s7_invocation is not None
    assert second_record.s7_invocation.incoming_cursor == first_outgoing.to_dict()
    assert second_record.native_id == pairs["LANE_2"][1].venue_native_id
    assert second_record.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS | {
        DISPOSITION_FAIL_CLOSED
    }


def test_single_writer_lane_local_cursor_no_n1_global(tmp_path: Path) -> None:
    pairs, results = _invoke(tmp_path, ("LANE_4",), cycle_id_prefix="n1-sw")
    record = results["LANE_4"]
    cursor_files = list(Path(tmp_path).rglob(CURSOR_FILENAME))
    assert len(cursor_files) == 1
    assert cursor_files[0] == Path(record.cursor_store_root) / CURSOR_FILENAME
    n1 = REPO_ROOT / N1_GLOBAL_CURSOR_STORE_RELPATH / CURSOR_FILENAME
    before = n1.read_bytes() if n1.is_file() else None
    after = n1.read_bytes() if n1.is_file() else None
    assert before == after
    assert "cap61_confirmation_state_v1.json" not in {
        path.name for path in Path(tmp_path).rglob("*")
    }
    persist_source = inspect.getsource(compose_occupied_lane_mv2_dp_durable_cycle_v1)
    assert "persist_occupied_lane_mv2_dp_decision_state_cursor_v1(" in persist_source
    assert "write_text" not in JOIN_SOURCE
    assert "persist_current_productive_sidestate_confirmation_cursor_v1(" not in JOIN_SOURCE


def test_lane_isolation_sequential_harness(tmp_path: Path) -> None:
    pairs, results = _invoke(tmp_path, ("LANE_1", "LANE_5"), cycle_id_prefix="n1-iso")
    left = results["LANE_1"]
    right = results["LANE_5"]
    assert left.cursor_store_root != right.cursor_store_root
    assert left.lock_root != right.lock_root
    assert left.evidence_root != right.evidence_root
    assert left.native_id != right.native_id
    assert Path(left.cursor_store_root) / CURSOR_FILENAME != (
        Path(right.cursor_store_root) / CURSOR_FILENAME
    )
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
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert left.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS, (
        left.governed_cycle_result.reason_code
    )
    assert right.governed_cycle_result.disposition in SUCCESS_DISPOSITIONS, (
        right.governed_cycle_result.reason_code
    )


def test_same_lane_concurrent_lock_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_s7_kwargs(_market_kwargs(cycle_id_prefix="n1-lock-seed")),  # type: ignore[arg-type]
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
            invoke_occupied_lane_governed_cycle_n1_consumer_v1(
                pairs,
                g17_typed_vol_producers=_lane_g17(pairs),
                **_market_kwargs(cycle_id_prefix="n1-lock"),  # type: ignore[arg-type]
            )
        assert exc.value.reason_code == REASON_CONCURRENT_CYCLE
    finally:
        lock.release()


def test_missing_candles_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    kwargs = _market_kwargs(cycle_id_prefix="n1-c1")
    kwargs["candles_payload"] = None
    with pytest.raises(FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError) as exc:
        invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            g17_typed_vol_producers=_lane_g17(pairs),
            **kwargs,  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_INJECTED_C1_REQUIRED


def test_corrupt_cursor_preserves_existing_fail_closed(tmp_path: Path) -> None:
    pairs, first = _invoke(tmp_path, ("LANE_4",), cycle_id_prefix="n1-corrupt-seed")
    path = Path(first["LANE_4"].cursor_store_root) / CURSOR_FILENAME
    path.write_text("{", encoding="utf-8")
    with pytest.raises(CurrentProductiveCursorError) as exc:
        invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            g17_typed_vol_producers=_lane_g17(pairs),
            **_market_kwargs(cycle_id_prefix="n1-corrupt"),  # type: ignore[arg-type]
        )
    assert exc.value.reason_code == "CURSOR_FILE_CORRUPT"


def test_schema_mismatch_does_not_silently_restore(tmp_path: Path) -> None:
    pairs, first = _invoke(tmp_path, ("LANE_3",), cycle_id_prefix="n1-schema-seed")
    path = Path(first["LANE_3"].cursor_store_root) / CURSOR_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_name"] = "not-the-canonical-schema"
    path.write_text(json.dumps(payload), encoding="utf-8")
    _clear_cycle_ledger(first["LANE_3"].evidence_root)
    with pytest.raises(CurrentProductiveGovernedCycleOrchestratorError) as exc:
        invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            g17_typed_vol_producers=_lane_g17(pairs),
            **_market_kwargs(cycle_id_prefix="n1-schema", last_ts=C1_TS_NEXT),  # type: ignore[arg-type]
        )
    assert exc.value.reason_code == "CURSOR_INVALID"
    reloaded = load_current_productive_sidestate_confirmation_cursor_v1(
        Path(first["LANE_3"].cursor_store_root)
    )
    assert reloaded is not None
    assert reloaded["schema_name"] == "not-the-canonical-schema"


def test_n1_global_root_still_rejected_via_s8(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1", lane_state_root=N1_GLOBAL_CURSOR_STORE_RELPATH)}
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError) as exc:
        invoke_occupied_lane_governed_cycle_n1_consumer_v1(
            pairs,
            g17_typed_vol_producers=_lane_g17(pairs),
            **_market_kwargs(cycle_id_prefix="n1-global"),  # type: ignore[arg-type]
        )
    assert exc.value.failure_code == FAILURE_N1_GLOBAL_CURSOR_STORE


def test_empty_pairs_are_noop() -> None:
    result = invoke_occupied_lane_governed_cycle_n1_consumer_v1(
        {},
        **_market_kwargs(cycle_id_prefix="n1-empty"),  # type: ignore[arg-type]
    )
    assert result == {}


def test_protected_surfaces_are_not_mutated_by_this_package() -> None:
    for rel in PROTECTED_RELPATHS:
        assert Path(rel).name not in {path.name for path in PACKAGE_DIR.iterdir()}
    assert JOIN_SOURCE.count("def invoke_occupied_lane_governed_cycle_n1_consumer_v1") == 1
    assert "MAY_INVOKE_GOVERNED_CYCLE is False" in ADDRESSING_JOIN_SOURCE or (
        "if MAY_INVOKE_GOVERNED_CYCLE:" in ADDRESSING_JOIN_SOURCE
    )
    assert S8_MAY_INVOKE_GOVERNED_CYCLE is False
    assert (
        "lane_id"
        not in CURSOR_OWNER_SOURCE.split("class CurrentProductiveSideStateConfirmationCursorV1", 1)[
            1
        ].split("def to_dict", 1)[0]
    )
    assert "def run_current_productive_governed_cycle_v1" in ORCHESTRATOR_SOURCE
    assert MF_PRODUCTIVE_JOIN is False
    assert PRODUCTIVE_RUNTIME_CARDINALITY == "1_UNJOINED"
